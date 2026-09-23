"""Real HTTP RAG checks, scoped to unique disposable test identities."""
import json
import sys
import time
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
import pymupdf
from supabase import create_client
from backend.app.config import SUPABASE_URL, SUPABASE_KEY, NVIDIA_API_KEY


def run(base_url):
    suffix = uuid.uuid4().hex[:12]
    user_a, user_b = f"verify_a_{suffix}", f"verify_b_{suffix}"
    session = f"verify_session_{suffix}"
    filename = f"perinty-verification-{suffix}.pdf"
    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    report = {"url": base_url, "user_id": user_a, "filename": filename, "checks": []}
    def passed(name):
        report["checks"].append(name)
        print("PASS:", name, flush=True)
    def check_response(response):
        assert response.is_success, f"HTTP {response.status_code} at {response.request.url.path}"
        text = response.text
        for secret in (SUPABASE_KEY, NVIDIA_API_KEY):
            assert not secret or secret not in text, "Credential found in response"
        assert "Traceback (most recent call last)" not in text
        return response
    with httpx.Client(base_url=base_url.rstrip("/") + "/", timeout=280) as client:
        try:
            check_response(client.get("api/"))
            passed("API startup")
            for user, token in [(user_a, "cobalt-orchid-731"), (user_b, "amber-pine-492")]:
                pdf = pymupdf.open()
                pdf.new_page().insert_text((72, 72), f"Perinty verification. The support launch code is {token}.")
                data = pdf.tobytes()
                pdf.close()
                result = check_response(client.post("api/upload", data={"user_id": user}, files={"file": (filename, data, "application/pdf")})).json()
                assert result["chunks_created"] > 0
                rows = db.table("documents").select("content,metadata,embedding").eq("metadata->>user_id", user).eq("metadata->>file_name", filename).execute().data
                assert rows and token in rows[0]["content"] and rows[0]["embedding"]
            passed("PDF extraction, chunk creation, embeddings persisted for two identities")
            for selection in (filename, None):
                start = time.monotonic()
                timings, chunks = [], []
                with client.stream("POST", "api/chat", json={"message": "What is the support launch code?", "user_id": user_a, "session_id": session, "active_document": selection}) as response:
                    assert response.status_code == 200
                    assert "no-store" in response.headers.get("cache-control", "")
                    for chunk in response.iter_text():
                        if chunk:
                            timings.append(round(time.monotonic() - start, 3))
                            chunks.append(chunk)
                text = "".join(chunks)
                assert "|||SOURCES|||" in text, "Incomplete stream"
                answer, source_text = text.split("|||SOURCES|||", 1)
                sources = json.loads(source_text)
                assert "cobalt-orchid-731" in answer.lower(), "Answer was not grounded in test document"
                assert "amber-pine-492" not in text, "Cross-identity content returned"
                assert sources and all(item["file_name"] == filename for item in sources)
                assert len(chunks) > 1, "Response was buffered into one chunk"
                assert all(secret not in text for secret in (SUPABASE_KEY, NVIDIA_API_KEY) if secret)
                report.setdefault("streams", []).append({"mode": "document" if selection else "all", "chunks": len(chunks), "first_chunk_seconds": timings[0], "complete_seconds": timings[-1]})
                passed("Streamed answer and sources: " + ("selected document" if selection else "All Documents"))
            history = check_response(client.get(f"api/chat/history/{user_a}", params={"session_id": session})).json()["messages"]
            assert len(history) == 4 and len([m for m in history if m["role"] == "assistant"]) == 2
            assert all(m["sources"] for m in history if m["role"] == "assistant")
            passed("Conversation history and citations persist")
            check_response(client.delete(f"api/documents/{filename}", params={"user_id": user_a}))
            a_docs = check_response(client.get("api/documents", params={"user_id": user_a})).json()["documents"]
            b_docs = check_response(client.get("api/documents", params={"user_id": user_b})).json()["documents"]
            assert not a_docs and any(d["file_name"] == filename for d in b_docs)
            passed("Deletion respects user ID and keeps the other identity's file")
            empty = check_response(client.post("api/chat", json={"message": "What is the support launch code?", "user_id": user_a, "session_id": session, "active_document": None})).text
            assert "amber-pine-492" not in empty
            assert json.loads(empty.split("|||SOURCES|||", 1)[1]) == []
            passed("No-match retrieval returns no other user's sources")
            assert client.post("api/clear").status_code == 400
            passed("Unscoped deletion blocked; no secrets or stack traces in checked responses")
        finally:
            for user in (user_a, user_b):
                db.table("documents").delete().eq("metadata->>user_id", user).eq("metadata->>file_name", filename).execute()
                db.table("chat_messages").delete().eq("user_id", user).eq("session_id", session).execute()
            Path("test-results").mkdir(exist_ok=True)
            Path("test-results/rag-smoke.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    try:
        run(sys.argv[1])
    except Exception as exc:
        print("FAIL:", type(exc).__name__, str(exc) if isinstance(exc, AssertionError) else "See server logs for details", flush=True)
        sys.exit(1)
