import os
import uuid
import chromadb
from chromadb.utils import embedding_functions
from typing import List

class VectorStoreManager:
    """
    Handles the lifecycle, persistence, and semantic querying of document embeddings 
    within a localized ChromaDB instance.
    """
    
    def __init__(self, persist_directory: str = "./chroma_data", collection_name: str = "video_assets"):
        """
        Initializes the vector database client and the embedding transformation function.
        """
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def insert_chunks(self, project_id: str, document_name: str, chunks: List[str]) -> None:
        """
        Transforms raw text chunks into vector embeddings and persists them with metadata.
        
        Args:
            project_id (str): The isolated workspace identifier for the data.
            document_name (str): The source origin of the text chunks.
            chunks (List[str]): The payload array of text segments.
        """
        if not chunks:
            return

        vector_ids = []
        chunk_metadata = []
        
        for index in range(len(chunks)):
            unique_id = f"{project_id}_{uuid.uuid4().hex[:8]}"
            vector_ids.append(unique_id)
            
            chunk_metadata.append({
                "project_id": project_id,
                "source": document_name,
                "chunk_index": index
            })

        self.collection.add(
            documents=chunks, 
            metadatas=chunk_metadata, 
            ids=vector_ids
        )

    def search_chunks(self, project_id: str, query: str, top_k: int = 3) -> List[str]:
        """
        Executes a semantic similarity search against the vector space, 
        filtered strictly by the designated project workspace.
        
        Args:
            project_id (str): The workspace identifier restricting the search domain.
            query (str): The natural language query to match.
            top_k (int): The maximum number of relevant chunks to retrieve.
            
        Returns:
            List[str]: The top matching textual segments.
        """
        query_results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"project_id": project_id} 
        )
        
        if query_results and "documents" in query_results and query_results["documents"]:
            return query_results["documents"][0]
        return []