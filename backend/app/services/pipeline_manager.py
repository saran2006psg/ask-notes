import logging
from typing import Dict, Any, Optional

from app.services import document_service
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

class PipelineManager:
    @staticmethod
    def run_full_indexing_pipeline(user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the end-to-end document ingestion, chunking, embedding, 
        and vector store indexing pipeline.
        
        Args:
            user_id (str, optional): The user identifier to isolate operations.
            
        Returns:
            Dict[str, Any]: Execution statistics for each stage.
        """
        logger.info(f"=== Starting Full Indexing Pipeline for user_id={user_id} ===")
        stats = {
            "ingestion": {},
            "chunking": {},
            "embedding": {},
            "indexing": {},
            "status": "success"
        }
        
        try:
            # Stage 1: Ingestion
            logger.info("Pipeline Stage 1/4: Ingesting notes documents...")
            ingest_results = document_service.load_documents(user_id=user_id)
            processed_new = sum(1 for r in ingest_results if r.get("status") == "processed")
            loaded_cached = sum(1 for r in ingest_results if r.get("status") == "cached")
            failed_ingest = sum(1 for r in ingest_results if r.get("status") == "failed")
            
            stats["ingestion"] = {
                "total_scanned": len(ingest_results),
                "processed_new": processed_new,
                "loaded_cached": loaded_cached,
                "failed": failed_ingest
            }
            logger.info(f"Ingestion done. Scanned: {len(ingest_results)} | New: {processed_new} | Cached: {loaded_cached}")
            
            # Stage 2: Semantic Chunking
            logger.info("Pipeline Stage 2/4: Chunking text files semantically...")
            chunk_results = document_service.create_chunks(user_id=user_id)
            success_chunks = sum(1 for r in chunk_results if r.get("status") == "chunked")
            failed_chunks = sum(1 for r in chunk_results if r.get("status") == "failed")
            
            stats["chunking"] = {
                "total_documents": len(chunk_results),
                "successfully_chunked": success_chunks,
                "failed": failed_chunks
            }
            logger.info(f"Chunking done. Chunked docs: {success_chunks}")
            
            # Stage 3: Embedding Generation
            logger.info("Pipeline Stage 3/4: Generating vector embeddings...")
            embed_results = document_service.generate_embeddings(user_id=user_id)
            success_embeds = sum(1 for r in embed_results if r.get("status") == "embedded")
            failed_embeds = sum(1 for r in embed_results if r.get("status") == "failed")
            
            stats["embedding"] = {
                "total_documents": len(embed_results),
                "successfully_embedded": success_embeds,
                "failed": failed_embeds
            }
            logger.info(f"Embeddings done. Embedded docs: {success_embeds}")
            
            # Stage 4: Pinecone Vector Database Indexing
            logger.info("Pipeline Stage 4/4: Upserting vectors to Pinecone index...")
            vs = VectorStoreService()
            index_stats = vs.index_embedded_chunks(user_id=user_id)
            
            stats["indexing"] = index_stats
            logger.info(f"Pinecone indexing done. Chunks indexed: {index_stats.get('indexed_chunks')}")
            
            logger.info("=== Full Indexing Pipeline Successfully Completed ===")
            return stats
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            stats["status"] = "failed"
            stats["error"] = str(e)
            return stats
