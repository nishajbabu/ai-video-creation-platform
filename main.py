import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List

# Import our core logic modules
from document_processor import extract_text_from_pdf, chunk_text
from vector_store import VectorStoreManager
from asset_manager import AssetManager

# Initialize the API application
app = FastAPI(
    title="Documents & Asset Management API",
    description="Microservice for PDF RAG and Media Asset Storage (Google Vids Clone)",
    version="1.0.0"
)

# Initialize our custom managers
vector_db = VectorStoreManager()
asset_db = AssetManager()

# --- PYDANTIC SCHEMAS ---
class RetrieveQuery(BaseModel):
    query: str
    top_k: int = 3

# --- API ENDPOINTS ---

@app.get("/health")
def health_check():
    """Simple endpoint to verify the service is running."""
    return {"status": "healthy", "service": "rag_module"}

@app.post("/api/v1/projects/{project_id}/documents")
async def upload_document(project_id: str, file: UploadFile = File(...)):
    """
    Accepts a PDF file, extracts text, chunks it, and saves embeddings to ChromaDB.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are currently supported.")

    # Save the uploaded file temporarily to process it
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Extract & Chunk
        raw_text = extract_text_from_pdf(temp_file_path)
        chunks = chunk_text(raw_text, chunk_size=800, overlap=150)

        # 2. Store in Vector DB
        vector_db.insert_chunks(project_id=project_id, document_name=file.filename, chunks=chunks)

        return {
            "status": "success",
            "project_id": project_id,
            "filename": file.filename,
            "chunks_processed": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/api/v1/projects/{project_id}/retrieve")
def retrieve_knowledge(project_id: str, payload: RetrieveQuery):
    """
    Searches the Vector DB for the most relevant document chunks based on a query.
    Used by the Agentic AI Backend.
    """
    try:
        results = vector_db.search_chunks(project_id=project_id, query=payload.query, top_k=payload.top_k)
        return {"project_id": project_id, "query": payload.query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/projects/{project_id}/assets")
async def upload_asset(project_id: str, asset_type: str = Form(...), file: UploadFile = File(...)):
    """
    Uploads a media asset (image, video, audio) to local storage.
    Used by the Frontend.
    """
    valid_types = ["images", "videos", "audio"]
    if asset_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"asset_type must be one of {valid_types}")

    temp_path = f"temp_asset_{file.filename}"
    try:
        # Save upload to a temp file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Move to permanent asset storage
        asset_info = asset_db.save_asset(project_id=project_id, source_file_path=temp_path, asset_type=asset_type)
        return {"status": "success", "data": asset_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/v1/projects/{project_id}/assets")
def get_project_assets(project_id: str):
    """
    Lists all stored assets for a specific project.
    Used by the Video Editor timeline.
    """
    try:
        assets = asset_db.list_project_assets(project_id=project_id)
        return {"project_id": project_id, "assets": assets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))