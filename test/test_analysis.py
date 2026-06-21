import os

import sys
from pathlib import Path

# Add backend directory to path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent / "backend"))

from app.core import config
from app.services import document_service

def main():
    print("=== Phase 2: Document Dataset Analysis Test ===")
    
    # Run analysis
    analysis = document_service.analyze_documents()
    overall = analysis.get("overall", {})
    by_subject = analysis.get("by_subject", {})
    by_document = analysis.get("by_document", [])
    
    if not by_document:
        print("\n[!] No analyzed documents found.")
        print("Please ensure that you have run 'python test_ingest.py' to extract text from your notes first.")
        return
        
    print("\n====================================================")
    print("OVERALL DATASET METRICS")
    print("====================================================")
    print(f"  * Total Documents:  {overall.get('total_documents')}")
    print(f"  * Total Pages/Slides: {overall.get('total_pages')}")
    print(f"  * Total Word Count:  {overall.get('total_words')}")
    print(f"  * Total Characters:  {overall.get('total_characters')}")
    
    print("\nFormats Distribution:")
    for fmt, count in overall.get("formats", {}).items():
        print(f"  - {fmt}: {count} file(s)")
        
    print("\n====================================================")
    print("SUBJECT-LEVEL BREAKDOWN")
    print("====================================================")
    for subject, stats in by_subject.items():
        print(f"\nSubject: {subject}")
        print(f"  * Files:      {stats.get('document_count')}")
        print(f"  * Pages:      {stats.get('total_pages')}")
        print(f"  * Words:      {stats.get('total_words')}")
        print(f"  * Characters: {stats.get('total_characters')}")
        
    print("\n====================================================")
    print("INDIVIDUAL DOCUMENT BREAKDOWN")
    print("====================================================")
    # Format header
    print(f"{'Filename':<40} | {'Format':<6} | {'Pages':<5} | {'Words':<8} | {'Characters':<10}")
    print("-" * 80)
    for doc in by_document:
        filename = doc.get("filename")
        # Truncate filename if too long for display
        display_name = filename if len(filename) <= 40 else filename[:37] + "..."
        print(f"{display_name:<40} | {doc.get('format'):<6} | {doc.get('pages'):<5} | {doc.get('words'):<8} | {doc.get('characters'):<10}")

if __name__ == "__main__":
    main()
