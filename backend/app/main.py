from fastapi import FastAPI, UploadFile, File, HTTPException, Path, Header, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from app.rag import (
    ingest_document,
    generate_streaming_response,
    clear_storage,
    list_documents,
    delete_document,
    get_chat_history,
    get_user_sessions,
    get_admin_analytics,
)
from app.parsers import extract_text
import os

app = FastAPI(title="Perinty RAG Customer Support API - Phase 3 SaaS")

# Configure CORS so our React frontend can access it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatQuery(BaseModel):
    message: str
    user_id: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    active_document: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "Perinty RAG Phase 3 SaaS API is running!"}


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Accepts multiple file formats, parses them, and indexes them in Supabase under the authenticated user.
    """
    file_name = file.filename
    _, ext = os.path.splitext(file_name)
    ext = ext.lower()

    effective_user_id = user_id or x_user_id or "default_user"

    valid_extensions = [".txt", ".md", ".json", ".pdf", ".docx", ".html", ".htm", ".csv"]
    if ext not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported: {', '.join(valid_extensions)}"
        )

    try:
        content_bytes = await file.read()
        text_content = extract_text(content_bytes, ext)

        result = ingest_document(file_name, ext, text_content, user_id=effective_user_id)
        return {
            "message": f"Successfully ingested file '{file_name}'",
            "chunks_created": result["chunks"],
            "storage": result["storage"],
            "user_id": effective_user_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/documents")
def get_documents(
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    List uploaded source documents, scoped by user_id if provided.
    """
    try:
        effective_user_id = user_id or x_user_id
        docs = list_documents(user_id=effective_user_id)
        return {"documents": docs, "user_id": effective_user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@app.delete("/documents/{file_name}")
def remove_document(
    file_name: str = Path(..., description="Name of the document to delete"),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Delete a specific source document and all its chunks for the target user.
    """
    try:
        effective_user_id = user_id or x_user_id
        result = delete_document(file_name, user_id=effective_user_id)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@app.post("/chat")
def chat(query: ChatQuery):
    """
    Query the indexed knowledge base with conversational memory and stream back answers.
    """
    if not query.message.strip():
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")
    if not query.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required.")

    try:
        generator = generate_streaming_response(
            query.message, query.user_id, query.session_id, query.active_document
        )
        return StreamingResponse(generator, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")


@app.get("/chat/history/{user_id}")
def chat_history(user_id: str, session_id: Optional[str] = None):
    """
    Get chat history for a user, optionally filtered by session_id.
    """
    try:
        messages = get_chat_history(user_id, session_id or "default", limit=100)
        return {"user_id": user_id, "session_id": session_id, "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load chat history: {str(e)}")


@app.get("/chat/sessions/{user_id}")
def list_user_sessions(user_id: str):
    """
    Get all past distinct conversation sessions for a user.
    """
    try:
        sessions = get_user_sessions(user_id)
        return {"user_id": user_id, "sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load user sessions: {str(e)}")


@app.get("/analytics")
def analytics(
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Get admin usage and telemetry metrics for Phase 3 dashboard.
    """
    try:
        effective_user_id = user_id or x_user_id
        stats = get_admin_analytics(user_id=effective_user_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load analytics: {str(e)}")


@app.post("/clear")
def clear_knowledge_base(
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Wipes out stored index chunks for the user (or all if unspecified).
    """
    try:
        effective_user_id = user_id or x_user_id
        res = clear_storage(user_id=effective_user_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear storage: {str(e)}")
