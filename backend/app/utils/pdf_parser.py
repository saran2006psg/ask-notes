import logging
from pathlib import Path
from pypdf import PdfReader

logger = logging.getLogger(__name__)

def extract_pdf_data(file_path: Path) -> dict:
    """
    Extracts text page-by-page from a PDF file.
    
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
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        pages_data = []
        
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            text = page.extract_text() or ""
            # Clean up whitespace and empty lines
            lines = [line.strip() for line in text.split("\n")]
            cleaned_text = "\n".join([line for line in lines if line])
            
            pages_data.append({
                "page_number": page_num,
                "text": cleaned_text
            })
            
        logger.info(f"Successfully extracted {total_pages} pages from {file_path.name}")
        return {
            "filename": file_path.name,
            "total_pages": total_pages,
            "pages": pages_data
        }
    except Exception as e:
        logger.error(f"Error reading PDF {file_path.name}: {e}")
        raise e
