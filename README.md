# Perinty — Document Q&A Demo

Perinty is a React + FastAPI document-grounded chat application. It extracts text
from PDF, DOCX, TXT, Markdown, HTML, CSV, and JSON, stores chunks and NVIDIA
embeddings in Supabase, and streams answers with source references. Conversation
history, sessions, document selection, analytics, and light/dark themes are included.

**Demo identity only:** the current API trusts a supplied user ID. It does not
verify passwords or Supabase Auth tokens. Anyone who knows a user ID can access
its data. Use non-sensitive demo documents; this is not production authentication.

## Structure

- `frontend/`: React 18, Vite 5, Tailwind CSS, Lucide icons.
- `backend/app/main.py`: FastAPI routes and upload limits.
- `backend/app/rag.py`: LlamaIndex retrieval, ingestion, streaming, history, analytics.
- `backend/app/parsers.py`: in-memory document extraction.
- `backend/app/embeddings.py`: NVIDIA query-mode compatibility fix.
- `backend/supabase_migrations/`: vector tables, chat history, scoped retrieval/RLS.
- `index.py`: Vercel entrypoint exposing the backend under `/api`.

## Local setup

Use Python 3.12 and Node.js 22 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
# Copy backend/.env.example to backend/.env and provide server credentials.
.\.venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
```

In another terminal:

```powershell
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open http://localhost:3000 for the landing page, or http://localhost:3000/app
for the document workspace. Vite proxies `/api` to FastAPI on port 8000.
For a new database, run migrations 001, 002, and 004. Existing installations can
apply 004 after their existing migrations. Older embedding models have been retired;
files indexed with them must be re-uploaded for the new model.

## API

Locally these are backend root paths; on Vercel prefix them with `/api`.

| Route | Purpose |
| --- | --- |
| `POST /upload` | Parse and index a file for a required demo user ID |
| `GET /documents` | List that identity's documents |
| `DELETE /documents/{file_name}` | Delete only that identity's matching file chunks |
| `POST /chat` | Stream an answer and JSON source trailer |
| `GET /chat/history/{user_id}` | Latest messages in chronological order |
| `GET /chat/sessions/{user_id}` | List conversation sessions |
| `GET /analytics` | Usage counters for the supplied user ID |
| `POST /clear` | Clear only the supplied identity's chunks |

## Verification and deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for the one-project Vercel architecture,
complete environment-variable inventory, database prerequisites, runtime/upload
limits, security limitations, and local/live verification commands.

```powershell
.\.venv\Scripts\python -m unittest discover -s backend/tests -v
npm --prefix frontend run build
```

Created by Afolabi Peter.
