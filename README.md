# Perinty - Enterprise Multi-Tenant SaaS Document Q&A (RAG) System

**Perinty** is a production-ready, full-stack Retrieval-Augmented Generation (RAG) SaaS platform designed for document-grounded AI customer support. Built with modern web aesthetics, Supabase `pgvector` multi-tenancy, NVIDIA NIM microservices, LlamaIndex orchestration, and Langfuse observability.

---

## 🌟 Tech Stack & Infrastructure

### **Frontend**
- **Framework**: React 18, Vite 5, TailwindCSS 3
- **Design System**: Vanilla CSS Glassmorphism with HSL tailored dark & light modes
- **Icons & UI**: Lucide React

### **Backend & AI Engine**
- **API Framework**: FastAPI, Pydantic, Uvicorn
- **Orchestration**: LlamaIndex Framework
- **LLM Model**: NVIDIA NIM (`meta/llama-3.1-8b-instruct`)
- **Embedding Model**: NVIDIA NIM (`nvidia/nv-embedqa-e5-v5`, 1024-dimensional)
- **Document Parsers**: PyPDF, python-docx, BeautifulSoup4, CSV/JSON extractors

### **Database & Vector Search**
- **Database**: Supabase PostgreSQL
- **Vector Extension**: `pgvector` with **HNSW Indexing** (`vector_cosine_ops`)
- **Multi-Tenancy**: Row-Level Security (RLS) policies scoped by `user_id`

### **Observability & CI/CD**
- **Monitoring**: Langfuse LLM Observability & Telemetry Tracing
- **CI/CD Pipeline**: GitHub Actions (`.github/workflows/ci-cd.yml`) verifying Python backend syntax and React Vite production builds

---

## 🚀 Key Features

1. **Multi-Format Document Ingestion**:
   - Upload and index `.txt`, `.md`, `.json`, `.pdf`, `.docx`, `.html`, and `.csv` files.
   - Automatic sentence splitting (`chunk_size=512`, `chunk_overlap=64`) and embedding generation.

2. **Supabase `pgvector` HNSW Vector Search**:
   - High-precision similarity search using HNSW indexing for ~100% recall regardless of dataset size.

3. **Multi-Tenancy & Data Isolation**:
   - Supabase Row-Level Security (RLS) policies isolate knowledge bases, vector embeddings, and chat histories per tenant/user ID.

4. **Interactive Document Selection**:
   - Select specific indexed documents from the sidebar to scope chat queries, or select **All Documents (Global Search)**.

5. **Conversational Memory & Past Session History**:
   - Persistent per-user chat memory.
   - **Recent Sessions (🕒)** dropdown selector to switch between past conversations.
   - **New Chat (+)** button to start clean threads without logging out.

6. **Real-Time Token Streaming with Source Citations**:
   - Streaming LLM token delivery with isolated source snippet cards.

7. **SaaS Admin Analytics Dashboard**:
   - Real-time telemetry monitoring for **Total Documents**, **Vector Chunks**, **Chat Turns**, and **Active Sessions**.

8. **Theme Customization (Dark & Light Mode)**:
   - Instant theme toggle with high-contrast typography, crisp glassmorphism cards, and `localStorage` state persistence.

---

## 🛠️ Installation & Setup Guide

### **1. Prerequisites**
- Python 3.10+
- Node.js 18+ & npm
- Supabase PostgreSQL Account with `pgvector` extension enabled
- NVIDIA Developer API Key (`NVIDIA_API_KEY`)

---

### **2. Backend Setup**

```powershell
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### **Environment Variables Configuration**
Create a `.env` file inside the `backend/` directory:

```env
NVIDIA_API_KEY=your_nvidia_api_key_here
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_KEY=your_supabase_anon_or_service_role_key

# Optional Langfuse Monitoring
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

#### **Database Migrations**
Execute the SQL migration scripts in your Supabase SQL Editor in sequence:
1. `backend/supabase_migrations/001_documents.sql` (Tables & HNSW vector index)
2. `backend/supabase_migrations/002_chat_messages.sql` (Chat history table)
3. `backend/supabase_migrations/003_auth_and_rls.sql` (RLS policies & multi-tenant RPCs)

#### **Start Backend Server**
```powershell
uvicorn app.main:app --reload --port 8000
```
- API will be accessible at: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`

---

### **3. Frontend Setup**

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
- Web application will be accessible at: `http://localhost:3000`

---

## 📡 API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /upload` | `POST` | Ingests `.pdf`, `.docx`, `.csv`, etc., into vector store with `X-User-ID` |
| `GET /documents` | `GET` | Lists distinct source documents uploaded for the target user |
| `DELETE /documents/{file_name}` | `DELETE` | Deletes a document and its vector chunks |
| `POST /chat` | `POST` | Streams RAG answers with persistent memory & document scoping |
| `GET /chat/history/{user_id}` | `GET` | Retrieves past message turns for a user and session |
| `GET /chat/sessions/{user_id}` | `GET` | Lists all past distinct conversation sessions for a user |
| `GET /analytics` | `GET` | Fetches SaaS telemetry metrics (Documents, Chunks, Messages, Sessions) |
| `POST /clear` | `POST` | Clears vector store data for the tenant |

---

## 🧪 Verification & Quality Assurance

- **Backend Syntax Validation**:
  ```powershell
  python -m py_compile app/main.py app/rag.py app/parsers.py app/config.py
  ```
- **Frontend Production Build**:
  ```powershell
  npm run build
  ```
- **CI/CD Pipeline**:
  Automated via `.github/workflows/ci-cd.yml` on every push to `main`.

---

## 📄 License
Created by **Afolabi Peter** for Enterprise RAG Showcase.
