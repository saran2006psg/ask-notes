# Backend Improvements & Pipeline Optimization

This document lists recommended architectural improvements and pipeline optimizations for the College Notes RAG Backend.

---

## 1. Pipeline Architecture & Organization

Currently, the backend pipeline is structured as:
```
NOTES_DIR (PDF/PPT/DOC) 
   ↓ (document_service.load_documents)
Raw Text JSON Cache (data/extracted/)
   ↓ (document_service.create_chunks)
Semantic Sentence Chunks (data/chunks/)
   ↓ (document_service.generate_embeddings)
Embedding JSONs (data/embedded/ - 384 dims)
   ↓ (vector_store.index_embedded_chunks - Padded to 1024 dims)
Pinecone Database (ask-notes index)
```

### Recommendation: Modular Pipeline Script
To make the data ingestion and indexing process easily runnable end-to-end, we recommend adding a master pipeline script `backend/app/services/pipeline_manager.py` that consolidates all sequential stages:
1. Ingestion (`load_documents()`)
2. Chunking (`create_chunks()`)
3. Embeddings (`generate_embeddings()`)
4. Indexing (`index_embedded_chunks()`)

This allows a single CLI command or REST endpoint to ingest new documents and index them in one click.

---

## 2. Recommended Code & System Improvements

### A. Pinecone Namespace Partitioning (Optimized Phase 12)
* **Current:** All document vectors are upserted into Pinecone's default namespace (`__default__`), and subject filtering is done using a metadata key filter (`filter={"subject": subject}`).
* **Improvement:** Pinecone allows creating distinct **Namespaces** within a single index (e.g., namespace `"DBMS"`, `"OS"`). Querying by namespace isolates vectors entirely and is much faster than metadata key-value queries.
* **Action:** Update `index_embedded_chunks` to upsert vectors into `namespace=subject`, and update `similarity_search` to query using `namespace=subject`.

### B. Asynchronous Task Execution (FastAPI Background Tasks)
* **Current:** Endpoints like `/ingest/process` and `/vectorstore/index` process files synchronously. Large files can cause timeout warnings.
* **Improvement:** Use FastAPI's built-in `BackgroundTasks` to execute indexing asynchronously and return a task ID.
* **Action:** Change the endpoints to trigger processes in the background and return a status checking link.

### C. Standardizing Embedding Dimensions
* **Current:** The local SentenceTransformer model generates 384-dimensional vectors, which are zero-padded to 1024 dimensions to fit the user's pre-configured `ask-notes` index.
* **Improvement:** Avoid zero-padding by standardizing on a model that natively outputs 1024 dimensions (e.g., `BAAI/bge-large-en-v1.5` or similar), or reconstruct the Pinecone index to match 384 dimensions.

### D. Hybrid Search (Dense + Sparse)
* **Current:** Search queries rely solely on semantic dense embeddings. Exact keyword searches (e.g. searching specific formulas or code commands) might miss matches.
* **Improvement:** Combine BM25 sparse retrieval (keyword matching) with dense vector embeddings to perform hybrid search.
