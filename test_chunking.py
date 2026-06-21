import os
import sys
import json
from pathlib import Path

# Add backend directory to path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent / "backend"))

from app.core import config
from app.services import document_service

def main():
    print("=== Phase 3: Semantic Chunking & Metadata Injection Test ===")
    
    # Run chunking
    print("\nRunning create_chunks()...")
    results = document_service.create_chunks()
    
    print("\n=== Processing Results ===")
    for res in results:
        status = res.get("status")
        filename = res.get("filename")
        subject = res.get("subject")
        
        if status == "chunked":
            print(f"[SUCCESS] {filename} -> Subject: {subject} | Generated Chunks: {res.get('total_chunks')} (Saved to disk)")
        else:
            print(f"[FAILED] {filename} -> Error: {res.get('error')}")
            
    # Fetch overall stats
    stats = document_service.get_chunk_statistics()
    print("\n====================================================")
    print("CHUNKING STATISTICS SUMMARY")
    print("====================================================")
    print(f"  * Total Documents Chunked: {stats.get('total_documents')}")
    print(f"  * Total Chunks Generated:  {stats.get('total_chunks')}")
    print(f"  * Avg Chunks Per Document: {stats.get('average_chunks_per_doc')}")
    
    print("\nChunks by Subject:")
    for subj, count in stats.get("by_subject", {}).items():
        print(f"  - {subj}: {count} chunk(s)")
        
    # Print a sample chunk to verify text + metadata
    chunk_files = list(document_service.CHUNKS_DIR.glob("**/*_chunks.json"))
    if chunk_files:
        print("\n====================================================")
        print("SAMPLE CHUNK DATA PREVIEW")
        print("====================================================")
        try:
            with open(chunk_files[0], "r", encoding="utf-8") as f:
                data = json.load(f)
            
            chunks = data.get("chunks", [])
            if chunks:
                sample = chunks[0]
                print(f"  * Chunk ID: {sample.get('chunk_id')}")
                print(f"  * Content Length: {len(sample.get('text'))} chars")
                print("  * Metadata:")
                for k, v in sample.get("metadata", {}).items():
                    print(f"      - {k}: {v}")
                print("  • Text Content Preview:")
                print("    " + "-" * 50)
                text = sample.get("text")
                # Indent lines of text preview
                indented_text = "\n    ".join(text.split("\n"))
                print(f"    {indented_text}")
                print("    " + "-" * 50)
        except Exception as e:
            print(f"Error loading sample chunk: {e}")

if __name__ == "__main__":
    main()
