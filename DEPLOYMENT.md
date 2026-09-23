# Perinty on Vercel

## Architecture

One Vercel project, rooted at this repository, using the native **FastAPI** preset
and Python 3.12. `index.py` mounts the existing FastAPI application at `/api`.
The build command installs the Vite frontend from its lockfile and writes its
production output to `dist/`. FastAPI's `app.frontend()` registers it for Vercel's
CDN and serves the index at `/`. React renders the landing page at `/` and the
existing document workspace at `/app` (including direct navigation and refresh).
Landing-page CTAs use normal links; the workspace keeps its existing browser storage.
The product preview embeds the real `/app` interface. There is no external backend host or frontend API URL variable.
All browser API calls use the same-origin `/api` prefix. Local Vite development
continues to proxy `/api` to `http://localhost:8000` without changing backend routes.

`vercel.json` is needed for the combined frontend build, 300-second
function duration, and exclusions that keep virtual environments and secrets out
of the Python bundle. Do not set the Vercel root directory to `frontend/`.
The Python dependencies are pinned directly in root `requirements.txt` for Vercel's
parser; `backend/requirements.txt` includes that file for local use. `.python-version` selects 3.12.

## Dashboard environment variables

Enter these in **Project Settings → Environment Variables**, for Production and
any Preview deployment that should use these services. Preview deployments should
normally use a separate test Supabase project. These are all **server-only**;
never prefix a secret with `VITE_` and never put secret values in `vercel.json`.

| Variable | Required / default |
| --- | --- |
| `SUPABASE_URL` | Required: the intended Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Required: that project's server-side service-role key |
| `SUPABASE_KEY` | Legacy fallback only when `SUPABASE_SERVICE_ROLE_KEY` is absent; must have server permissions, not an anonymous key |
| `NVIDIA_API_KEY` | Required: NVIDIA hosted inference credential |
| `NVIDIA_LLM_MODEL` | Defaults to `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` |
| `NVIDIA_EMBEDDING_MODEL` | Defaults to `nvidia/llama-nemotron-embed-vl-1b-v2` |
| `EMBEDDING_DIMENSIONS` | `1024`; current database schema rejects other values |
| `CHUNK_SIZE` | `512` tokens |
| `CHUNK_OVERLAP` | `64` tokens |
| `MAX_UPLOAD_BYTES` | `4000000`; application clamps this at 4 MB |
| `MAX_DOCUMENT_CHARS` | `200000` extracted characters |
| `MAX_DOCUMENT_CHUNKS` | `100` per upload |
| `CORS_ORIGINS` | Empty for same-origin; optional comma-separated explicit origins for a separate frontend |
| `LANGFUSE_PUBLIC_KEY` | Optional; enable only together with the secret key |
| `LANGFUSE_SECRET_KEY` | Optional, secret; document prompts/responses may be sent to Langfuse when enabled |
| `LANGFUSE_HOST` | Optional; defaults to `https://cloud.langfuse.com` |

No frontend environment variables are required. `VERCEL` is supplied by Vercel;
when present, local `.env` loading is disabled. The unused legacy `GEMINI_API_KEY`
found in the local environment is not used or transferred. Model adapters may also
honor provider-specific environment overrides; leave `NVIDIA_BASE_URL` unset for
the default NVIDIA hosted service.

## Database prerequisite and embedding migration

For a new database, run migrations 001 and 002, then 004. Existing installations
with migration 003 can also apply 004. Migration 004 tightens the known RLS
policies and adds `match_documents_scoped`, accessible only to `service_role`.
It filters user ID, optional filename, embedding model, and dimension before
returning the nearest results. Application filtering remains a second check.
No existing document or conversation row is deleted or rewritten by the migration.

The former hosted `nvidia/nv-embedqa-e5-v5` endpoint returns HTTP 410 (retired).
The former `meta/llama-3.1-8b-instruct` chat endpoint is also retired. The configured
replacement is NVIDIA Nano Omni, with reasoning disabled for direct streamed answers.
The replacement uses 1024-dimensional output but a different vector space.
Old chunks must be re-indexed by re-uploading their source files. They remain in
the database and are excluded from retrieval until new compatible chunks exist.
The document list marks files that require re-upload. Changing the embedding
model later also requires re-indexing, even if dimensions remain the same.

## Local and deployment checks

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m compileall -q backend/app index.py scripts
.\.venv\Scripts\python -m unittest discover -s backend/tests -v
.\.venv\Scripts\python -m unittest backend.test_rag -v
npm --prefix frontend ci
npm --prefix frontend test
npm --prefix frontend run build -- --outDir ../dist
```

`backend/test_rag.py` is now explicitly opt-in. The original script cleared the
whole database on import; that unsafe behavior has been removed. To run the real
integration test, start `python -m uvicorn index:app --port 8017`, then run:

```powershell
.\.venv\Scripts\python scripts/smoke_test.py http://127.0.0.1:8017
# After deploying, substitute the actual live URL:
.\.venv\Scripts\python scripts/smoke_test.py https://YOUR-PERINTY-URL.vercel.app
```

The smoke test creates unique disposable PDF fixtures for two identities, verifies
database text/vectors, multiple streamed chunks, correct answers/sources, stored
history, All Documents, scoped deletion, and empty retrieval. It deletes only its
own exact test records and writes a secret-free report to ignored `test-results/`.
It consumes a small amount of NVIDIA inference. Browser verification is also needed
for upload controls, visible sources, and enabling the All Documents input.

Deploy with the official Vercel CLI (`vercel --prod`) or the connected GitHub repo.
Never upload `.env` files. The optional `scripts/configure_vercel_env.py` transfers
only the audited runtime values via stdin to the linked project, without printing
them. Review its target scope before reusing it for a different Vercel account.

## Streaming, upload, and runtime limitations

- Python ASGI `StreamingResponse` streams plain text, followed by the existing
  `|||SOURCES|||` JSON trailer. No proxy function buffers it. Responses use
  `Cache-Control: no-store, no-transform`. Assistant history is saved before the
  final sources trailer, so successful completion includes persisted history.
  NVIDIA capacity errors before the first answer token receive two bounded retries;
  errors after partial output terminate cleanly without replaying the answer.
- Vercel's function request payload limit is 4.5 MB, including multipart overhead.
  The UI and backend allow at most 4,000,000 bytes. Larger documents need direct
  object-storage uploads and a background ingestion workflow, which this version
  does not implement.
- Hobby functions have a 300-second maximum. Slow parsing, embedding batches,
  provider retries, and token generation all count toward that request's duration.
  Streaming does not remove the duration limit. Upload text/chunk limits reduce
  risk but cannot guarantee completion under provider outages or throttling.
- PDF uses PyMuPDF's Linux wheel; DOCX uses python-docx/lxml. Files are parsed from
  bytes; no durable local disk is assumed. Temporary upload spooling is ephemeral.
  Scanned image-only PDFs need OCR before upload; DOCX table extraction is limited.
- Standard Python function bundles are capped at 500 MB. Development folders are
  excluded. No local model weights are bundled; NVIDIA performs inference remotely.
  This deployment's roughly 302 MB dependency bundle triggered Vercel's dependency
  optimization; runtime logs show dependencies installed into ephemeral `/tmp` on
  cold starts. This adds startup latency and depends on package availability.
- Ingestion is synchronous and individual chunk writes are not transactional;
  interrupted uploads can leave partial chunks. Repeated uploads can add duplicates.
- List/analytics helpers are bounded by Supabase's REST row-return limit and do not
  yet offer full pagination; metrics on large datasets may undercount.

## Authentication and security scope

**This is a demo deployment, not a production authentication system.** The browser
stores a demo identity and the API trusts a supplied user ID. Anyone knowing or
guessing an ID can impersonate it. RLS protects direct anonymous database access,
but the backend's service-role key bypasses RLS and depends on application filters.
Use non-sensitive demo data only. Real Supabase Auth/JWT verification, verified
identity propagation, authorization, rate limiting, and abuse controls remain
required before hosting private user data or representing this as production-ready.

## Verified deployment, September 22, 2026

Live URL: https://perinty.vercel.app. One native FastAPI/Python 3.12 Vercel project,
with the React build registered through `app.frontend()` and same-origin `/api`.
Migration 004 was applied to the configured Supabase project successfully.

Production API checks passed using two isolated disposable PDF fixtures: extraction,
stored text/vectors, tenant-scoped retrieval, selected-document and All Documents
streaming, citations, persisted conversation history, scoped deletion, empty-result
isolation, missing-identity rejection, and absence of configured credentials or stack
traces in checked responses. The selected-document answer arrived in 17 chunks
(first at 1.953 seconds, complete at 2.594 seconds); All Documents arrived in 14
chunks (first at 1.578 seconds, complete at 1.796 seconds). These are observed test
timings, not service guarantees. Test records were removed.

Browser checks confirmed the app loads, PDF upload indexes successfully, All
Documents keeps chat enabled, answers display the expected source, and history
with citations survives a reload. The browser PDF's extracted text and vector
were independently verified in Supabase.

Final check on September 23: the live frontend returned HTTP 200. Both remaining
browser fixture documents were deleted through the live API (HTTP 200), and the
fixture identity's document list was empty. Browser automation became unavailable
during the deletion confirmation, so final deletion verification used the API.

The deployed code was uploaded with the Vercel CLI. Repository changes remain
local and uncommitted; commit and push these files before relying on future GitHub
deployments, which otherwise still use the old repository version.

### Files changed

- Deployment: `index.py`, `vercel.json`, `.python-version`, `.vercelignore`,
  `.gitignore`, root and backend `requirements.txt`, `.github/workflows/ci-cd.yml`.
- Backend: `backend/app/config.py`, `main.py`, `rag.py`, `parsers.py`, `embeddings.py`,
  `backend/.env.example`, `backend/list_nvidia_models.py`,
  `backend/supabase_migrations/004_scoped_retrieval.sql`.
- Frontend: `frontend/package.json`, `frontend/src/App.jsx`,
  `components/AuthModal.jsx`, `components/ChatWindow.jsx`,
  `components/DocumentUploader.jsx`, `stream.js`, `stream.test.js`.
- Verification/docs: `backend/tests/test_regressions.py`, `backend/test_rag.py`,
  `scripts/preflight.py`, `scripts/check_embedding.py`, `scripts/smoke_test.py`,
  `scripts/check_public_assets.py`, `scripts/configure_vercel_env.py`, `README.md`,
  `DEPLOYMENT.md`.

Local validation: frontend production build, 2 frontend stream-parser tests,
13 backend regression tests, Python syntax/import/startup checks, and `pip check`.
The opt-in live test module is skipped unless explicitly enabled. The frontend
production dependency audit found zero vulnerabilities; the existing Vite build
toolchain still reports development dependency advisories.

## Official platform references

- https://vercel.com/docs/frameworks/backend/fastapi
- https://vercel.com/docs/functions/runtimes/python
- https://vercel.com/docs/functions/limitations
- https://docs.api.nvidia.com/nim/reference/nvidia-llama-nemotron-embed-vl-1b-v2
