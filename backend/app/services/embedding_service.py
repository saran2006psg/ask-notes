import os
import math
import logging
from typing import List

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.provider = None
        self.model = None
        self.dimension = 0
        
        # Check for Gemini API key in env or .env file
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.provider = "gemini"
                self.dimension = 1024
                logger.info("Embedding Service: Successfully initialized Gemini API (gemini-embedding-001, 1024-dim)")
                return
            except ImportError:
                logger.warning("Gemini API key is configured, but 'google-generativeai' package is not installed.")
                
        # Try importing and loading sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            # Load lightweight Model (downloads ~90MB)
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.provider = "local"
            self.dimension = 384
            logger.info("Embedding Service: Successfully initialized local SentenceTransformer (all-MiniLM-L6-v2)")
            return
        except ImportError:
            logger.warning("sentence-transformers/torch package is not installed.")
            
        # Fallback to deterministic mock vectors
        self.provider = "mock"
        self.dimension = 128
        logger.warning("Embedding Service: Fallback to mock deterministic embeddings (128-dim).")
        
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of strings. Returns a list of vectors.
        """
        if not texts:
            return []
            
        if self.provider == "gemini":
            import google.generativeai as genai
            try:
                response = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=texts,
                    task_type="retrieval_document",
                    output_dimensionality=1024
                )
                # embed_content returns a list when given a list
                embs = response["embedding"]
                # Handle both single and batch responses
                if embs and isinstance(embs[0], float):
                    return [embs]  # single text was passed
                return embs
            except Exception as e:
                logger.error(f"Gemini API embedding failed: {e}. Falling back to local/mock.")
                
        if self.provider == "local" and self.model:
            try:
                embeddings = self.model.encode(texts, show_progress_bar=False)
                return embeddings.tolist()
            except Exception as e:
                logger.error(f"Local SentenceTransformer embedding failed: {e}. Falling back to mock.")
                
        # Mock Vector Fallback (Deterministic by hashing sentence contents)
        import random
        mock_embeddings = []
        for text in texts:
            text_hash = hash(text) & 0xffffffff
            random.seed(text_hash)
            
            vec = [random.uniform(-1.0, 1.0) for _ in range(self.dimension)]
            sq_sum = sum(x**2 for x in vec)
            norm = math.sqrt(sq_sum) if sq_sum > 0 else 1.0
            normalized_vec = [x / norm for x in vec]
            
            mock_embeddings.append(normalized_vec)
            
        return mock_embeddings
        
    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single string for document indexing.
        """
        return self.embed_texts([text])[0]

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a query string using retrieval_query task_type for better semantic matching.
        """
        if self.provider == "gemini":
            import google.generativeai as genai
            try:
                response = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=query,
                    task_type="retrieval_query",
                    output_dimensionality=1024
                )
                embs = response["embedding"]
                if embs and isinstance(embs[0], float):
                    return embs
                return embs[0]
            except Exception as e:
                logger.error(f"Gemini query embedding failed: {e}. Falling back to embed_text.")
        # Fallback: use standard embed_texts
        return self.embed_texts([query])[0]
