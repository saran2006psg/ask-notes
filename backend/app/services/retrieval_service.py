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
    ) -> Dict[str, Any]:
        """
        Retrieves matching document chunks for a given query, optionally filtered by subject.
        
        Returns:
            Dict with keys:
              - "chunks": List of matching chunk dicts (text, score, metadata)
              - "images": List of unique image dicts [{path, description, url}] from all matched chunks
        """
        logger.info(f"Retrieval Request: query='{query}' | subject={subject} | top_k={top_k} | rerank={rerank} | user_id={user_id}")
        
        try:
            # 1. Embed query using retrieval_query task_type for better matching
            query_vector = self.embedder.embed_query(query)
            
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
                
            chunks = matches[:top_k]

            # 4. Collect unique images from all matched chunks
            seen_paths = set()
            images = []
            for chunk in chunks:
                chunk_paths = chunk.get("image_paths", [])
                chunk_descs = chunk.get("image_descriptions", [])
                for i, path in enumerate(chunk_paths):
                    if path and path not in seen_paths:
                        seen_paths.add(path)
                        desc = chunk_descs[i] if i < len(chunk_descs) else ""
                        # Build a relative URL for the frontend to fetch
                        from pathlib import Path as _Path
                        from app.core import config as _cfg
                        try:
                            rel = _Path(path).relative_to(_cfg.IMAGES_DIR)
                            url = f"/api/images/{rel.as_posix()}"
                        except ValueError:
                            url = f"/api/images/{_Path(path).name}"
                        images.append({"path": path, "description": desc, "url": url})

            logger.info(f"Returning {len(chunks)} chunks and {len(images)} unique image(s).")
            return {"chunks": chunks, "images": images}
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return {"chunks": [], "images": []}

