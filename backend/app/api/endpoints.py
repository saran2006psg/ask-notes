import shutil
import logging
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Query

from app.core import config
from app.services import document_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/documents")
def list_documents():
    """
    Get a list of all supported documents in the notes directory and subdirectories, 
    including their classification and processing status.
    """
    try:
        docs = document_service.get_all_documents()
        return {
            "count": len(docs),
            "documents": docs
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/analysis")
def get_document_analysis():
    """
    Get aggregated dataset analytics (files, pages, words, characters)
    overall, by subject, and per file.
    """
    try:
        return document_service.analyze_documents()
    except Exception as e:
        logger.error(f"Error compiling document analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    subject: Optional[str] = Query(None, description="The subject category folder name, e.g., 'DBMS', 'OS'")
):
    """
    Upload multiple PDF, PPTX, or DOCX files.
    If 'subject' is provided, saves to notes/{subject}/. Otherwise, saves to notes/.
    """
    saved_files = []
    failed_files = []
    
    # Resolve target directory based on subject
    target_dir = config.NOTES_DIR
    if subject:
        # Sanitize subject folder name
        safe_subject = "".join([c for c in subject if c.isalnum() or c in " -_"]).strip()
        if safe_subject:
            target_dir = config.NOTES_DIR / safe_subject
            
    target_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in [".pdf", ".pptx", ".docx"]:
            failed_files.append({
                "filename": file.filename,
                "error": "Unsupported file format. Only PDF, PPTX, and DOCX are allowed."
            })
            continue
            
        target_path = target_dir / file.filename
        try:
            with open(target_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            saved_files.append({
                "filename": file.filename,
                "subject": subject or "Root (Filename Classified)",
                "path": str(target_path.relative_to(config.NOTES_DIR))
            })
            logger.info(f"Successfully uploaded: {file.filename} to {target_dir}")
        except Exception as e:
            logger.error(f"Failed to save upload {file.filename}: {e}")
            failed_files.append({
                "filename": file.filename,
                "error": str(e)
            })
            
    return {
        "uploaded": saved_files,
        "failed": failed_files,
        "total_uploaded": len(saved_files)
    }

@router.post("/ingest/process")
def process_documents():
    """
    Trigger ingestion (extract text and metadata from files in notes/ folder recursively).
    """
    try:
        results = document_service.load_documents()
        processed_count = sum(1 for r in results if r["status"] == "processed")
        cached_count = sum(1 for r in results if r["status"] == "cached")
        failed_count = sum(1 for r in results if r["status"] == "failed")
        
        return {
            "message": "Ingestion scan completed.",
            "statistics": {
                "total_scanned": len(results),
                "processed_new": processed_count,
                "loaded_cached": cached_count,
                "failed": failed_count
            },
            "details": results
        }
    except Exception as e:
        logger.error(f"Error processing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/chunk")
def chunk_documents():
    """
    Trigger semantic chunking across all ingested documents.
    """
    try:
        results = document_service.create_chunks()
        success_count = sum(1 for r in results if r["status"] == "chunked")
        failed_count = sum(1 for r in results if r["status"] == "failed")
        
        return {
            "message": "Semantic chunking completed.",
            "statistics": {
                "total_documents": len(results),
                "successfully_chunked": success_count,
                "failed": failed_count
            },
            "details": results
        }
    except Exception as e:
        logger.error(f"Error chunking documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/chunks")
def get_chunk_stats():
    """
    Get statistics about generated document chunks.
    """
    try:
        return document_service.get_chunk_statistics()
    except Exception as e:
        logger.error(f"Error fetching chunk statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

