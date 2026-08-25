# Documents, RAG & Asset Management API

This microservice handles the backend storage, retrieval, and processing of user documents and media assets for the AI Video Creation Platform. It provides a FastAPI interface for file ingestion, PDF/DOCX text chunking, ChromaDB vector retrieval (RAG), and isolated local media storage.

## Features

* **Document Processing:** Extracts and chunks text from uploaded `.pdf` and `.docx` files.
* **Vector RAG:** Generates embeddings (using `all-MiniLM-L6-v2`) and searches relevant document context via ChromaDB.
* **Asset Vault:** Securely isolates uploaded media (images, video, audio) into project-specific local directories.
* **Automated Testing:** Fully tested using `pytest` and FastAPI's `TestClient`.

## Installation

1. Ensure you have Python 3.9+ installed.
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. You can view the interactive Swagger documentation by navigating to `http://localhost:8000/docs` in your browser.

## Running Tests

To verify the integration and health of the endpoints, run the automated test suite:

```bash
pytest
```

## Core API Endpoints

* `POST /api/v1/projects/{project_id}/documents` - Upload and vectorize a PDF/DOCX.
* `POST /api/v1/projects/{project_id}/retrieve` - Query the vector database for RAG context.
* `POST /api/v1/projects/{project_id}/assets` - Upload a media asset (images, video, audio).
* `GET /api/v1/projects/{project_id}/assets` - Retrieve a list of all asset URLs for a project.
