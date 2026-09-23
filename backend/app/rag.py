import os
import json
import time
import uuid
from typing import List, Dict, Any, Generator, Optional, Callable
from .config import (
    NVIDIA_API_KEY,
    SUPABASE_URL,
    SUPABASE_KEY,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    LANGFUSE_HOST,
    NVIDIA_LLM_MODEL,
    NVIDIA_EMBEDDING_MODEL,
    MAX_DOCUMENT_CHUNKS,
    EMBEDDING_DIMENSIONS,
)
from .parsers import extract_text
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
from .embeddings import RetrievalEmbedding

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
    llm_options = {"extra_body": {"chat_template_kwargs": {"enable_thinking": False}}} if "nemotron-3-nano" in NVIDIA_LLM_MODEL else {}
    Settings.llm = NVIDIA(model=NVIDIA_LLM_MODEL, api_key=NVIDIA_API_KEY, max_tokens=2048, timeout=120, max_retries=1, is_chat_model=True, additional_kwargs=llm_options)
    Settings.embed_model = RetrievalEmbedding(model=NVIDIA_EMBEDDING_MODEL, api_key=NVIDIA_API_KEY, dimensions=EMBEDDING_DIMENSIONS, timeout=90, max_retries=1)
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
            user_id = metadata.get("user_id")
            if user_id:
                metadata["user_id"] = str(user_id)

            content = node.get_content(metadata_mode=MetadataMode.NONE)
            embedding = node.get_embedding()
            if not embedding:
                embedding = Settings.embed_model.get_text_embedding(content)

            row = {
                "content": content,
                "metadata": metadata,
                "embedding": embedding
            }

            def _insert():
                return supabase_client.table("documents").insert(row).execute()

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

        user_id = delete_kwargs.get("user_id")

        def _delete():
            q = supabase_client.table("documents").delete().eq("metadata->>file_name", ref_doc_id)
            if user_id:
                q = q.eq("metadata->>user_id", str(user_id))
            return q.execute()

        try:
            _execute_with_retry(_delete)
        except Exception as e:
            print(f"Supabase delete failed for file_name={ref_doc_id}: {e}")

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        if not supabase_client:
            raise ValueError("Supabase client is not initialized.")

        user_id = kwargs.get("user_id")
        file_name = kwargs.get("file_name")
        if not user_id:
            raise ValueError("user_id is required for retrieval.")

        def _query():
            return supabase_client.rpc("match_documents_scoped", {
                "query_embedding": query.query_embedding,
                "match_threshold": 0.1,
                "match_count": query.similarity_top_k,
                "p_user_id": str(user_id),
                "p_file_name": file_name if file_name and file_name != "All Documents" else None,
                "p_embedding_model": NVIDIA_EMBEDDING_MODEL,
                "p_dimensions": EMBEDDING_DIMENSIONS,
            }).execute()

        response = _execute_with_retry(_query)

        raw_items = response.data or []
        if user_id:
            user_str = str(user_id)
            matching_items = [
                item for item in raw_items
                if (item.get("metadata") or {}).get("user_id") == user_str
                and (item.get("metadata") or {}).get("embedding_model") == NVIDIA_EMBEDDING_MODEL
                and (item.get("metadata") or {}).get("embedding_dimensions") == EMBEDDING_DIMENSIONS
            ]
            raw_items = matching_items

        if file_name and file_name != "All Documents":
            doc_matched_items = [
                item for item in raw_items
                if item.get("metadata", {}).get("file_name") == file_name
            ]
            raw_items = doc_matched_items

        raw_items = raw_items[:query.similarity_top_k]

        nodes = []
        similarities = []
        ids = []
        for item in raw_items:
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


def ingest_document(file_name: str, file_type: str, text_content: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Parses, chunks, embeds, and stores text content using LlamaIndex.
    Scope metadata by user_id for multi-tenancy.
    """
    if not NVIDIA_API_KEY:
        raise ValueError("NVIDIA_API_KEY is not set. Cannot run embedding pipeline.")

    metadata = {"file_name": file_name, "file_type": file_type, "embedding_model": NVIDIA_EMBEDDING_MODEL, "embedding_dimensions": EMBEDDING_DIMENSIONS}
    if user_id:
        metadata["user_id"] = str(user_id)

    # 1. Wrap content in LlamaIndex Document
    doc = Document(
        text=text_content,
        metadata=metadata
    )

    # 2. Get/Initialize index
    idx = get_index()

    # 3. Split document into nodes
    parser = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    nodes = parser.get_nodes_from_documents([doc])
    if len(nodes) > MAX_DOCUMENT_CHUNKS:
        raise ValueError(f"Document exceeds the {MAX_DOCUMENT_CHUNKS}-chunk limit. Split it into smaller files.")

    # Propagate metadata to nodes
    for node in nodes:
        if user_id:
            node.metadata["user_id"] = str(user_id)

    # 4. Insert nodes
    idx.insert_nodes(nodes)

    return {
        "status": "success",
        "chunks": len(nodes),
        "storage": "supabase"
    }


def list_documents(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List distinct source documents stored in Supabase, filtered by user_id or default documents.
    """
    if not supabase_client:
        raise ValueError("Supabase client is not initialized.")

    if not user_id:
        return []
    response = supabase_client.table("documents").select("metadata").eq("metadata->>user_id", str(user_id)).execute()
    user_str = str(user_id) if user_id else None
    docs = {}

    for row in (response.data or []):
        meta = row.get("metadata") or {}
        doc_user = meta.get("user_id")
        file_name = meta.get("file_name")
        file_type = meta.get("file_type", "unknown")

        # Match user_id OR default/legacy uploaded documents
        if doc_user == user_str:
            if file_name and file_name not in docs:
                docs[file_name] = {"file_name": file_name, "file_type": file_type, "needs_reindex": True}
            if file_name and meta.get("embedding_model") == NVIDIA_EMBEDDING_MODEL and meta.get("embedding_dimensions") == EMBEDDING_DIMENSIONS:
                docs[file_name]["needs_reindex"] = False

    return list(docs.values())


def delete_document(file_name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete all chunks belonging to a specific document.
    """
    if not supabase_client:
        raise ValueError("Supabase client is not initialized.")

    try:
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required for deletion.")
        supabase_client.table("documents").delete().eq("metadata->>file_name", file_name).eq("metadata->>user_id", str(user_id)).execute()
        reinit_index()
        return {"status": "success", "message": f"Deleted '{file_name}'"}
    except Exception as e:
        raise RuntimeError("Document deletion failed.") from e


def clear_storage(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Deletes records from vector store for user_id (or all if not specified).
    """
    if not user_id or not user_id.strip():
        raise ValueError("user_id is required to clear storage.")
    if supabase_client:
        try:
            q = supabase_client.table("documents").delete()
            if user_id:
                q = q.eq("metadata->>user_id", str(user_id))
            else:
                q = q.neq("id", "00000000-0000-0000-0000-000000000000")
            q.execute()
        except Exception as e:
            raise RuntimeError("Failed to clear storage.") from e

    reinit_index()
    return {"status": "success", "message": "Cleared storage archive."}


# -----------------------------------------------------------------------------
# Chat memory & Analytics helpers
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
            .eq("user_id", str(user_id))
            .eq("session_id", str(session_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return list(reversed(response.data or []))
    except Exception as e:
        print(f"Failed to load chat history: {e}")
        return []


def get_user_sessions(user_id: str) -> List[Dict[str, Any]]:
    """
    Load distinct past chat sessions with message snippets for a user.
    """
    if not supabase_client:
        return []

    try:
        response = (
            supabase_client.table("chat_messages")
            .select("session_id, content, created_at, role, user_id")
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .execute()
        )
        user_str = str(user_id) if user_id else None
        sessions = {}

        for row in (response.data or []):
            sid = row.get("session_id")
            row_user = row.get("user_id")

            # Match user_id OR default/legacy chat sessions
            if row_user == user_str:
                if sid and sid not in sessions:
                    content_snippet = row.get("content", "")[:60]
                    sessions[sid] = {
                        "session_id": sid,
                        "last_message": content_snippet + "..." if len(row.get("content", "")) > 60 else content_snippet,
                        "created_at": row.get("created_at")
                    }
        return list(sessions.values())
    except Exception as e:
        print(f"Failed to fetch user sessions: {e}")
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
            "user_id": str(user_id),
            "session_id": str(session_id),
            "role": role,
            "content": content,
            "sources": sources or []
        }).execute()
    except Exception as e:
        print(f"Failed to save chat message: {e}")
        raise RuntimeError("Conversation could not be saved.") from e


def get_admin_analytics(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate admin usage and telemetry statistics for Phase 3 dashboard.
    """
    if not supabase_client:
        return {
            "total_documents": 0,
            "total_chunks": 0,
            "total_messages": 0,
            "active_sessions": 0
        }

    try:
        # 1. Total Chunks & Documents
        doc_res = supabase_client.table("documents").select("id, metadata").eq("metadata->>user_id", str(user_id)).execute()
        
        total_chunks = 0
        distinct_docs = set()
        user_str = str(user_id) if user_id else None

        for row in (doc_res.data or []):
            meta = row.get("metadata") or {}
            doc_user = meta.get("user_id")
            fname = meta.get("file_name")

            # Match user_id OR default/legacy uploaded documents
            if doc_user == user_str:
                if fname:
                    distinct_docs.add(fname)
                    total_chunks += 1

        total_documents = len(distinct_docs)

        # 2. Total Chat Messages & Sessions
        msg_res = supabase_client.table("chat_messages").select("id, session_id, user_id").eq("user_id", str(user_id)).execute()
        
        filtered_msgs = []
        for m in (msg_res.data or []):
            m_user = m.get("user_id")
            if m_user == user_str:
                filtered_msgs.append(m)

        total_messages = len(filtered_msgs)
        distinct_sessions = len(set(m.get("session_id") for m in filtered_msgs if m.get("session_id")))

        return {
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "total_messages": total_messages,
            "active_sessions": distinct_sessions,
            "user_id": user_id or "all_users"
        }
    except Exception as e:
        print(f"Analytics query error: {e}")
        return {
            "total_documents": 0,
            "total_chunks": 0,
            "total_messages": 0,
            "active_sessions": 0,
            "error": "Analytics are temporarily unavailable."
        }


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
    session_id: Optional[str] = None,
    active_document: Optional[str] = None
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
        save_chat_message(user_id, session_id, "user", query_text)

        system_prompt = (
            "You are an expert customer support AI assistant. Answer the user query using ONLY the provided sources. "
            "Do not include internal node IDs or raw JSON metadata in your text response. "
            "If the references are empty or the answer cannot be found in them, say: "
            "I don't have information about that in the uploaded documents. " 
            "Keep your tone helpful, technical, and professional.\n\n"
            "{conversation_history}"
            "Here are the references:\n"
            "{context_str}\n\n"
            "Query: {query_str}\n"
            "Answer:"
        )

        qa_template = PromptTemplate(system_prompt).partial_format(conversation_history=memory_prefix)

        # Create query engine with user_id & file_name kwargs filter for SupabaseHTTPVectorStore
        query_engine = idx.as_query_engine(
            streaming=True,
            similarity_top_k=4,
            text_qa_template=qa_template,
            vector_store_kwargs={"user_id": user_id, "file_name": active_document}
        )

        # Execute query and stream text chunks
        full_response = ""
        for attempt in range(3):
            try:
                response = query_engine.query(query_text)
                for token in response.response_gen:
                    full_response += token
                    yield token
                break
            except Exception as exc:
                # NIM can send capacity errors inside an HTTP-200 SSE stream.
                # Retry only before answer text, so users never see duplicate text.
                capacity_error = "ResourceExhausted" in str(exc) or getattr(exc, "status_code", None) == 429
                if full_response or not capacity_error or attempt == 2:
                    raise
                time.sleep(2 ** (attempt + 1))

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
        # Save assistant message
        save_chat_message(user_id, session_id, "assistant", full_response, sources)
        yield "|||SOURCES|||"
        yield json.dumps(sources)

    except Exception as e:
        # Log diagnostics only on the server, with configured credentials removed.
        detail = str(e)
        for secret in (NVIDIA_API_KEY, SUPABASE_KEY):
            if secret:
                detail = detail.replace(secret, "[redacted]")
        print(f"Streaming generation failed: {type(e).__name__}: {detail}", flush=True)
        error_msg = "\nThe response could not be completed. Please try again."
        yield error_msg
