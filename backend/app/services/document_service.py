import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

from app.core import config
from app.utils.pdf_parser import extract_pdf_data
from app.utils.pptx_parser import extract_pptx_data
from app.utils.docx_parser import extract_docx_data

logger = logging.getLogger(__name__)

def classify_subject(filename: str) -> str:
    """
    Fallback subject classifier based on filename if file is at root notes/ folder.
    """
    name_lower = filename.lower()
    if "dbms" in name_lower or "database" in name_lower:
        return "DBMS"
    elif "os" in name_lower or "operating" in name_lower or "system" in name_lower:
        return "Operating Systems"
    elif "cn" in name_lower or "network" in name_lower:
        return "Computer Networks"
    elif "oop" in name_lower or "object" in name_lower or "java" in name_lower or "c++" in name_lower:
        return "OOP"
    return "General"

def get_subject_for_file(file_path: Path) -> str:
    """
    Determine the subject: if in a subfolder under notes/, use subfolder name.
    If in the root notes/ folder, fallback to classify_subject(filename).
    """
    # Resolve paths to avoid symlink issues
    resolved_file = file_path.resolve()
    resolved_notes = config.NOTES_DIR.resolve()
    
    # If the file is directly in the notes root
    if resolved_file.parent == resolved_notes:
        return classify_subject(file_path.name)
        
    # If it's in a subfolder, the direct child of notes/ is the subject folder
    # e.g., resolved_file = /notes/OS/unit1/lecture.pdf -> relative to resolved_notes = OS/unit1/lecture.pdf
    # We want the top-level subfolder "OS" as the subject.
    try:
        relative_path = resolved_file.relative_to(resolved_notes)
        return relative_path.parts[0]
    except Exception:
        return classify_subject(file_path.name)

def get_extracted_path(file_path: Path, subject: str) -> Path:
    """
    Get the path where the extracted JSON file should be saved.
    Replicates directory structure under data/extracted/{subject}/{filename}.json
    """
    json_filename = file_path.with_suffix(".json").name
    subject_dir = config.EXTRACTED_DIR / subject
    subject_dir.mkdir(parents=True, exist_ok=True)
    return subject_dir / json_filename

def get_supported_files() -> List[Path]:
    """
    Find all PDF, PPTX, and DOCX files in NOTES_DIR and its subdirectories.
    """
    if not config.NOTES_DIR.exists():
        return []
    
    all_files = []
    # Recursively list files and filter by supported extensions
    for p in config.NOTES_DIR.glob("**/*"):
        if p.is_file() and p.suffix.lower() in [".pdf", ".pptx", ".docx"]:
            all_files.append(p)
            
    return all_files

def load_documents() -> List[Dict[str, Any]]:
    """
    Recursively scan NOTES_DIR, extract text using appropriate parser,
    save cached JSON by subject, and return list of results.
    """
    results = []
    
    # Ensure root notes directory exists
    config.NOTES_DIR.mkdir(parents=True, exist_ok=True)
    
    files_to_process = get_supported_files()
    logger.info(f"Found {len(files_to_process)} document(s) in {config.NOTES_DIR}")
    
    for file_path in files_to_process:
        filename = file_path.name
        subject = get_subject_for_file(file_path)
        json_path = get_extracted_path(file_path, subject)
        ext = file_path.suffix.lower()
        
        try:
            # If already processed and cached, load details from JSON
            if json_path.exists():
                logger.info(f"Loading already processed document from cache: {filename} ({subject})")
                with open(json_path, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)
                results.append({
                    "filename": filename,
                    "subject": subject,
                    "format": ext[1:].upper(),
                    "total_pages": doc_data.get("total_pages", 0),
                    "status": "cached",
                    "json_path": str(json_path)
                })
                continue
                
            # Perform text extraction based on file extension
            if ext == ".pdf":
                extracted_data = extract_pdf_data(file_path)
            elif ext == ".pptx":
                extracted_data = extract_pptx_data(file_path)
            elif ext == ".docx":
                extracted_data = extract_docx_data(file_path)
            else:
                raise ValueError(f"Unsupported format: {ext}")
                
            # Enrich with metadata
            document_payload = {
                "filename": filename,
                "subject": subject,
                "format": ext[1:].upper(),
                "total_pages": extracted_data["total_pages"],
                "file_size_bytes": file_path.stat().st_size,
                "processed_at": time.time(),
                "pages": extracted_data["pages"]
            }
            
            # Save cached JSON file
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(document_payload, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved extracted text for {filename} to {json_path}")
            
            results.append({
                "filename": filename,
                "subject": subject,
                "format": ext[1:].upper(),
                "total_pages": extracted_data["total_pages"],
                "status": "processed",
                "json_path": str(json_path)
            })
            
        except Exception as e:
            logger.error(f"Failed to process document {filename} ({subject}): {e}")
            results.append({
                "filename": filename,
                "subject": subject,
                "format": ext[1:].upper() if ext else "UNKNOWN",
                "status": "failed",
                "error": str(e)
            })
            
    return results

def get_all_documents() -> List[Dict[str, Any]]:
    """
    Get a list of all documents recursively, along with their subject and ingestion status.
    """
    documents = []
    files = get_supported_files()
    
    for file_path in files:
        filename = file_path.name
        subject = get_subject_for_file(file_path)
        json_path = get_extracted_path(file_path, subject)
        is_processed = json_path.exists()
        ext = file_path.suffix.lower()
        
        doc_info = {
            "filename": filename,
            "subject": subject,
            "format": ext[1:].upper(),
            "file_size_bytes": file_path.stat().st_size,
            "is_processed": is_processed,
            "relative_path": str(file_path.relative_to(config.NOTES_DIR))
        }
        
        if is_processed:
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)
                doc_info["total_pages"] = doc_data.get("total_pages", 0)
                doc_info["processed_at"] = doc_data.get("processed_at", None)
            except Exception:
                pass
                
    return documents

def analyze_documents() -> Dict[str, Any]:
    """
    Analyzes the extracted JSON files and returns dataset statistics:
    - Overall statistics: total documents, total pages, total words, total characters, formats.
    - Subject-level breakdown: documents, pages, words, characters per subject.
    - Document-level breakdown: details for each file.
    """
    analysis = {
        "overall": {
            "total_documents": 0,
            "total_pages": 0,
            "total_words": 0,
            "total_characters": 0,
            "formats": {}
        },
        "by_subject": {},
        "by_document": []
    }
    
    if not config.EXTRACTED_DIR.exists():
        return analysis
        
    # Recursively find all generated JSON files in the extracted directory
    json_files = list(config.EXTRACTED_DIR.glob("**/*.json"))
    
    for json_path in json_files:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                doc_data = json.load(f)
                
            filename = doc_data.get("filename")
            subject = doc_data.get("subject", "General")
            fmt = doc_data.get("format", "UNKNOWN")
            pages = doc_data.get("pages", [])
            total_pages = len(pages)
            
            # Calculate counts
            doc_words = 0
            doc_chars = 0
            for page in pages:
                text = page.get("text", "")
                doc_words += len(text.split())
                doc_chars += len(text)
                
            # Document entry
            doc_entry = {
                "filename": filename,
                "subject": subject,
                "format": fmt,
                "pages": total_pages,
                "words": doc_words,
                "characters": doc_chars
            }
            analysis["by_document"].append(doc_entry)
            
            # Accumulate overall stats
            analysis["overall"]["total_documents"] += 1
            analysis["overall"]["total_pages"] += total_pages
            analysis["overall"]["total_words"] += doc_words
            analysis["overall"]["total_characters"] += doc_chars
            
            # Format count
            analysis["overall"]["formats"][fmt] = analysis["overall"]["formats"].get(fmt, 0) + 1
            
            # Accumulate subject stats
            if subject not in analysis["by_subject"]:
                analysis["by_subject"][subject] = {
                    "document_count": 0,
                    "total_pages": 0,
                    "total_words": 0,
                    "total_characters": 0
                }
            analysis["by_subject"][subject]["document_count"] += 1
            analysis["by_subject"][subject]["total_pages"] += total_pages
            analysis["by_subject"][subject]["total_words"] += doc_words
            analysis["by_subject"][subject]["total_characters"] += doc_chars
            
        except Exception as e:
            logger.error(f"Error analyzing document at {json_path}: {e}")
            
    return analysis

