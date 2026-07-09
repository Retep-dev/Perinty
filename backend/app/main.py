from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.rag import ingest_document, generate_streaming_response, clear_storage
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


@app.get("/")
def read_root():
    return {"message": "Perinty RAG API is running!"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts text or markdown files and indexes them in the vector database.
    """
    file_name = file.filename
    _, ext = os.path.splitext(file_name)
    
    if ext.lower() not in [".txt", ".md", ".json"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a .txt, .md, or .json file."
        )

    try:
        content_bytes = await file.read()
        text_content = content_bytes.decode("utf-8", errors="ignore")
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")
            
        result = ingest_document(file_name, text_content)
        return {
            "message": f"Successfully ingested file '{file_name}'",
            "chunks_created": result["chunks"],
            "storage": result["storage"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/chat")
def chat(query: ChatQuery):
    """
    Query the indexed knowledge base and stream back answers with citation details.
    """
    if not query.message.strip():
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")
        
    try:
        generator = generate_streaming_response(query.message)
        return StreamingResponse(generator, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")


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
