import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class RerankingService:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        self.model = None
        self.enabled = False
        
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Reranking Service: Loading CrossEncoder model '{model_name}'...")
            # Load CrossEncoder model
            self.model = CrossEncoder(model_name)
            self.enabled = True
            logger.info("Reranking Service: Model successfully loaded.")
        except Exception as e:
            logger.warning(
                f"Reranking Service: Failed to load cross-encoder model '{model_name}'. "
                f"Reranking is disabled. Fallback to vector DB scoring. Error: {e}"
            )
            
    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rerank a list of chunks using BGE Cross-Encoder relative to the user query.
        
        Args:
            query (str): User natural language question.
            chunks (List[Dict[str, Any]]): Retrieved chunks list from Pinecone.
            top_k (int): Number of top reranked chunks to return.
            
        Returns:
            List[Dict[str, Any]]: Reranked and sorted chunks.
        """
        if not chunks:
            return []
            
        if not self.enabled or self.model is None:
            logger.info("Reranking Service: Reranker is disabled or not loaded. Returning top_k chunks sorted by Pinecone score.")
            return chunks[:top_k]
            
        try:
            logger.info(f"Reranking Service: Scoring {len(chunks)} chunks using '{self.model_name}'...")
            
            # Construct query-passage pairs
            pairs = [[query, chunk["text"]] for chunk in chunks]
            
            # Compute cross-encoder similarity scores
            scores = self.model.predict(pairs)
            
            # Update chunks with the new score and merge old/new scores for metadata
            reranked_chunks = []
            for idx, chunk in enumerate(chunks):
                updated_chunk = chunk.copy()
                # Store original pinecone score inside metadata for verification/comparisons
                updated_chunk["metadata"] = chunk.get("metadata", {}).copy()
                updated_chunk["metadata"]["original_pinecone_score"] = chunk.get("score", 0.0)
                
                # Assign new cross-encoder score
                updated_chunk["score"] = round(float(scores[idx]), 4)
                reranked_chunks.append(updated_chunk)
                
            # Sort by the new cross-encoder score descending
            reranked_chunks.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(f"Reranking Service: Successfully reranked and sorted chunks.")
            return reranked_chunks[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking Service: Reranking failed: {e}. Falling back to default scoring.")
            return chunks[:top_k]
