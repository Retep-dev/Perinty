import os
import json
from typing import List, Dict, Any, Generator
from app.config import GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY, CHUNK_SIZE, CHUNK_OVERLAP
from supabase import create_client, Client

# Configure Gemini Generative AI SDK environment variable
if GEMINI_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
    print("GOOGLE_API_KEY environment variable configured.")
else:
    print("WARNING: GEMINI_API_KEY is not set.")

# Supabase Client Setup
supabase_client: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")

# Import LlamaIndex packages
from llama_index.core import Settings, VectorStoreIndex, StorageContext, Document, PromptTemplate
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores.types import BasePydanticVectorStore, VectorStoreQuery, VectorStoreQueryResult
from llama_index.core.schema import TextNode, BaseNode, MetadataMode
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

# Configure LlamaIndex global Settings
if GEMINI_API_KEY:
    # Use GoogleGenAI with Gemini 3.5 Flash
    Settings.llm = GoogleGenAI(model="models/gemini-3.5-flash", api_key=GEMINI_API_KEY)
    # Use GoogleGenAIEmbedding with Gemini embedding model
    Settings.embed_model = GoogleGenAIEmbedding(model_name="models/gemini-embedding-001", api_key=GEMINI_API_KEY)
    print("LlamaIndex global settings configured with Gemini LLM and Embedding models.")

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
                
            try:
                supabase_client.table("documents").insert({
                    "content": content,
                    "metadata": metadata,
                    "embedding": embedding
                }).execute()
                ids.append(node.node_id)
            except Exception as e:
                print(f"Supabase HTTP insert failed for node {node.node_id}: {e}")
                
        return ids

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        pass

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        if not supabase_client:
            raise ValueError("Supabase client is not initialized.")
        
        response = supabase_client.rpc("match_documents", {
            "query_embedding": query.query_embedding,
            "match_threshold": 0.3,
            "match_count": query.similarity_top_k
        }).execute()
        
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
        if supabase_client:
            vector_store = SupabaseHTTPVectorStore()
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex([], storage_context=storage_context)
        else:
            from llama_index.core.vector_stores.simple import SimpleVectorStore
            vector_store = SimpleVectorStore()
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex([], storage_context=storage_context)
    return index

def reinit_index():
    global index, storage_context
    index = None
    storage_context = None
    get_index()

def ingest_document(file_name: str, text_content: str) -> Dict[str, Any]:
    """
    Parses, chunks, embeds, and stores the text content using LlamaIndex.
    Returns status and number of chunks ingested.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set. Cannot run embedding pipeline.")

    # 1. Wrap content in LlamaIndex Document
    doc = Document(text=text_content, metadata={"file_name": file_name})

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
        "storage": "supabase" if supabase_client else "local_memory"
    }

def clear_storage() -> Dict[str, Any]:
    """
    Deletes all records from vector store
    """
    if supabase_client:
        try:
            supabase_client.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        except Exception as e:
            return {"status": "error", "message": f"Cleared local memory, but Supabase failed: {str(e)}"}
            
    reinit_index()
    return {"status": "success", "message": "Cleared storage archive."}

def generate_streaming_response(query_text: str) -> Generator[str, None, None]:
    """
    RAG Query flow with streaming response generator using LlamaIndex.
    Yields chunks of text responses, ending with a JSON block of sources.
    """
    if not GEMINI_API_KEY:
        yield "Error: Gemini API key is not configured. Please verify your environment settings."
        return

    try:
        idx = get_index()
        
        system_prompt = (
            "You are an expert customer support AI assistant. Answer the user query using ONLY the provided sources. "
            "If the answer cannot be found in the sources, say politely that you don't know based on the uploaded data. "
            "Keep your tone helpful, technical, and professional.\n\n"
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
        
        # Execute query
        response = query_engine.query(query_text)
        
        # Stream text chunks
        for token in response.response_gen:
            yield token
            
        # Compile references
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
            
    except Exception as e:
        yield f"Error during streaming generation: {str(e)}"
        return
        
    # Append Sources Metadata at the end (separated by custom delimiter)
    yield "|||SOURCES|||"
    yield json.dumps(sources)
