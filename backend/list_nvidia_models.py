"""List available NVIDIA NIM models for the configured API key."""
import os
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

if not NVIDIA_API_KEY:
    print("ERROR: NVIDIA_API_KEY is not set in backend/.env")
    exit(1)

if not NVIDIA_API_KEY.startswith("nvapi-"):
    print("WARNING: Key does not have the expected NVIDIA API key format.")

os.environ["NVIDIA_API_KEY"] = NVIDIA_API_KEY

try:
    from llama_index.llms.nvidia import NVIDIA
    from llama_index.embeddings.nvidia import NVIDIAEmbedding

    print("\n=== Available LLM models ===")
    llm = NVIDIA()
    for model in llm.available_models:
        print(f"  - {model.id}")

    print("\n=== Available Embedding models ===")
    embedder = NVIDIAEmbedding()
    for model in embedder.available_models:
        print(f"  - {model.id}")

except Exception as e:
    print(f"ERROR: {e}")
