import time
import shutil
import logging
import re
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
import requests

from app.core import config
from app.services import document_service
from app.services.vector_store import VectorStoreService
from app.services.retrieval_service import RetrievalService
from app.services.prompt_service import PromptService
from app.services.llm_service import LLMService
from app.services.citation_service import CitationService
from app.services.pipeline_manager import PipelineManager

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

def verify_clerk_token() -> str:
    """
    Bypasses Clerk signature verification and returns an empty string,
    enabling single-user local mode accessing the root notes/ directory.
    """
    return ""


@router.get("/documents")
def list_documents(user_id: str = Depends(verify_clerk_token)):
    """
    Get a list of all supported documents in the notes directory and subdirectories, 
    including their classification and processing status.
    """
    try:
        docs = document_service.get_all_documents(user_id=user_id)
        return {
            "count": len(docs),
            "documents": docs
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/analysis")
def get_document_analysis(user_id: str = Depends(verify_clerk_token)):
    """
    Get aggregated dataset analytics (files, pages, words, characters)
    overall, by subject, and per file.
    """
    try:
        return document_service.analyze_documents(user_id=user_id)
    except Exception as e:
        logger.error(f"Error compiling document analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    subject: Optional[str] = Query(None, description="The subject category folder name, e.g., 'DBMS', 'OS'"),
    user_id: str = Depends(verify_clerk_token)
):
    """
    Upload multiple PDF, PPTX, or DOCX files.
    Saves to notes/{user_id}/{subject}/.
    """
    saved_files = []
    failed_files = []
    
    # Resolve target directory based on user_id and subject
    target_dir = config.NOTES_DIR / user_id
    if subject:
        # Sanitize subject folder name
        safe_subject = "".join([c for c in subject if c.isalnum() or c in " -_"]).strip()
        if safe_subject:
            target_dir = target_dir / safe_subject
            
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
                "path": str(target_path.relative_to(config.NOTES_DIR / user_id))
            })
            logger.info(f"Successfully uploaded: {file.filename} to {target_dir} for user {user_id}")
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
def process_documents(user_id: str = Depends(verify_clerk_token)):
    """
    Trigger ingestion (extract text and metadata from files in notes/folder recursively).
    """
    try:
        results = document_service.load_documents(user_id=user_id)
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
def chunk_documents(user_id: str = Depends(verify_clerk_token)):
    """
    Trigger semantic chunking across all ingested documents.
    """
    try:
        results = document_service.create_chunks(user_id=user_id)
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
def get_chunk_stats(user_id: str = Depends(verify_clerk_token)):
    """
    Get statistics about generated document chunks.
    """
    try:
        return document_service.get_chunk_statistics(user_id=user_id)
    except Exception as e:
        logger.error(f"Error fetching chunk statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/embed")
def embed_documents(user_id: str = Depends(verify_clerk_token)):
    """
    Trigger vector embedding generation for all chunked documents.
    """
    try:
        results = document_service.generate_embeddings(user_id=user_id)
        success_count = sum(1 for r in results if r["status"] == "embedded")
        failed_count = sum(1 for r in results if r["status"] == "failed")
        
        return {
            "message": "Vector embedding generation completed.",
            "statistics": {
                "total_documents": len(results),
                "successfully_embedded": success_count,
                "failed": failed_count
            },
            "details": results
        }
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/embeddings")
def get_embedding_stats(user_id: str = Depends(verify_clerk_token)):
    """
    Get statistics about generated vector embeddings.
    """
    try:
        return document_service.get_embedding_statistics(user_id=user_id)
    except Exception as e:
        logger.error(f"Error fetching embedding statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vectorstore/index")
def index_vectorstore(user_id: str = Depends(verify_clerk_token)):
    """
    Trigger indexing of all cached vector embeddings into Pinecone.
    """
    try:
        vs = VectorStoreService()
        stats = vs.index_embedded_chunks(user_id=user_id)
        return {
            "message": "Pinecone indexing complete.",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error indexing vectors in Pinecone: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vectorstore/stats")
def get_vectorstore_stats(user_id: str = Depends(verify_clerk_token)):
    """
    Get statistics about the indexed collection inside Pinecone.
    """
    try:
        vs = VectorStoreService()
        stats = vs.get_stats()
        
        # Override total_chunks count with user-specific embedded chunks count
        embed_stats = document_service.get_embedding_statistics(user_id=user_id)
        stats["total_chunks"] = embed_stats.get("total_embedded_chunks", 0)
        return stats
    except Exception as e:
        logger.error(f"Error fetching Pinecone statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/retrieve")
def retrieve_context(
    query: str = Query(..., description="The query string to search for"),
    subject: Optional[str] = Query(None, description="Optional subject to filter by, e.g., 'DBMS', 'OS'"),
    top_k: int = Query(5, description="Number of results to retrieve"),
    rerank: bool = Query(True, description="Whether to apply BGE cross-encoder reranking"),
    user_id: str = Depends(verify_clerk_token)
):
    """
    Retrieve matching context chunks for a query from Pinecone, with optional subject filtering and BGE reranking.
    """
    try:
        retriever = RetrievalService()
        result = retriever.retrieve_context(query=query, subject=subject, top_k=top_k, rerank=rerank, user_id=user_id)
        return {
            "query": query,
            "subject": subject,
            "top_k": top_k,
            "rerank": rerank,
            "results": result["chunks"],
            "images": result["images"]
        }
    except Exception as e:
        logger.error(f"Error during context retrieval: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class PromptBuildRequest(BaseModel):
    query: str
    subject: Optional[str] = None
    top_k: int = 5
    rerank: bool = True

@router.post("/prompt/build")
def build_prompt_endpoint(request: PromptBuildRequest, user_id: str = Depends(verify_clerk_token)):
    """
    Retrieve matching context chunks and assemble a grounded prompt.
    """
    try:
        retriever = RetrievalService()
        prompter = PromptService()

        # 1. Retrieve context
        result = retriever.retrieve_context(
            query=request.query,
            subject=request.subject,
            top_k=request.top_k,
            rerank=request.rerank,
            user_id=user_id
        )
        chunks = result["chunks"]

        # 2. Build grounded prompt
        prompt = prompter.build_prompt(query=request.query, chunks=chunks)

        return {
            "query": request.query,
            "subject": request.subject,
            "prompt": prompt
        }
    except Exception as e:
        logger.error(f"Error building prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    query: str
    subject: Optional[str] = None
    top_k: int = 5
    rerank: bool = True

@router.post("/chat")
def chat_endpoint(request: ChatRequest, user_id: str = Depends(verify_clerk_token)):
    """
    Run full RAG pipeline: retrieve context, build grounded prompt,
    generate answer using Groq LLM, and verify citations.
    """
    try:
        retriever = RetrievalService()
        prompter = PromptService()
        llm = LLMService()
        cit_engine = CitationService()

        # 1. Retrieve context (returns {chunks, images})
        retrieval_result = retriever.retrieve_context(
            query=request.query,
            subject=request.subject,
            top_k=request.top_k,
            rerank=request.rerank,
            user_id=user_id
        )
        chunks = retrieval_result["chunks"]
        images = retrieval_result["images"]

        # 2. Build grounded prompt
        prompt = prompter.build_prompt(query=request.query, chunks=chunks)

        # 3. Generate LLM answer
        answer = llm.generate_answer(prompt=prompt)

        # 4. Extract and verify citations actually cited in response
        verified_citations = cit_engine.citation_engine(answer=answer, retrieved_chunks=chunks)

        # Strip parenthetical inline citations from the final answer text returned to the user
        clean_answer = re.sub(r"\s*\(Source:\s*.*?\)", "", answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r" +", " ", clean_answer)
        clean_answer = re.sub(r"\s+\.", ".", clean_answer)
        clean_answer = re.sub(r"\s+,", ",", clean_answer)
        clean_answer = clean_answer.strip()

        # Format retrieved citations
        retrieved_citations = []
        for idx, chunk in enumerate(chunks):
            meta = chunk.get("metadata", {})
            retrieved_citations.append({
                "index": idx + 1,
                "chunk_id": chunk.get("chunk_id"),
                "score": chunk.get("score"),
                "filename": meta.get("filename"),
                "subject": meta.get("subject"),
                "page": meta.get("page"),
                "source": meta.get("source"),
                "text": chunk.get("text", "")
            })

        return {
            "query": request.query,
            "subject": request.subject,
            "answer": clean_answer,
            "verified_citations": verified_citations,
            "retrieved_citations": retrieved_citations,
            "images": images  # [{url, description, path}]
        }
    except Exception as e:
        logger.error(f"Error in RAG chat pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pipeline/run")
def run_indexing_pipeline(user_id: str = Depends(verify_clerk_token)):
    """
    Trigger the end-to-end RAG indexing pipeline: ingest documents,
    create chunks, generate embeddings, and upsert them to Pinecone.
    """
    try:
        results = PipelineManager.run_full_indexing_pipeline(user_id=user_id)
        if results.get("status") == "failed":
            raise HTTPException(status_code=500, detail=results.get("error"))
        return results
    except Exception as e:
        logger.error(f"Error running pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{file_path:path}")
def serve_image(file_path: str):
    """
    Serve an extracted document image from data/images/ directory.
    e.g. GET /api/images/data_privacy_and_security/MyDoc/slide_1_img_1.png
    """
    full_path = config.IMAGES_DIR / file_path
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail=f"Image not found: {file_path}")
    # Basic safety check: prevent path traversal outside IMAGES_DIR
    try:
        full_path.resolve().relative_to(config.IMAGES_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied.")
    return FileResponse(str(full_path))


# Triggering reload - multimodal image support added
