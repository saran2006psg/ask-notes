import os
import sys
import json
from pathlib import Path

# Add backend directory to path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent / "backend"))

from app.core import config
from app.services import document_service

def main():
    print("=== Phase 4: Vector Embeddings Generation Test ===")
    
    # Run embedding pipeline
    print("\nRunning generate_embeddings()...")
    results = document_service.generate_embeddings()
    
    print("\n=== Processing Results ===")
    for res in results:
        status = res.get("status")
        filename = res.get("filename")
        subject = res.get("subject")
        
        if status == "embedded":
            print(f"[SUCCESS] {filename} -> Subject: {subject} | Chunks: {res.get('total_chunks')} | Provider: {res.get('provider').upper()} ({res.get('dimension')} dims)")
        elif status == "skipped":
            print(f"[SKIPPED] {filename} -> Subject: {subject} | Reason: {res.get('reason')}")
        else:
            print(f"[FAILED] {filename} -> Error: {res.get('error')}")
            
    # Query stats
    stats = document_service.get_embedding_statistics()
    print("\n====================================================")
    print("📊 EMBEDDING STATISTICS SUMMARY")
    print("====================================================")
    print(f"  • Total Embedded Documents: {stats.get('total_embedded_documents')}")
    print(f"  • Total Embedded Chunks:    {stats.get('total_embedded_chunks')}")
    
    print("\nProviders Used:")
    for prov, count in stats.get("providers_used", {}).items():
        print(f"  - {prov.upper()}: {count} document(s)")
        
    print("\nEmbeddings by Subject:")
    for subj, count in stats.get("by_subject", {}).items():
        print(f"  - {subj}: {count} chunk(s)")
        
    # Sample preview of the first vector
    embedded_files = list(document_service.EMBEDDED_DIR.glob("**/*_embedded.json"))
    if embedded_files:
        print("\n====================================================")
        print("🔍 VECTOR EMBEDDING PREVIEW")
        print("====================================================")
        try:
            with open(embedded_files[0], "r", encoding="utf-8") as f:
                data = json.load(f)
                
            chunks = data.get("chunks", [])
            if chunks:
                sample = chunks[0]
                vector = sample.get("embedding", [])
                print(f"  • Chunk ID:  {sample.get('chunk_id')}")
                print(f"  • Provider:  {data.get('provider').upper()}")
                print(f"  • Dimension: {data.get('dimension')} dims")
                print(f"  • Vector Snippet (First 10 values):")
                print(f"    {vector[:10]}")
                print(f"    (Total elements in vector: {len(vector)})")
        except Exception as e:
            print(f"Error loading vector preview: {e}")

if __name__ == "__main__":
    main()
