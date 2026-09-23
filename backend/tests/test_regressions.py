"""Offline regression tests; never read or mutate the real Supabase project."""
import io
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch, Mock

os.environ.update(VERCEL="1", SUPABASE_URL="https://example.supabase.co", SUPABASE_KEY="test-only", NVIDIA_API_KEY="")
from backend.app import rag, main
from backend.app.parsers import extract_text
from fastapi.testclient import TestClient
from llama_index.core.vector_stores.types import VectorStoreQuery
from index import app


class Query:
    def __init__(self, rows):
        self.rows = rows
        self.filters = []
        self.desc = False
        self.maximum = None
        self.deleting = False

    def select(self, *args, **kwargs): return self
    def delete(self):
        self.deleting = True
        return self
    def eq(self, key, value):
        self.filters.append((key, value))
        return self
    def order(self, key, desc=False):
        self.desc = desc
        return self
    def limit(self, value):
        self.maximum = value
        return self
    def execute(self):
        rows = self.rows[:]
        for key, value in self.filters:
            rows = [row for row in rows if (row.get("metadata", {}).get(key.split("->>")[1]) if "->>" in key else row.get(key)) == value]
        if self.deleting:
            for row in rows: self.rows.remove(row)
        else:
            rows.sort(key=lambda row: row.get("created_at", ""), reverse=self.desc)
            if self.maximum is not None: rows = rows[:self.maximum]
        return SimpleNamespace(data=rows)


class Regressions(unittest.TestCase):
    def test_capacity_retry_does_not_duplicate_persisted_messages(self):
        def busy():
            raise RuntimeError("ResourceExhausted: Worker local total request limit reached")
            yield
        engine = Mock()
        engine.query.side_effect = [SimpleNamespace(response_gen=busy()), SimpleNamespace(response_gen=iter(["answer"]), source_nodes=[])]
        index = SimpleNamespace(as_query_engine=lambda **kwargs: engine)
        with patch.object(rag, "NVIDIA_API_KEY", "test"), patch.object(rag, "get_index", return_value=index), patch.object(rag, "get_chat_history", return_value=[]), patch.object(rag, "save_chat_message") as save, patch.object(rag.time, "sleep"):
            result = "".join(rag.generate_streaming_response("question", "alice", "session"))
        self.assertEqual(result, 'answer|||SOURCES|||[]')
        self.assertEqual(engine.query.call_count, 2)
        self.assertEqual(save.call_count, 2)

    def test_partial_answer_is_not_replayed_on_capacity_failure(self):
        def partial():
            yield "partial answer"
            raise RuntimeError("ResourceExhausted")
        engine = Mock()
        engine.query.return_value = SimpleNamespace(response_gen=partial())
        with patch.object(rag, "NVIDIA_API_KEY", "test"), patch.object(rag, "get_index", return_value=SimpleNamespace(as_query_engine=lambda **kwargs: engine)), patch.object(rag, "get_chat_history", return_value=[]), patch.object(rag, "save_chat_message"):
            result = "".join(rag.generate_streaming_response("question", "alice", "session"))
        self.assertEqual(engine.query.call_count, 1)
        self.assertNotIn("|||SOURCES|||", result)
        self.assertEqual(result.count("partial answer"), 1)

    def test_latest_history_is_returned_in_conversation_order(self):
        rows = [dict(user_id="alice", session_id="one", created_at=i, content=str(i)) for i in range(20)]
        rows.append(dict(user_id="bob", session_id="one", created_at=21, content="private"))
        client = SimpleNamespace(table=lambda _: Query(rows))
        with patch.object(rag, "supabase_client", client):
            history = rag.get_chat_history("alice", "one", 10)
        self.assertEqual([m["content"] for m in history], [str(i) for i in range(10, 20)])

    def test_delete_keeps_other_users_same_named_document(self):
        rows = [dict(metadata=dict(user_id=user, file_name="same.txt")) for user in ("alice", "bob")]
        with patch.object(rag, "supabase_client", SimpleNamespace(table=lambda _: Query(rows))), patch.object(rag, "reinit_index"):
            rag.delete_document("same.txt", "alice")
        self.assertEqual(rows, [dict(metadata=dict(user_id="bob", file_name="same.txt"))])

    def retrieve(self, rows, user="alice", filename=None):
        for row in rows:
            row.setdefault("metadata", {}).update(embedding_model=rag.NVIDIA_EMBEDDING_MODEL, embedding_dimensions=rag.EMBEDDING_DIMENSIONS)
        client = SimpleNamespace(rpc=lambda *args, **kwargs: SimpleNamespace(execute=lambda: SimpleNamespace(data=rows)))
        with patch.object(rag, "supabase_client", client):
            return rag.SupabaseHTTPVectorStore().query(VectorStoreQuery(query_embedding=[0.1], similarity_top_k=4), user_id=user, file_name=filename)

    def test_no_tenant_matches_never_returns_other_users(self):
        result = self.retrieve([dict(content="secret", metadata=dict(user_id="bob", file_name="secret.txt"))])
        self.assertEqual(result.nodes, [])

    def test_no_document_matches_never_falls_back(self):
        result = self.retrieve([dict(content="other", metadata=dict(user_id="alice", file_name="other.txt"))], filename="selected.txt")
        self.assertEqual(result.nodes, [])

    def test_missing_identity_fails_closed(self):
        with self.assertRaises(ValueError): self.retrieve([], user=None)

    def test_matching_tenant_has_sources(self):
        result = self.retrieve([dict(content="answer", metadata=dict(user_id="alice", file_name="selected.txt", node_id="a"), similarity=0.8)], filename="selected.txt")
        self.assertEqual(result.nodes[0].text, "answer")

    def test_no_identity_cannot_clear_everyones_documents(self):
        with TestClient(app) as client:
            self.assertEqual(client.post("/api/clear").status_code, 400)
            self.assertEqual(client.delete("/api/documents/a.txt").status_code, 400)

    def test_api_mount_and_stream_headers(self):
        with patch.object(main, "generate_streaming_response", return_value=iter(["hello", "|||SOURCES|||", "[]"])), TestClient(app) as client:
            response = client.post("/api/chat", json=dict(message="question", user_id="alice"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "hello|||SOURCES|||[]")
        self.assertIn("no-store", response.headers["cache-control"])

    def test_sdk_errors_are_not_exposed(self):
        with patch.object(main, "list_documents", side_effect=RuntimeError("secret-key traceback")), TestClient(app) as client:
            response = client.get("/api/documents?user_id=alice")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secret", response.text)
        self.assertNotIn("traceback", response.text)

    def test_oversize_upload_is_rejected_before_parsing(self):
        with patch.object(main, "MAX_UPLOAD_BYTES", 10), patch.object(main, "extract_text") as parser, TestClient(app) as client:
            response = client.post("/api/upload", data={"user_id": "alice"}, files={"file": ("test.txt", b"x" * 11, "text/plain")})
        self.assertEqual(response.status_code, 413)
        parser.assert_not_called()

    def test_supported_parsers(self):
        import fitz
        from docx import Document
        pdf = fitz.open()
        pdf.new_page().insert_text((72, 72), "Perinty PDF test")
        self.assertIn("Perinty PDF test", extract_text(pdf.tobytes(), ".pdf"))
        pdf.close()
        doc = Document()
        doc.add_paragraph("Perinty DOCX test")
        output = io.BytesIO()
        doc.save(output)
        self.assertIn("DOCX test", extract_text(output.getvalue(), ".docx"))
        for extension, content in [(".txt", b"hello"), (".md", b"# hello"), (".json", b'{"hello": true}'), (".html", b"<p>hello</p>"), (".csv", b"name\nhello")]:
            with self.subTest(extension=extension): self.assertIn("hello", extract_text(content, extension))


if __name__ == "__main__":
    unittest.main()
