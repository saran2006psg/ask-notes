import logging
from typing import List, Dict, Any, Optional

from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.vector_store = VectorStoreService()
        
    def retrieve_context(
        self, 
        query: str, 
        subject: Optional[str] = None, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieves matching document chunks for a given query, optionally filtered by subject.
        
        Args:
            query (str): The natural language query.
            subject (str, optional): The subject category to filter by (e.g. 'DBMS', 'OS').
            top_k (int): Number of context chunks to retrieve.
            
        Returns:
            List[Dict[str, Any]]: List of matching chunks with text, scores, and metadata.
        """
        logger.info(f"Retrieval Request: query='{query}' | subject={subject} | top_k={top_k}")
        
        try:
            # 1. Embed query
            query_vector = self.embedder.embed_text(query)
            
            # 2. Similarity search in Pinecone
            matches = self.vector_store.similarity_search(
                query_vector=query_vector,
                top_k=top_k,
                subject=subject
            )
            
            logger.info(f"Retrieved {len(matches)} match(es) from Pinecone.")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return []
