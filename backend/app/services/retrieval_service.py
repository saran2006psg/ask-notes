import logging
from typing import List, Dict, Any, Optional

from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.services.reranking_service import RerankingService

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.vector_store = VectorStoreService()
        self.reranker = RerankingService()
        
    def retrieve_context(
        self, 
        query: str, 
        subject: Optional[str] = None, 
        top_k: int = 5,
        rerank: bool = True,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves matching document chunks for a given query, optionally filtered by subject.
        
        Args:
            query (str): The natural language query.
            subject (str, optional): The subject category to filter by (e.g. 'DBMS', 'OS').
            top_k (int): Number of context chunks to retrieve.
            rerank (bool): Whether to use BGE reranker to refine results.
            user_id (str, optional): The user identifier to restrict query matching scope.
            
        Returns:
            List[Dict[str, Any]]: List of matching chunks with text, scores, and metadata.
        """
        logger.info(f"Retrieval Request: query='{query}' | subject={subject} | top_k={top_k} | rerank={rerank} | user_id={user_id}")
        
        try:
            # 1. Embed query
            query_vector = self.embedder.embed_text(query)
            
            # 2. Similarity search in Pinecone
            # If reranking is enabled, retrieve a larger pool of candidate chunks first
            search_k = max(20, top_k * 4) if rerank else top_k
            
            matches = self.vector_store.similarity_search(
                query_vector=query_vector,
                top_k=search_k,
                subject=subject,
                user_id=user_id
            )
            
            logger.info(f"Retrieved {len(matches)} candidate match(es) from Pinecone.")
            
            # 3. Apply Cross-Encoder Reranking
            if rerank and matches:
                logger.info(f"Applying cross-encoder reranking to return top {top_k} results...")
                matches = self.reranker.rerank(query=query, chunks=matches, top_k=top_k)
                
            return matches[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return []
