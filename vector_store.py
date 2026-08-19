import os
import uuid
import chromadb
from chromadb.utils import embedding_functions
from typing import List

class VectorStoreManager:
    """
    Manages the connection, insertion, and retrieval of document embeddings.
    """
    
    def __init__(self, persist_directory: str = "./chroma_data", collection_name: str = "video_assets"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )
        print(f"Vector Store initialized. Collection '{collection_name}' is ready.")

    def insert_chunks(self, project_id: str, document_name: str, chunks: List[str]) -> None:
        if not chunks:
            return

        ids = []
        metadatas = []
        
        for i in range(len(chunks)):
            chunk_id = f"{project_id}_{uuid.uuid4().hex[:8]}"
            ids.append(chunk_id)
            metadatas.append({
                "project_id": project_id,
                "source": document_name,
                "chunk_index": i
            })

        self.collection.add(documents=chunks, metadatas=metadatas, ids=ids)
        print(f"Successfully inserted {len(chunks)} chunks for project '{project_id}'.")

    def search_chunks(self, project_id: str, query: str, top_k: int = 3) -> List[str]:
        """
        Searches the database for the most relevant text chunks matching the query.
        
        Args:
            project_id (str): The specific video project to search inside.
            query (str): The question or topic to search for.
            top_k (int): The number of relevant chunks to return.
            
        Returns:
            List[str]: A list of the most relevant text chunks.
        """
        print(f"\nSearching for: '{query}' in project '{project_id}'...")
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"project_id": project_id} # STRICT GUARDRAIL: Only search this project
        )
        
        if results and "documents" in results and results["documents"]:
            return results["documents"][0]
        return []

# --- MODULE EXECUTION ---
if __name__ == "__main__":
    from document_processor import extract_text_from_pdf, chunk_text
    
    test_pdf = "sample.pdf"
    test_project_id = "proj_test_001"
    
    try:
        db_manager = VectorStoreManager()
        
        # 1. Insert Data (If it's already there, ChromaDB handles it safely)
        raw_text = extract_text_from_pdf(test_pdf)
        text_chunks = chunk_text(raw_text, chunk_size=800, overlap=150)
        db_manager.insert_chunks(project_id=test_project_id, document_name=test_pdf, chunks=text_chunks)
        
        # 2. Test the Search Engine
        search_query = "What does DeepFER stand for?"
        found_chunks = db_manager.search_chunks(project_id=test_project_id, query=search_query, top_k=1)
        
        print("\n--- SEARCH RESULTS ---")
        for idx, chunk in enumerate(found_chunks):
            print(f"Result {idx + 1}:\n{chunk}")
            
    except Exception as e:
        print(f"Error during execution: {e}")