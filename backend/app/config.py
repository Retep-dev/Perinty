import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
if not os.getenv("VERCEL"):
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# NVIDIA NIM API Configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_LLM_MODEL = os.getenv("NVIDIA_LLM_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning")
NVIDIA_EMBEDDING_MODEL = os.getenv("NVIDIA_EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
if EMBEDDING_DIMENSIONS != 1024:
    raise ValueError("The current database schema requires EMBEDDING_DIMENSIONS=1024.")

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

# Langfuse Observability Configuration
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# RAG Settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))
MAX_UPLOAD_BYTES = min(int(os.getenv("MAX_UPLOAD_BYTES", "4000000")), 4000000)
MAX_DOCUMENT_CHARS = int(os.getenv("MAX_DOCUMENT_CHARS", "200000"))
MAX_DOCUMENT_CHUNKS = int(os.getenv("MAX_DOCUMENT_CHUNKS", "100"))
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
