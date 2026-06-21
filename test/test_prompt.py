import os
import sys
from pathlib import Path

# Add backend directory to path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.retrieval_service import RetrievalService
from app.services.prompt_service import PromptService

def main():
    print("=== Phase 7: Prompt Construction Test ===")
    
    # Check credentials
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("\n[!] Error: PINECONE_API_KEY environment variable is not set in .env.")
        return
        
    retriever = RetrievalService()
    prompter = PromptService()
    
    test_query = "What is database normalization and functional dependencies?"
    print(f"\nRetrieving context segments for: '{test_query}'...")
    
    # Retrieve top 2 matches (reranked)
    chunks = retriever.retrieve_context(query=test_query, top_k=2, rerank=True)
    
    # Build prompt
    print("\nBuilding grounded RAG prompt...")
    compiled_prompt = prompter.build_prompt(query=test_query, chunks=chunks)
    
    print("\n======================================================================")
    print("COMPILED RAG PROMPT")
    print("======================================================================")
    # Sanitize prompt output for Windows command prompt character mapping (CP1252)
    sanitized_prompt = compiled_prompt.replace("\u2022", "*").encode('ascii', errors='ignore').decode('ascii')
    print(sanitized_prompt)
    print("======================================================================")

if __name__ == "__main__":
    main()
