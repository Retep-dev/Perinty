"""Diagnose embedding initialization without exposing credentials."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.config import NVIDIA_API_KEY, SUPABASE_KEY

try:
    from backend.app.rag import Settings, get_index
    print("Embedding dimensions:", len(Settings.embed_model.get_text_embedding("Perinty verification")), flush=True)
    get_index()
    print("Vector index initialized", flush=True)
    print("Query embedding dimensions:", len(Settings.embed_model.get_query_embedding("Perinty verification")), flush=True)
    result = Settings.llm.complete("Reply with the word OK.")
    print("LLM completion succeeded:", bool(result.text), flush=True)
except Exception as exc:
    message = str(exc)
    for secret in (NVIDIA_API_KEY, SUPABASE_KEY):
        if secret: message = message.replace(secret, "[redacted]")
    print(type(exc).__name__, message, flush=True)
    sys.exit(1)
