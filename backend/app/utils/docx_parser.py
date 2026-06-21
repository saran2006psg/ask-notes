import logging
from pathlib import Path
import docx

logger = logging.getLogger(__name__)

def extract_docx_data(file_path: Path) -> dict:
    """
    Extracts text from a DOCX file. Since DOCX doesn't have hard physical pages easily
    accessible, we group paragraphs and tables into virtual 'pages' (approx 400 words or split by page breaks).
    
    Returns:
        dict: {
            "filename": str,
            "total_pages": int,
            "pages": [
                {
                    "page_number": int,
                    "text": str
                }
            ]
        }
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    logger.info(f"Starting text extraction for: {file_path.name}")
    
    try:
        doc = docx.Document(file_path)
        pages_data = []
        current_page_text = []
        current_word_count = 0
        page_num = 1
        
        def flush_page():
            nonlocal page_num, current_page_text, current_word_count
            text = "\n".join(current_page_text).strip()
            if text:
                pages_data.append({
                    "page_number": page_num,
                    "text": text
                })
                page_num += 1
            current_page_text = []
            current_word_count = 0

        # Iterate paragraphs and check for page breaks
        for para in doc.paragraphs:
            has_page_break = False
            for run in para.runs:
                # Check for page break element or last rendered page break
                if 'w:br' in run._r.xml and 'type="page"' in run._r.xml:
                    has_page_break = True
                elif 'w:lastRenderedPageBreak' in run._r.xml:
                    has_page_break = True
                    
            para_text = para.text.strip()
            if para_text:
                current_page_text.append(para_text)
                current_word_count += len(para_text.split())
                
            if has_page_break or current_word_count >= 400:
                flush_page()
                
        # Process tables
        for table in doc.tables:
            table_text = []
            for row in table.rows:
                # Deduplicate side-by-side cell texts
                row_cells = []
                for cell in row.cells:
                    cell_val = cell.text.strip()
                    if cell_val and (not row_cells or row_cells[-1] != cell_val):
                        row_cells.append(cell_val)
                if row_cells:
                    table_text.append(" | ".join(row_cells))
            
            if table_text:
                current_page_text.append("[Table]\n" + "\n".join(table_text))
                current_word_count += len("\n".join(table_text).split())
                
            if current_word_count >= 400:
                flush_page()
                
        # Flush remaining content
        flush_page()
        
        # Fallback if doc is empty
        if not pages_data:
            pages_data.append({
                "page_number": 1,
                "text": ""
            })
            
        logger.info(f"Successfully extracted {len(pages_data)} virtual pages from {file_path.name}")
        return {
            "filename": file_path.name,
            "total_pages": len(pages_data),
            "pages": pages_data
        }
    except Exception as e:
        logger.error(f"Error reading DOCX {file_path.name}: {e}")
        raise e
