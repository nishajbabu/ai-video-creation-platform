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