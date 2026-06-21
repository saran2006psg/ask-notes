import os
import sys
from pathlib import Path

# Add backend directory to path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent / "backend"))

from app.services.retrieval_service import RetrievalService
from app.services.prompt_service import PromptService
from app.services.llm_service import LLMService

def main():
    print("=== Phase 8: RAG Answer Generation (Groq) Test ===")
    
    # Check credentials
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("\n[!] Error: GROQ_API_KEY environment variable is not set in .env.")
        return
        
    retriever = RetrievalService()
    prompter = PromptService()
    llm = LLMService()
    
    # Query related to differential privacy (which is in our indexed data)
    test_query = "What is the basic concept of differential privacy?"
    print(f"\nUser Question: '{test_query}'")
    
    print("\n[1] Retrieving relevant notes from Pinecone & Reranking...")
    chunks = retriever.retrieve_context(query=test_query, top_k=3, rerank=True)
    print(f"    Retrieved {len(chunks)} context segments.")
    for idx, c in enumerate(chunks):
        print(f"    * Cit. [{idx+1}]: {c['metadata'].get('filename')} (Page {c['metadata'].get('page')}) | Score: {c.get('score')}")
        
    print("\n[2] Assembling prompt templates...")
    prompt = prompter.build_prompt(query=test_query, chunks=chunks)
    
    print("\n[3] Querying Groq API completion (Llama-3.1-8b-instant)...")
    answer = llm.generate_answer(prompt=prompt)
    
    print("\n======================================================================")
    print("GROQ GENERATED ANSWER (Grounded in Notes)")
    print("======================================================================")
    # Sanitize answer for Windows command prompt character mapping (CP1252)
    sanitized_answer = answer.replace("\u2022", "*").encode('ascii', errors='ignore').decode('ascii')
    print(sanitized_answer)
    print("======================================================================")

if __name__ == "__main__":
    main()
