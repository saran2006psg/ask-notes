import os
import sys
from pathlib import Path

# Add backend directory to path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.retrieval_service import RetrievalService
from app.services.prompt_service import PromptService
from app.services.llm_service import LLMService
from app.services.citation_service import CitationService

def main():
    print("=== Phase 9: Source Citations Engine Verification ===")
    
    # Check credentials
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("\n[!] Error: GROQ_API_KEY environment variable is not set in .env.")
        return
        
    retriever = RetrievalService()
    prompter = PromptService()
    llm = LLMService()
    cit_engine = CitationService()
    
    test_query = "Explain the basic concepts of SNA in data privacy and security notes."
    print(f"\nUser Question: '{test_query}'")
    
    print("\n[1] Retrieving relevant notes & Reranking...")
    chunks = retriever.retrieve_context(query=test_query, top_k=4, rerank=True)
    print(f"    Retrieved {len(chunks)} chunks.")
    
    print("\n[2] Assembling prompt...")
    prompt = prompter.build_prompt(query=test_query, chunks=chunks)
    
    print("\n[3] Generating answer using Groq (Llama-3.1-8b-instant)...")
    answer = llm.generate_answer(prompt=prompt)
    
    print("\n[4] Running citation engine to extract and verify source references...")
    verified_cits = cit_engine.citation_engine(answer=answer, retrieved_chunks=chunks)
    
    print("\n======================================================================")
    print("GROQ ANSWER OUTPUT")
    print("======================================================================")
    sanitized_answer = answer.replace("\u2022", "*").encode('ascii', errors='ignore').decode('ascii')
    print(sanitized_answer)
    
    print("\n======================================================================")
    print("VERIFIED SOURCE CITATIONS (Parsed & Validated)")
    print("======================================================================")
    print(f"Total Verified Citations Used in Answer: {len(verified_cits)}")
    for idx, cit in enumerate(verified_cits):
        print(f"\n[{idx + 1}] Source: {cit.get('source')}")
        print(f"    - File:    {cit.get('filename')}")
        print(f"    - Subject: {cit.get('subject')}")
        print(f"    - Page:    {cit.get('page')}")
        print(f"    - Vector Score: {cit.get('score')}")
    print("======================================================================")

if __name__ == "__main__":
    main()
