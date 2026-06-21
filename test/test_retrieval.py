import os
import sys
from pathlib import Path

# Add backend directory to path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent / "backend"))

from app.services.retrieval_service import RetrievalService

def main():
    print("=== Phase 6: Context Retrieval & Metadata Filtering Test ===")
    
    # Check credentials
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("\n[!] Error: PINECONE_API_KEY environment variable is not set in .env.")
        return
        
    retriever = RetrievalService()
    
    # Test Query 1: Retrieval without subject filtering (across all subjects)
    query_all = "What is database normalization and functional dependencies?"
    print(f"\n[1] Running query without subject filter:")
    print(f"    Query: '{query_all}'")
    
    matches_all = retriever.retrieve_context(query=query_all, top_k=3)
    print(f"    Retrieved {len(matches_all)} match(es):")
    for i, match in enumerate(matches_all):
        print(f"    * Match {i+1} | Score: {match.get('score')} | Chunk: {match.get('chunk_id')}")
        print(f"      - File:    {match['metadata'].get('filename')}")
        print(f"      - Subject: {match['metadata'].get('subject')}")
        print(f"      - Source:  {match['metadata'].get('source')}")
        
    # Test Query 2: Retrieval with subject filtering matching our indexed subject
    subject_match = "data_privacy_and_security"
    print(f"\n[2] Running query with matching subject filter:")
    print(f"    Query:   '{query_all}'")
    print(f"    Subject: '{subject_match}'")
    
    matches_filtered = retriever.retrieve_context(query=query_all, subject=subject_match, top_k=3)
    print(f"    Retrieved {len(matches_filtered)} match(es):")
    all_subject_correct = True
    for i, match in enumerate(matches_filtered):
        subj = match['metadata'].get('subject')
        print(f"    * Match {i+1} | Score: {match.get('score')} | Chunk: {match.get('chunk_id')}")
        print(f"      - File:    {match['metadata'].get('filename')}")
        print(f"      - Subject: {subj}")
        if subj != subject_match:
            all_subject_correct = False
            
    if all_subject_correct:
        print("\n[SUCCESS] All retrieved matches belong to the filtered subject: " + subject_match)
    else:
        print("\n[WARNING] Metadata filtering returned elements outside the target subject!")
        
    # Test Query 3: Retrieval with subject filtering mismatch (should return empty or unrelated)
    subject_mismatch = "OOP"
    print(f"\n[3] Running query with non-matching subject filter (no OOP documents are indexed yet):")
    print(f"    Query:   '{query_all}'")
    print(f"    Subject: '{subject_mismatch}'")
    
    matches_mismatch = retriever.retrieve_context(query=query_all, subject=subject_mismatch, top_k=3)
    print(f"    Retrieved {len(matches_mismatch)} match(es):")
    for i, match in enumerate(matches_mismatch):
        print(f"    * Match {i+1} | Score: {match.get('score')} | Chunk: {match.get('chunk_id')}")
        print(f"      - File:    {match['metadata'].get('filename')}")
        print(f"      - Subject: {match['metadata'].get('subject')}")

if __name__ == "__main__":
    main()
