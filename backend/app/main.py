from fastapi import FastAPI, UploadFile, File, HTTPException, Path
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
)
from app.parsers import extract_text
import os

app = FastAPI(title="Perinty RAG Customer Support API")

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


@app.get("/")
def read_root():
    return {"message": "Perinty RAG API is running!"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts multiple file formats, parses them, and indexes them in Supabase.
    """
    file_name = file.filename
    _, ext = os.path.splitext(file_name)
    ext = ext.lower()

    valid_extensions = [".txt", ".md", ".json", ".pdf", ".docx", ".html", ".htm", ".csv"]
    if ext not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported: {', '.join(valid_extensions)}"
        )

    try:
        content_bytes = await file.read()
        text_content = extract_text(content_bytes, ext)

        result = ingest_document(file_name, ext, text_content)
        return {
            "message": f"Successfully ingested file '{file_name}'",
            "chunks_created": result["chunks"],
            "storage": result["storage"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/documents")
def get_documents():
    """
    List all uploaded source documents.
    """
    try:
        docs = list_documents()
        return {"documents": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@app.delete("/documents/{file_name}")
def remove_document(file_name: str = Path(..., description="Name of the document to delete")):
    """
    Delete a specific source document and all its chunks.
    """
    try:
        result = delete_document(file_name)
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
        generator = generate_streaming_response(query.message, query.user_id, query.session_id)
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


@app.post("/clear")
def clear_knowledge_base():
    """
    Wipes out the existing stored index chunks.
    """
    try:
        res = clear_storage()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear storage: {str(e)}")
