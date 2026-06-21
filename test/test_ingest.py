import os
import sys
from pathlib import Path

# Add backend directory to path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent / "backend"))

from app.core import config
from app.services import document_service

def main():
    print("=== Phase 1: Recursive Ingestion & Multi-Format Test ===")
    
    # Ensure notes and data/extracted directories exist
    config.NOTES_DIR.mkdir(parents=True, exist_ok=True)
    config.EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for files
    files = document_service.get_supported_files()
    if not files:
        print(f"\n[!] No supported files (PDF, PPTX, DOCX) found in notes/.")
        print("Please run: python create_dummy_pdfs.py to populate test documents.")
        return
        
    print(f"\nFound {len(files)} files to process:")
    for f in files:
        rel_path = f.relative_to(config.NOTES_DIR)
        print(f" - {rel_path} ({f.suffix.upper()[1:]} | {f.stat().st_size / 1024:.2f} KB)")
        
    print("\nRunning load_documents()...")
    results = document_service.load_documents()
    
    print("\n=== Ingestion Results ===")
    for res in results:
        status = res.get("status")
        filename = res.get("filename")
        subject = res.get("subject")
        fmt = res.get("format")
        
        if status == "processed":
            print(f"[SUCCESS] [{fmt}] {filename} -> Subject: {subject} | Pages/Slides: {res.get('total_pages')} (New Extraction)")
        elif status == "cached":
            print(f"[CACHED] [{fmt}] {filename} -> Subject: {subject} | Pages/Slides: {res.get('total_pages')} (Loaded from JSON)")
        else:
            print(f"[FAILED] [{fmt}] {filename} -> Subject: {subject} | Error: {res.get('error')}")
            
    # Check what is inside data/extracted recursively
    print("\n=== Cache Structure (data/extracted/) ===")
    extracted_jsons = list(config.EXTRACTED_DIR.glob("**/*.json"))
    for j in extracted_jsons:
        rel_json = j.relative_to(config.EXTRACTED_DIR)
        print(f" - {rel_json}")
        
    if extracted_jsons:
        import json
        print("\n=== Sample Extracted Data ===")
        # Load the first JSON file we find
        with open(extracted_jsons[0], "r", encoding="utf-8") as f:
            sample_data = json.load(f)
            
        print(f"File Name: {sample_data['filename']}")
        print(f"Classified Subject (Folder): {sample_data['subject']}")
        print(f"Document Format: {sample_data['format']}")
        print(f"Total Pages/Slides: {sample_data['total_pages']}")
        if sample_data['pages']:
            first_page = sample_data['pages'][0]
            print(f"--- Page/Slide {first_page['page_number']} Text (First 300 chars) ---")
            print(first_page['text'][:300] + "...")
            
if __name__ == "__main__":
    main()
