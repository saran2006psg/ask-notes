# 🎓 College Notes Assistant (RAG-Based)

Welcome to the **College Notes Assistant**, a Retrieval-Augmented Generation (RAG) powered search and QA assistant. This system enables students to query multiple academic notes across subjects (such as DBMS, Operating Systems, Computer Networks, and OOP) and receive accurate, source-aware answers.

---

## 🏗️ System Architecture

Below is the RAG pipeline architecture diagram showing the document ingestion, semantic chunking, and vector search retrieval flow:

![Architecture Diagram](Architecture.svg)

---

## 🚀 Key Features

* 📁 **Folder-Based Subject Classification:** Organize files into subdirectories under `notes/` (e.g., `notes/Operating Systems/`) and they will be automatically classified by subject.
* 📄 **Multi-Format Processing:** Supports text extraction from **PDFs**, **PowerPoint Slide Decks (PPTX)**, and **Word Documents (DOCX)**.
* ⚡ **High-Speed Ingestion & Cache:** Text is extracted page-by-page (or slide-by-slide) and stored in a structured JSON database cache (`data/extracted/`) to skip slow re-parsing.
* 📊 **Dataset Metrics Dashboard:** Run analysis to view total files, pages, words, and characters overall, by subject, and per file.
* 🧠 **Sentence-Level Semantic Chunking:** Groups text dynamically based on sentence-to-sentence TF-IDF cosine similarity, preserving context integrity.
* 🏷️ **Metadata Injection:** Automatically tags each chunk with the filename, subject, format, page number, and source citation (`Subject Notes - Page X`) for accurate referencing.

---

## 🛠️ Installation & Setup

Ensure you have Python 3.10+ installed.

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Run Parser Ingestion Test (Phase 1)
Scan the `notes/` directory recursively to extract and cache text page-by-page:
```bash
python test_ingest.py
```
This produces structured `.json` documents inside the `data/extracted/` folder.

### 3. Run Document Analysis (Phase 2)
Calculate stats (pages, words, characters) overall, by subject subfolder, and per file:
```bash
python test_analysis.py
```

### 4. Run Semantic Chunking (Phase 3)
Divide the page texts into semantic chunks and inject metadata tags:
```bash
python test_chunking.py
```
This saves chunks to `data/chunks/{subject}/` as structured JSON.

### 5. Start the Backend API Server
```bash
python backend/run.py
```
The server will run on `http://127.0.0.1:8000`. You can visit:
- **Interactive Swagger Docs:** http://127.0.0.1:8000/docs
- **Documents list:** http://127.0.0.1:8000/api/documents
- **Analytics endpoint:** http://127.0.0.1:8000/api/documents/analysis
- **Chunking stats:** http://127.0.0.1:8000/api/documents/chunks
