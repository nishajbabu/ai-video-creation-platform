import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List

# Import updated document processor function
from document_processor import extract_text_from_document, chunk_text
from vector_store import VectorStoreManager
from asset_manager import AssetManager

app = FastAPI(
    title="Documents & Asset Management API",
    description="Microservice handling PDF/DOCX ingestion, vector search (RAG), and localized media storage.",
    version="1.1.0"
)

vector_db = VectorStoreManager()
asset_db = AssetManager()

class RetrieveQuery(BaseModel):
    """
    Data validation schema for incoming vector search requests.
    """
    query: str
    top_k: int = 3

@app.get("/health")
def health_check():
    """
    Verifies service availability for load balancers or health monitoring systems.
    """
    return {"status": "healthy", "service": "rag_module"}

@app.post("/api/v1/projects/{project_id}/documents")
async def upload_document(project_id: str, file: UploadFile = File(...)):
    """
    Ingests a PDF or DOCX stream, processes the binary into vectorized text chunks, 
    and persists them within the designated project namespace.
    """
    valid_extensions = ('.pdf', '.docx')
    if not file.filename.lower().endswith(valid_extensions):
        raise HTTPException(status_code=400, detail=f"MIME type mismatch: Expected one of {valid_extensions}.")

    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer_stream:
            shutil.copyfileobj(file.file, buffer_stream)

        # Call the newly updated extraction logic
        extracted_raw_text = extract_text_from_document(temp_path)
        context_chunks = chunk_text(extracted_raw_text, chunk_size=800, overlap=150)
        vector_db.insert_chunks(project_id=project_id, document_name=file.filename, chunks=context_chunks)

        return {
            "status": "success",
            "project_id": project_id,
            "filename": file.filename,
            "chunks_processed": len(context_chunks)
        }
    except Exception as processing_error:
        raise HTTPException(status_code=500, detail=str(processing_error))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/v1/projects/{project_id}/retrieve")
def retrieve_knowledge(project_id: str, payload: RetrieveQuery):
    """
    Executes a semantic query against the vector database to retrieve contextual knowledge.
    """
    try:
        search_results = vector_db.search_chunks(
            project_id=project_id, 
            query=payload.query, 
            top_k=payload.top_k
        )
        return {"project_id": project_id, "query": payload.query, "results": search_results}
    except Exception as db_error:
        raise HTTPException(status_code=500, detail=str(db_error))

@app.post("/api/v1/projects/{project_id}/assets")
async def upload_asset(project_id: str, asset_type: str = Form(...), file: UploadFile = File(...)):
    """
    Ingests multimedia payloads via multipart form data and persists them in isolated local storage.
    """
    accepted_types = ["images", "videos", "audio"]
    if asset_type not in accepted_types:
        raise HTTPException(status_code=400, detail=f"Invalid payload category. Must be one of {accepted_types}")

    temp_path = f"temp_asset_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer_stream:
            shutil.copyfileobj(file.file, buffer_stream)
            
        asset_metadata = asset_db.save_asset(
            project_id=project_id, 
            source_file_path=temp_path, 
            asset_type=asset_type
        )
        return {"status": "success", "data": asset_metadata}
    except Exception as storage_error:
        raise HTTPException(status_code=500, detail=str(storage_error))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/v1/projects/{project_id}/assets")
def get_project_assets(project_id: str):
    """
    Retrieves the complete catalog of stored media assets mapped to a specific project.
    """
    try:
        catalog = asset_db.list_project_assets(project_id=project_id)
        return {"project_id": project_id, "assets": catalog}
    except Exception as retrieval_error:
        raise HTTPException(status_code=500, detail=str(retrieval_error))