import re
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

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

def get_subject_for_file(file_path: Path, user_id: Optional[str] = None) -> str:
    """
    Determine the subject: if in a subfolder under notes/{user_id}/, use subfolder name.
    If in the root notes/{user_id}/ folder, fallback to classify_subject(filename).
    """
    resolved_file = file_path.resolve()
    resolved_notes = (config.NOTES_DIR / user_id if user_id else config.NOTES_DIR).resolve()
    
    # If the file is directly in the notes root
    if resolved_file.parent == resolved_notes:
        return classify_subject(file_path.name)
        
    try:
        relative_path = resolved_file.relative_to(resolved_notes)
        return relative_path.parts[0]
    except Exception:
        return classify_subject(file_path.name)

def get_images_dir_for_file(file_path: Path, subject: str, user_id: Optional[str] = None) -> Path:
    """
    Get the directory where extracted images for a specific document are stored.
    Structure: data/images/{user_id}/{subject}/{filename_stem}/
    """
    stem = file_path.stem
    if user_id:
        images_dir = config.IMAGES_DIR / user_id / subject / stem
    else:
        images_dir = config.IMAGES_DIR / subject / stem
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir


def get_extracted_path(file_path: Path, subject: str, user_id: Optional[str] = None) -> Path:
    """
    Get the path where the extracted JSON file should be saved.
    Replicates directory structure under data/extracted/{user_id}/{subject}/{filename}.json
    """
    json_filename = file_path.with_suffix(".json").name
    if user_id:
        subject_dir = config.EXTRACTED_DIR / user_id / subject
    else:
        subject_dir = config.EXTRACTED_DIR / subject
    subject_dir.mkdir(parents=True, exist_ok=True)
    return subject_dir / json_filename

def get_supported_files(user_id: Optional[str] = None) -> List[Path]:
    """
    Find all PDF, PPTX, and DOCX files in NOTES_DIR/{user_id} and its subdirectories.
    """
    target_dir = config.NOTES_DIR / user_id if user_id else config.NOTES_DIR
    if not target_dir.exists():
        return []
    
    all_files = []
    # Recursively list files and filter by supported extensions
    for p in target_dir.glob("**/*"):
        if p.is_file() and p.suffix.lower() in [".pdf", ".pptx", ".docx"]:
            # If user_id is NOT provided (i.e. global scan), we want to EXCLUDE
            # any subdirectories that belong to individual users
            if not user_id:
                try:
                    rel = p.relative_to(config.NOTES_DIR)
                    if rel.parts and rel.parts[0].startswith("user_"):
                        continue
                except Exception:
                    pass
            all_files.append(p)
            
    return all_files

def load_documents(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Recursively scan NOTES_DIR/{user_id}, extract text using appropriate parser,
    save cached JSON by subject, and return list of results.
    """
    results = []
    
    target_notes_dir = config.NOTES_DIR / user_id if user_id else config.NOTES_DIR
    target_notes_dir.mkdir(parents=True, exist_ok=True)
    
    files_to_process = get_supported_files(user_id)
    logger.info(f"Found {len(files_to_process)} document(s) in {target_notes_dir}")
    
    for file_path in files_to_process:
        filename = file_path.name
        subject = get_subject_for_file(file_path, user_id)
        json_path = get_extracted_path(file_path, subject, user_id)
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
                
            # Perform text + image extraction based on file extension
            images_dir = get_images_dir_for_file(file_path, subject, user_id)
            if ext == ".pdf":
                extracted_data = extract_pdf_data(file_path, images_dir=images_dir)
            elif ext == ".pptx":
                extracted_data = extract_pptx_data(file_path, images_dir=images_dir)
            elif ext == ".docx":
                extracted_data = extract_docx_data(file_path, images_dir=images_dir)
            else:
                raise ValueError(f"Unsupported format: {ext}")

            # Describe extracted images with Gemini Vision
            try:
                from app.services.image_description_service import ImageDescriptionService
                img_describer = ImageDescriptionService()
                for page in extracted_data["pages"]:
                    for img_info in page.get("images", []):
                        img_path = Path(img_info["path"])
                        description = img_describer.describe_image(img_path)
                        img_info["description"] = description or ""
            except Exception as e:
                logger.warning(f"Image description step failed for {filename}: {e}")
                
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

def get_all_documents(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get a list of all documents recursively, along with their subject and ingestion status.
    """
    documents = []
    files = get_supported_files(user_id)
    
    for file_path in files:
        filename = file_path.name
        subject = get_subject_for_file(file_path, user_id)
        json_path = get_extracted_path(file_path, subject, user_id)
        is_processed = json_path.exists()
        ext = file_path.suffix.lower()
        
        doc_info = {
            "filename": filename,
            "subject": subject,
            "format": ext[1:].upper(),
            "file_size_bytes": file_path.stat().st_size,
            "is_processed": is_processed,
            "relative_path": str(file_path.relative_to(config.NOTES_DIR / user_id if user_id else config.NOTES_DIR))
        }
        
        if is_processed:
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)
                doc_info["total_pages"] = doc_data.get("total_pages", 0)
                doc_info["processed_at"] = doc_data.get("processed_at", None)
            except Exception:
                pass
        
        documents.append(doc_info)
                
    return documents

def analyze_documents(user_id: Optional[str] = None) -> Dict[str, Any]:
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
    
    extracted_target = config.EXTRACTED_DIR / user_id if user_id else config.EXTRACTED_DIR
    if not extracted_target.exists():
        return analysis
        
    # Recursively find all generated JSON files in the extracted directory
    json_files = []
    for p in extracted_target.glob("**/*.json"):
        if not user_id:
            try:
                rel = p.relative_to(config.EXTRACTED_DIR)
                if rel.parts and rel.parts[0].startswith("user_"):
                    continue
            except Exception:
                pass
        json_files.append(p)
    
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

# Path for chunks storage
CHUNKS_DIR = config.DATA_DIR / "chunks"

def create_chunks(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load extracted JSON documents, run the SemanticChunker on each page,
    attach metadata, save chunks to data/chunks/{user_id}/{subject}/, and return results.
    """
    from app.utils.semantic_chunker import SemanticChunker
    
    results = []
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    
    extracted_target = config.EXTRACTED_DIR / user_id if user_id else config.EXTRACTED_DIR
    if not extracted_target.exists():
        logger.warning("Extracted documents directory does not exist.")
        return results
        
    # Recursively find all JSON extracted files
    json_files = []
    for p in extracted_target.glob("**/*.json"):
        if not user_id:
            try:
                rel = p.relative_to(config.EXTRACTED_DIR)
                if rel.parts and rel.parts[0].startswith("user_"):
                    continue
            except Exception:
                pass
        json_files.append(p)
        
    logger.info(f"Found {len(json_files)} extracted document JSON(s) to chunk.")
    
    chunker = SemanticChunker()
    
    for json_path in json_files:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                doc_data = json.load(f)
                
            filename = doc_data.get("filename")
            subject = doc_data.get("subject", "General")
            fmt = doc_data.get("format", "UNKNOWN")
            pages = doc_data.get("pages", [])
            
            doc_chunks = []
            chunk_idx = 0
            
            # Clean filename for IDs (remove spaces and special chars)
            clean_filename_id = Path(filename).stem.replace(" ", "_")
            clean_filename_id = re.sub(r'[^\w\-]', '', clean_filename_id)
            
            for page in pages:
                page_num = page.get("page_number", 1)
                text = page.get("text", "").strip()
                # Collect image info from this page
                page_images = page.get("images", [])
                page_image_paths = [img["path"] for img in page_images if img.get("path")]
                page_image_descriptions = [img.get("description", "") for img in page_images if img.get("path")]

                if not text:
                    continue

                # Split text semantically
                page_chunks = chunker.chunk_text(text)

                for chunk_text in page_chunks:
                    # Formulate chunk ID prefix including user_id
                    uid_prefix = f"{user_id}_" if user_id else ""
                    chunk_id = f"{uid_prefix}{subject}_{clean_filename_id}_chunk_{chunk_idx}"
                    chunk_id = re.sub(r'[^\w\-]', '', chunk_id)

                    doc_chunks.append({
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                        "metadata": {
                            "filename": filename,
                            "subject": subject,
                            "format": fmt,
                            "page": page_num,
                            "source": f"{subject} Notes - Page {page_num}",
                            "image_paths": page_image_paths,
                            "image_descriptions": page_image_descriptions
                        }
                    })
                    chunk_idx += 1
            
            # Output payload
            chunk_payload = {
                "filename": filename,
                "subject": subject,
                "format": fmt,
                "total_chunks": len(doc_chunks),
                "chunks": doc_chunks
            }
            
            # Save file in data/chunks/{user_id}/{subject}/
            if user_id:
                dest_dir = CHUNKS_DIR / user_id / subject
            else:
                dest_dir = CHUNKS_DIR / subject
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / f"{Path(filename).stem}_chunks.json"
            
            with open(dest_path, "w", encoding="utf-8") as f:
                json.dump(chunk_payload, f, indent=2, ensure_ascii=False)
                
            results.append({
                "filename": filename,
                "subject": subject,
                "total_chunks": len(doc_chunks),
                "status": "chunked",
                "dest_path": str(dest_path)
            })
            logger.info(f"Successfully chunked {filename} into {len(doc_chunks)} chunks.")
            
        except Exception as e:
            logger.error(f"Failed to chunk document {json_path.name}: {e}")
            results.append({
                "filename": json_path.name,
                "status": "failed",
                "error": str(e)
            })
            
    return results

def get_chunk_statistics(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Gives overall statistics about generated chunks.
    """
    stats = {
        "total_documents": 0,
        "total_chunks": 0,
        "average_chunks_per_doc": 0.0,
        "by_subject": {}
    }
    
    chunks_target = CHUNKS_DIR / user_id if user_id else CHUNKS_DIR
    if not chunks_target.exists():
        return stats
        
    chunk_files = []
    for p in chunks_target.glob("**/*_chunks.json"):
        if not user_id:
            try:
                rel = p.relative_to(CHUNKS_DIR)
                if rel.parts and rel.parts[0].startswith("user_"):
                    continue
            except Exception:
                pass
        chunk_files.append(p)
        
    stats["total_documents"] = len(chunk_files)
    
    for f in chunk_files:
        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
            count = data.get("total_chunks", 0)
            subject = data.get("subject", "General")
            
            stats["total_chunks"] += count
            stats["by_subject"][subject] = stats["by_subject"].get(subject, 0) + count
        except Exception:
            pass
            
    if stats["total_documents"] > 0:
        stats["average_chunks_per_doc"] = round(stats["total_chunks"] / stats["total_documents"], 2)
        
    return stats

# Path for embedded storage
EMBEDDED_DIR = config.DATA_DIR / "embedded"

def generate_embeddings(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load chunk JSON files, pass text to EmbeddingService,
    save embedded chunks in data/embedded/{user_id}/{subject}/, and return results.
    """
    from app.services.embedding_service import EmbeddingService
    
    results = []
    EMBEDDED_DIR.mkdir(parents=True, exist_ok=True)
    
    chunks_target = CHUNKS_DIR / user_id if user_id else CHUNKS_DIR
    if not chunks_target.exists():
        logger.warning("Chunks directory does not exist. Please chunk files first.")
        return results
        
    chunk_files = []
    for p in chunks_target.glob("**/*_chunks.json"):
        if not user_id:
            try:
                rel = p.relative_to(CHUNKS_DIR)
                if rel.parts and rel.parts[0].startswith("user_"):
                    continue
            except Exception:
                pass
        chunk_files.append(p)
        
    logger.info(f"Found {len(chunk_files)} chunk files to embed.")
    
    embedder = EmbeddingService()
    
    for f_path in chunk_files:
        try:
            with open(f_path, "r", encoding="utf-8") as f:
                chunk_data = json.load(f)
                
            filename = chunk_data.get("filename")
            subject = chunk_data.get("subject", "General")
            fmt = chunk_data.get("format", "UNKNOWN")
            chunks = chunk_data.get("chunks", [])
            
            if not chunks:
                results.append({
                    "filename": filename,
                    "subject": subject,
                    "status": "skipped",
                    "reason": "No chunks found in document."
                })
                continue
                
            # Extract texts
            texts = [c["text"] for c in chunks]
            
            # Batch embedding call
            vectors = embedder.embed_texts(texts)
            
            # Inject vectors
            embedded_chunks = []
            for idx, chunk in enumerate(chunks):
                chunk["embedding"] = vectors[idx]
                embedded_chunks.append(chunk)
                
            embedded_payload = {
                "filename": filename,
                "subject": subject,
                "format": fmt,
                "provider": embedder.provider,
                "dimension": embedder.dimension,
                "total_chunks": len(embedded_chunks),
                "chunks": embedded_chunks
            }
            
            # Save file in data/embedded/{user_id}/{subject}/
            if user_id:
                dest_dir = EMBEDDED_DIR / user_id / subject
            else:
                dest_dir = EMBEDDED_DIR / subject
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / f"{Path(filename).stem}_embedded.json"
            
            with open(dest_path, "w", encoding="utf-8") as f:
                json.dump(embedded_payload, f, indent=2, ensure_ascii=False)
                
            results.append({
                "filename": filename,
                "subject": subject,
                "total_chunks": len(embedded_chunks),
                "provider": embedder.provider,
                "dimension": embedder.dimension,
                "status": "embedded",
                "dest_path": str(dest_path)
            })
            logger.info(f"Successfully embedded {filename} | {len(embedded_chunks)} chunks using {embedder.provider}")
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings for {f_path.name}: {e}")
            results.append({
                "filename": f_path.name,
                "status": "failed",
                "error": str(e)
            })
            
    return results

def get_embedding_statistics(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns statistics about the generated embeddings.
    """
    stats = {
        "total_embedded_documents": 0,
        "total_embedded_chunks": 0,
        "providers_used": {},
        "by_subject": {}
    }
    
    embedded_target = EMBEDDED_DIR / user_id if user_id else EMBEDDED_DIR
    if not embedded_target.exists():
        return stats
        
    embedded_files = []
    for p in embedded_target.glob("**/*_embedded.json"):
        if not user_id:
            try:
                rel = p.relative_to(EMBEDDED_DIR)
                if rel.parts and rel.parts[0].startswith("user_"):
                    continue
            except Exception:
                pass
        embedded_files.append(p)
        
    stats["total_embedded_documents"] = len(embedded_files)
    
    for f in embedded_files:
        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
            count = data.get("total_chunks", 0)
            subject = data.get("subject", "General")
            provider = data.get("provider", "UNKNOWN")
            
            stats["total_embedded_chunks"] += count
            stats["providers_used"][provider] = stats["providers_used"].get(provider, 0) + 1
            stats["by_subject"][subject] = stats["by_subject"].get(subject, 0) + count
        except Exception:
            pass
            
    return stats
