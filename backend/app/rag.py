import os
import json
import time
import uuid
from typing import List, Dict, Any, Generator, Optional, Callable
from app.config import (
    NVIDIA_API_KEY,
    SUPABASE_URL,
    SUPABASE_KEY,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    LANGFUSE_HOST,
)
from app.parsers import extract_text
from supabase import create_client, Client

# Configure NVIDIA API key environment variable
if NVIDIA_API_KEY:
    os.environ["NVIDIA_API_KEY"] = NVIDIA_API_KEY
    print("NVIDIA_API_KEY environment variable configured.")
else:
    print("WARNING: NVIDIA_API_KEY is not set.")

# Supabase Client Setup
supabase_client: Client = None
if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "Phase 2 requires SUPABASE_URL and SUPABASE_KEY to be set in backend/.env"
    )

try:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client initialized successfully.")
except Exception as e:
    raise EnvironmentError(f"Failed to initialize Supabase client: {e}") from e

# Import LlamaIndex packages
from llama_index.core import Settings, VectorStoreIndex, StorageContext, Document, PromptTemplate
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores.types import BasePydanticVectorStore, VectorStoreQuery, VectorStoreQueryResult
from llama_index.core.schema import TextNode, BaseNode, MetadataMode
from llama_index.llms.nvidia import NVIDIA
from llama_index.embeddings.nvidia import NVIDIAEmbedding

# Optional Langfuse Observability Integration
langfuse_handler = None
if LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
    try:
        from llama_index.core.callbacks import CallbackManager
        from llama_index.callbacks.langfuse import LlamaIndexCallbackHandler
        langfuse_handler = LlamaIndexCallbackHandler(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST
        )
        Settings.callback_manager = CallbackManager([langfuse_handler])
        print("Langfuse LLM Observability & Monitoring registered successfully.")
    except Exception as e:
        print(f"Notice: Langfuse callback handler not initialized: {e}")

# Configure LlamaIndex global Settings
if NVIDIA_API_KEY:
    Settings.llm = NVIDIA(model="meta/llama-3.1-8b-instruct", api_key=NVIDIA_API_KEY)
    Settings.embed_model = NVIDIAEmbedding(model="nvidia/nv-embedqa-e5-v5", api_key=NVIDIA_API_KEY)
    print("LlamaIndex global settings configured with NVIDIA LLM and Embedding models.")


def _execute_with_retry(operation: Callable, max_retries: int = 3, base_delay: float = 1.0):
    """
    Execute a Supabase operation with retries on transient network/SSL errors.
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            last_exception = e
            error_str = str(e).lower()
            # Retry on transient connection/SSL errors
            is_transient = any(
                marker in error_str
                for marker in [
                    "forcibly closed",
                    "bad record mac",
                    "decryption failed",
                    "connecterror",
                    "readerror",
                    "timeout",
                ]
            )
            if not is_transient or attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"Supabase operation failed (attempt {attempt + 1}/{max_retries}), retrying in {delay}s: {e}")
            time.sleep(delay)
    raise last_exception


# Custom Pydantic-based Supabase Vector Store
class SupabaseHTTPVectorStore(BasePydanticVectorStore):
    stores_text: bool = True

    @property
    def client(self) -> Any:
        return supabase_client

    def add(self, nodes: List[BaseNode], **kwargs: Any) -> List[str]:
        if not supabase_client:
            raise ValueError("Supabase client is not initialized.")

        ids = []
        for node in nodes:
            metadata = node.metadata or {}
            metadata["node_id"] = node.node_id

            content = node.get_content(metadata_mode=MetadataMode.NONE)
            embedding = node.get_embedding()
            if not embedding:
                embedding = Settings.embed_model.get_text_embedding(content)

            def _insert():
                return supabase_client.table("documents").insert({
                    "content": content,
                    "metadata": metadata,
                    "embedding": embedding
                }).execute()

            try:
                _execute_with_retry(_insert)
                ids.append(node.node_id)
            except Exception as e:
                raise RuntimeError(
                    f"Supabase vector insert failed for node {node.node_id}: {e}"
                ) from e

        return ids

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        """
        Delete nodes by file_name stored in metadata.
        ref_doc_id is treated as the file_name to remove.
        """
        if not supabase_client:
            raise ValueError("Supabase client is not initialized.")

        def _delete():
            return supabase_client.table("documents").delete().eq(
                "metadata->>file_name", ref_doc_id
            ).execute()

        try:
            _execute_with_retry(_delete)
        except Exception as e:
            print(f"Supabase delete failed for file_name={ref_doc_id}: {e}")

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        if not supabase_client:
            raise ValueError("Supabase client is not initialized.")

        def _query():
            return supabase_client.rpc("match_documents", {
                "query_embedding": query.query_embedding,
                "match_threshold": 0.1,
                "match_count": query.similarity_top_k
            }).execute()

        response = _execute_with_retry(_query)

        nodes = []
        similarities = []
        ids = []
        for item in response.data:
            content = item.get("content", "")
            metadata = item.get("metadata", {})
            similarity = item.get("similarity", 0.0)
            node_id = metadata.get("node_id", "")

            node = TextNode(
                text=content,
                id_=node_id,
                metadata=metadata
            )
            nodes.append(node)
            similarities.append(similarity)
            ids.append(node_id)

        return VectorStoreQueryResult(
            nodes=nodes,
            similarities=similarities,
            ids=ids
        )


# Global variables for index and storage
index = None
storage_context = None


def get_index() -> VectorStoreIndex:
    global index, storage_context
    if index is None:
        vector_store = SupabaseHTTPVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex([], storage_context=storage_context)
    return index


def reinit_index():
    global index, storage_context
    index = None
    storage_context = None
    get_index()


def ingest_document(file_name: str, file_type: str, text_content: str) -> Dict[str, Any]:
    """
    Parses, chunks, embeds, and stores the text content using LlamaIndex.
    Returns status and number of chunks ingested.
    """
    if not NVIDIA_API_KEY:
        raise ValueError("NVIDIA_API_KEY is not set. Cannot run embedding pipeline.")

    # 1. Wrap content in LlamaIndex Document
    doc = Document(
        text=text_content,
        metadata={"file_name": file_name, "file_type": file_type}
    )

    # 2. Get/Initialize the index
    idx = get_index()

    # 3. Split document into nodes
    parser = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    nodes = parser.get_nodes_from_documents([doc])

    # 4. Insert nodes (this automatically embeds them via Settings.embed_model)
    idx.insert_nodes(nodes)

    return {
        "status": "success",
        "chunks": len(nodes),
        "storage": "supabase"
    }


def list_documents() -> List[Dict[str, Any]]:
    """
    List distinct source documents stored in Supabase by file_name.
    """
    if not supabase_client:
        raise ValueError("Supabase client is not initialized.")

    response = supabase_client.table("documents").select("metadata").execute()
    docs = {}
    for row in response.data:
        meta = row.get("metadata") or {}
        file_name = meta.get("file_name")
        file_type = meta.get("file_type", "unknown")
        if file_name and file_name not in docs:
            docs[file_name] = {"file_name": file_name, "file_type": file_type}

    return list(docs.values())


def delete_document(file_name: str) -> Dict[str, Any]:
    """
    Delete all chunks belonging to a specific source document.
    """
    if not supabase_client:
        raise ValueError("Supabase client is not initialized.")

    try:
        supabase_client.table("documents").delete().eq(
            "metadata->>file_name", file_name
        ).execute()
        # Also clear in-memory index so it reloads fresh on next query
        reinit_index()
        return {"status": "success", "message": f"Deleted '{file_name}'"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def clear_storage() -> Dict[str, Any]:
    """
    Deletes all records from vector store.
    """
    if supabase_client:
        try:
            supabase_client.table("documents").delete().neq(
                "id", "00000000-0000-0000-0000-000000000000"
            ).execute()
        except Exception as e:
            return {"status": "error", "message": f"Supabase failed: {str(e)}"}

    reinit_index()
    return {"status": "success", "message": "Cleared storage archive."}


# -----------------------------------------------------------------------------
# Chat memory helpers
# -----------------------------------------------------------------------------

def get_chat_history(user_id: str, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Load recent chat messages for a user/session from Supabase.
    """
    if not supabase_client:
        return []

    try:
        response = (
            supabase_client.table("chat_messages")
            .select("*")
            .eq("user_id", user_id)
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Failed to load chat history: {e}")
        return []


def save_chat_message(
    user_id: str,
    session_id: str,
    role: str,
    content: str,
    sources: Optional[List[Dict[str, Any]]] = None
) -> None:
    """
    Persist a chat message to Supabase.
    """
    if not supabase_client:
        return

    try:
        supabase_client.table("chat_messages").insert({
            "user_id": user_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "sources": sources or []
        }).execute()
    except Exception as e:
        print(f"Failed to save chat message: {e}")


def _build_memory_prefix(history: List[Dict[str, Any]]) -> str:
    """
    Build a short conversation history prefix for the LLM prompt.
    """
    if not history:
        return ""

    lines = ["Previous conversation:"]
    for msg in history:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    lines.append("")
    return "\n".join(lines)


def generate_streaming_response(
    query_text: str,
    user_id: str,
    session_id: Optional[str] = None
) -> Generator[str, None, None]:
    """
    RAG Query flow with streaming response generator using LlamaIndex.
    Yields chunks of text responses, ending with a JSON block of sources.
    Saves user and assistant messages to Supabase for persistent memory.
    """
    if not NVIDIA_API_KEY:
        yield "Error: NVIDIA API key is not configured. Please verify your environment settings."
        return

    if not session_id:
        session_id = str(uuid.uuid4())

    # Save user message
    try:
        idx = get_index()

        # Tag trace params for Langfuse Observability if enabled
        if langfuse_handler:
            try:
                langfuse_handler.set_trace_params(
                    user_id=user_id,
                    session_id=session_id,
                    tags=["perinty-rag-v2"]
                )
            except Exception:
                pass

        # Load prior conversation context
        history = get_chat_history(user_id, session_id, limit=10)
        memory_prefix = _build_memory_prefix(history)

        system_prompt = (
            "You are an expert customer support AI assistant. Answer the user query using ONLY the provided sources. "
            "Do not include internal node IDs or raw JSON metadata in your text response. "
            "If the references are empty or the answer cannot be found in them, say: "
            "I don't have information about that in the uploaded documents. " 
            "Keep your tone helpful, technical, and professional.\n\n"
            f"{memory_prefix}"
            "Here are the references:\n"
            "{context_str}\n\n"
            "Query: {query_str}\n"
            "Answer:"
        )

        qa_template = PromptTemplate(system_prompt)

        # Create query engine
        query_engine = idx.as_query_engine(
            streaming=True,
            similarity_top_k=4,
            text_qa_template=qa_template
        )

        # Execute query and stream text chunks
        response = query_engine.query(query_text)
        full_response = ""
        for token in response.response_gen:
            full_response += token
            yield token

        # Compile references from retrieved source nodes
        sources = []
        for i, node_with_score in enumerate(response.source_nodes):
            node = node_with_score.node
            meta = node.metadata or {}
            file_name = meta.get("file_name", "Unknown Source")
            content = node.get_content(metadata_mode=MetadataMode.NONE)
            sources.append({
                "index": i + 1,
                "file_name": file_name,
                "snippet": content[:150] + "..." if len(content) > 150 else content
            })

        # Append source metadata at the end (separated by custom delimiter)
        yield "|||SOURCES|||"
        yield json.dumps(sources)

        # Save assistant message
        save_chat_message(user_id, session_id, "assistant", full_response, sources)

    except Exception as e:
        error_msg = f"Error during streaming generation: {str(e)}"
        yield error_msg
