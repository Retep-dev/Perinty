"""Read-only service checks. Prints status and schema information, never credentials."""
import base64
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.config import SUPABASE_URL, SUPABASE_KEY, NVIDIA_API_KEY
import httpx

def main():
    print("Supabase URL configured:", bool(SUPABASE_URL), flush=True)
    print("Supabase key configured:", bool(SUPABASE_KEY), flush=True)
    print("NVIDIA key configured:", bool(NVIDIA_API_KEY), flush=True)
    if SUPABASE_KEY and SUPABASE_KEY.count(".") == 2:
        payload = SUPABASE_KEY.split(".")[1]
        print("Supabase key role:", json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))).get("role"), flush=True)
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    with httpx.Client(timeout=30) as client:
        response = client.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
        print("Supabase schema HTTP:", response.status_code, flush=True)
        if response.is_success:
            schema = response.json()
            for name in ("documents", "chat_messages"):
                fields = schema.get("definitions", {}).get(name, {}).get("properties", {})
                print(name, "columns:", list(fields), flush=True)
            print("Vector RPC present:", "/rpc/match_documents" in schema.get("paths", {}), flush=True)
        response = client.get("https://integrate.api.nvidia.com/v1/models", headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"})
        print("NVIDIA models HTTP:", response.status_code, flush=True)
        if response.is_success:
            print("Available embedding model IDs:", [item["id"] for item in response.json().get("data", []) if "embed" in item["id"] or "bge" in item["id"]], flush=True)
            print("Available LLM candidates:", [item["id"] for item in response.json().get("data", []) if any(part in item["id"] for part in ("llama", "nano", "qwen", "mistral")) and "embed" not in item["id"]], flush=True)

if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print("Preflight failed:", type(exc).__name__)
        sys.exit(1)
