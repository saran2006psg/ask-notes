import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from pinecone import Pinecone, ServerlessSpec
from app.core import config

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self, index_name: str = "ask-notes"):
        self.index_name = index_name
        self.pc = None
        self.index = None
        self.target_dimension = 384
        self._initialize_db()
        
    def _initialize_db(self):
        """
        Initializes the Pinecone client.
        """
        try:
            api_key = os.environ.get("PINECONE_API_KEY")
            if not api_key:
                logger.warning("Pinecone: PINECONE_API_KEY environment variable is not set. Service offline.")
                return
                
            self.pc = Pinecone(api_key=api_key)
            logger.info("Pinecone: Client successfully initialized.")
        except Exception as e:
            logger.error(f"Pinecone: Initialization failed: {e}")
            raise e
            
    def _get_index(self, dimension: int = 384) -> Any:
        """
        Ensures index exists and returns the Pinecone Index connection.
        """
        if self.pc is None:
            raise ValueError("Pinecone client is not initialized. Please set PINECONE_API_KEY.")
            
        if self.index is not None:
            return self.index
            
        # Get list of index names
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        
        # If it doesn't exist, create a serverless index
        if self.index_name not in existing_indexes:
            logger.info(f"Pinecone: Creating serverless index '{self.index_name}' (dimension={dimension})...")
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            
        self.index = self.pc.Index(self.index_name)
        
        # Describe index to retrieve actual dimensions
        try:
            desc = self.pc.describe_index(self.index_name)
            self.target_dimension = desc.dimension
            logger.info(f"Pinecone: Connected to index '{self.index_name}' (dimension={self.target_dimension})")
        except Exception as e:
            logger.warning(f"Pinecone: Could not describe index, defaulting target dimension to {dimension}. Error: {e}")
            self.target_dimension = dimension
            
        return self.index
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Return the statistics of the Pinecone vector index.
        """
        if self.pc is None:
            return {"status": "offline", "total_chunks": 0}
            
        try:
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            if self.index_name not in existing_indexes:
                return {
                    "status": "online",
                    "index_name": self.index_name,
                    "total_chunks": 0,
                    "info": "Index does not exist yet (will be created during first ingestion)."
                }
                
            desc = self.pc.describe_index(self.index_name)
            idx = self.pc.Index(self.index_name)
            index_stats = idx.describe_index_stats()
            
            return {
                "status": "online",
                "index_name": self.index_name,
                "total_chunks": index_stats.get("total_vector_count", 0),
                "dimension": desc.dimension,
                "metric": desc.metric,
                "host": desc.host
            }
        except Exception as e:
            logger.error(f"Pinecone: Failed to get index statistics: {e}")
            return {"status": "error", "error": str(e)}
            
    def index_embedded_chunks(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans data/embedded/ recursively, loads chunks and vectors,
        provisions the Pinecone index, and upserts in batches.
        """
        stats = {
            "scanned_files": 0,
            "indexed_chunks": 0,
            "failed_files": [],
            "provider": None,
            "dimension": 0
        }
        
        embedded_dir = config.DATA_DIR / "embedded"
        if user_id:
            embedded_dir = embedded_dir / user_id
            
        if not embedded_dir.exists():
            logger.warning("No embedded files found. Please generate embeddings first.")
            return stats
            
        embedded_files = []
        for p in embedded_dir.glob("**/*_embedded.json"):
            if not user_id:
                try:
                    rel = p.relative_to(config.DATA_DIR / "embedded")
                    if rel.parts and rel.parts[0].startswith("user_"):
                        continue
                except Exception:
                    pass
            embedded_files.append(p)
            
        if not embedded_files:
            logger.warning("No embedded JSON files found in data/embedded/.")
            return stats
            
        logger.info(f"Pinecone: Found {len(embedded_files)} embedded file(s) to index.")
        
        # Load the first file to detect dimension size dynamically
        try:
            with open(embedded_files[0], "r", encoding="utf-8") as f:
                sample_data = json.load(f)
            dimension = sample_data.get("dimension", 384)
            stats["dimension"] = dimension
            stats["provider"] = sample_data.get("provider")
        except Exception as e:
            logger.error(f"Pinecone: Failed to read dimension from sample file: {e}")
            raise e
            
        # Get index client connection (creates index if missing)
        try:
            idx_connection = self._get_index(dimension=dimension)
        except Exception as e:
            logger.error(f"Pinecone: Database connection failed: {e}")
            return {"status": "error", "error": str(e)}
            
        for file_path in embedded_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                filename = data.get("filename")
                subject = data.get("subject", "General")
                chunks = data.get("chunks", [])
                
                if not chunks:
                    continue
                    
                vectors_to_upsert = []
                for chunk in chunks:
                    # In Pinecone, the raw text MUST be stored inside the metadata payload
                    # because Pinecone only stores IDs and vectors.
                    meta = chunk["metadata"].copy()
                    meta["text"] = chunk["text"]
                    if user_id:  # Only tag user_id when explicitly set
                        meta["user_id"] = user_id

                    # Serialize image_paths as JSON string (Pinecone metadata only supports scalars)
                    image_paths = meta.pop("image_paths", []) or []
                    image_descriptions = meta.pop("image_descriptions", []) or []
                    if image_paths:
                        meta["image_paths_json"] = json.dumps(image_paths)
                    if image_descriptions:
                        meta["image_descriptions_json"] = json.dumps(image_descriptions)
                    
                    # Pad/truncate vector if index dimension mismatches chunk embedding dimension
                    raw_emb = chunk["embedding"]
                    target_dim = getattr(self, "target_dimension", len(raw_emb))
                    if len(raw_emb) != target_dim:
                        if len(raw_emb) < target_dim:
                            padded_emb = raw_emb + [0.0] * (target_dim - len(raw_emb))
                        else:
                            padded_emb = raw_emb[:target_dim]
                    else:
                        padded_emb = raw_emb
                        
                    vectors_to_upsert.append({
                        "id": chunk["chunk_id"],
                        "values": padded_emb,
                        "metadata": meta
                    })
                    
                # Index in batches of 200 to prevent exceeding payload sizes
                batch_size = 200
                total_chunks = len(vectors_to_upsert)
                
                for start_idx in range(0, total_chunks, batch_size):
                    end_idx = start_idx + batch_size
                    batch = vectors_to_upsert[start_idx:end_idx]
                    
                    idx_connection.upsert(vectors=batch)
                    
                stats["scanned_files"] += 1
                stats["indexed_chunks"] += total_chunks
                logger.info(f"Pinecone: Indexed {total_chunks} chunks from '{filename}'")
                
            except Exception as e:
                logger.error(f"Pinecone: Failed to index file {file_path.name}: {e}")
                stats["failed_files"].append({
                    "filename": file_path.name,
                    "error": str(e)
                })
                
        return stats
        
    def similarity_search(self, query_vector: List[float], top_k: int = 5, subject: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query Pinecone index using a vector. Returns matches with similarity scores.
        """
        if self.pc is None:
            logger.error("Pinecone: Client is offline.")
            return []
            
        try:
            # Connect to index if not already cached
            if self.index is None:
                self._get_index()
                
            # Pad/truncate vector if index dimension mismatches query vector dimension
            target_dim = getattr(self, "target_dimension", len(query_vector))
            if len(query_vector) != target_dim:
                if len(query_vector) < target_dim:
                    query_vector = query_vector + [0.0] * (target_dim - len(query_vector))
                else:
                    query_vector = query_vector[:target_dim]
                    
            # Formulate query filter if subject or user_id is provided
            query_filter = {}
            if user_id:  # Only filter by user_id when explicitly set
                query_filter["user_id"] = user_id
            if subject:
                query_filter["subject"] = subject
                
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                filter=query_filter,
                include_metadata=True
            )
            
            formatted_results = []
            matches = results.get("matches", [])
            
            for m in matches:
                metadata = m.get("metadata", {})
                # Extract text out from metadata
                text = metadata.pop("text", "")

                # Deserialize image_paths and image_descriptions from JSON strings
                image_paths_json = metadata.pop("image_paths_json", None)
                image_descriptions_json = metadata.pop("image_descriptions_json", None)
                image_paths = json.loads(image_paths_json) if image_paths_json else []
                image_descriptions = json.loads(image_descriptions_json) if image_descriptions_json else []

                formatted_results.append({
                    "chunk_id": m.get("id"),
                    "text": text,
                    "score": round(m.get("score", 0.0), 4),
                    "metadata": metadata,
                    "image_paths": image_paths,
                    "image_descriptions": image_descriptions
                })
                
            return formatted_results
        except Exception as e:
            logger.error(f"Pinecone: Similarity query search failed: {e}")
            return []
