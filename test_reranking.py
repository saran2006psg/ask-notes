import os
import sys
from pathlib import Path

# Add backend directory to path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent / "backend"))

from app.services.retrieval_service import RetrievalService

def main():
    print("=== Phase 13: Reranking System (BGE Cross-Encoder) Comparison Test ===")
    
    # Check credentials
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("\n[!] Error: PINECONE_API_KEY environment variable is not set in .env.")
        return
        
    retriever = RetrievalService()
    
    test_query = "What is database normalization and functional dependencies?"
    print(f"\nComparing results for query: '{test_query}'\n")
    
    # 1. Retrieve WITHOUT RERANKING (Vector Cosine Similarity only)
    print("----------------------------------------------------------------------")
    print("1. BEFORE RERANKING (Bi-Encoder / Pinecone Cosine Similarity only)")
    print("----------------------------------------------------------------------")
    matches_no_rerank = retriever.retrieve_context(query=test_query, top_k=3, rerank=False)
    
    for idx, match in enumerate(matches_no_rerank):
        print(f"\n[{idx + 1}] Match Score: {match.get('score')} | Chunk: {match.get('chunk_id')}")
        print(f"    - File:    {match['metadata'].get('filename')}")
        print(f"    - Subject: {match['metadata'].get('subject')}")
        print(f"    - Source:  {match['metadata'].get('source')}")
        # Sanitize text for Windows terminal output
        text = match.get("text", "").replace("\u2022", "*").encode('ascii', errors='ignore').decode('ascii')
        text_lines = text.strip().split("\n")
        indented_text = "\n      ".join(text_lines[:2])
        if len(text_lines) > 2:
            indented_text += "\n      ... [truncated]"
        print(f"    - Text Snippet:")
        print(f"      {indented_text}")
        
    # 2. Retrieve WITH RERANKING (BGE Cross-Encoder reranked)
    print("\n----------------------------------------------------------------------")
    print("2. AFTER RERANKING (BGE Cross-Encoder reranked)")
    print("----------------------------------------------------------------------")
    matches_rerank = retriever.retrieve_context(query=test_query, top_k=3, rerank=True)
    
    for idx, match in enumerate(matches_rerank):
        orig_score = match['metadata'].get('original_pinecone_score', 'N/A')
        print(f"\n[{idx + 1}] New Rerank Score: {match.get('score')} | (Original Pinecone Score: {orig_score})")
        print(f"    - Chunk:   {match.get('chunk_id')}")
        print(f"    - File:    {match['metadata'].get('filename')}")
        print(f"    - Subject: {match['metadata'].get('subject')}")
        print(f"    - Source:  {match['metadata'].get('source')}")
        # Sanitize text for Windows terminal output
        text = match.get("text", "").replace("\u2022", "*").encode('ascii', errors='ignore').decode('ascii')
        text_lines = text.strip().split("\n")
        indented_text = "\n      ".join(text_lines[:2])
        if len(text_lines) > 2:
            indented_text += "\n      ... [truncated]"
        print(f"    - Text Snippet:")
        print(f"      {indented_text}")

if __name__ == "__main__":
    main()
