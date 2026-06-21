import os
import sys
import json
from pathlib import Path

# Add backend directory to path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.vector_store import VectorStoreService
from app.services.embedding_service import EmbeddingService

def main():
    print("=== Phase 5: Knowledge Base (Pinecone) Indexing & Query Test ===")
    
    # Check credentials
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("\n[!] Error: PINECONE_API_KEY environment variable is not set.")
        print("    Please set the key in your terminal before running this script.")
        print("    Example (PowerShell): $env:PINECONE_API_KEY='your-key'")
        print("    Example (Command Prompt): set PINECONE_API_KEY=your-key\n")
        return
        
    # 1. Initialize service
    vs = VectorStoreService()
    
    # 2. Trigger indexing of all cached vector files
    print("\nIndexing cached vector files into Pinecone...")
    index_stats = vs.index_embedded_chunks()
    
    print("\n=== Indexing Results ===")
    print(f"  * Scanned Files:  {index_stats.get('scanned_files')}")
    print(f"  * Indexed Chunks: {index_stats.get('indexed_chunks')}")
    print(f"  * Embedding Provider: {str(index_stats.get('provider')).upper()} ({index_stats.get('dimension')} dims)")
    
    if index_stats.get("failed_files"):
        print(f"  [!] Failed Files:")
        for f in index_stats["failed_files"]:
            print(f"    - {f.get('filename')}: {f.get('error')}")
            
    # 3. Retrieve DB stats
    db_stats = vs.get_stats()
    print("\n====================================================")
    print("VECTOR STORE COLLECTION STATISTICS")
    print("====================================================")
    print(f"  * Status:          {db_stats.get('status').upper()}")
    print(f"  * Index Name:      {db_stats.get('index_name')}")
    print(f"  * Total Chunks:    {db_stats.get('total_chunks')}")
    print(f"  * Host:            {db_stats.get('host')}")
    
    if db_stats.get("total_chunks") == 0:
        print("\n[!] Index is empty. Cannot run test query.")
        return
        
    # 4. Perform a test similarity query
    print("\n====================================================")
    print("SIMILARITY QUERY TEST")
    print("====================================================")
    
    test_query = "What is database normalization and functional dependencies?"
    print(f"  * Test Query: \"{test_query}\"")
    
    print("  * Generating vector embedding for query...")
    embedder = EmbeddingService()
    query_vector = embedder.embed_text(test_query)
    
    print(f"  * Querying Pinecone (retrieving top 3 matches)...")
    matches = vs.similarity_search(query_vector, top_k=3)
    
    print(f"\nFound {len(matches)} match(es):")
    for idx, match in enumerate(matches):
        print(f"\n[{idx + 1}] Match Score: {match.get('score')} | Chunk ID: {match.get('chunk_id')}")
        print(f"    - Source: {match['metadata'].get('source')}")
        print(f"    - File:   {match['metadata'].get('filename')}")
        print(f"    - Text Content:")
        print("      " + "-" * 60)
        # Indent the text lines
        text_lines = match.get("text", "").strip().split("\n")
        indented_text = "\n      ".join(text_lines[:4])
        if len(text_lines) > 4:
            indented_text += "\n      ... [truncated]"
        print(f"      {indented_text}")
        print("      " + "-" * 60)

if __name__ == "__main__":
    main()
