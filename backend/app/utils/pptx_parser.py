import logging
from pathlib import Path
from pptx import Presentation

logger = logging.getLogger(__name__)

def extract_pptx_data(file_path: Path) -> dict:
    """
    Extracts text slide-by-slide from a PPTX file.
    
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
        
    logger.info(f"Starting slide text extraction for: {file_path.name}")
    
    try:
        prs = Presentation(file_path)
        total_slides = len(prs.slides)
        pages_data = []
        
        for idx, slide in enumerate(prs.slides):
            slide_num = idx + 1
            slide_text_runs = []
            
            # Extract text from shapes
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text_runs.append(shape.text.strip())
            
            # Extract text from notes if any
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes_text = slide.notes_slide.notes_text_frame.text.strip()
                if notes_text:
                    slide_text_runs.append(f"[Presenter Notes]\n{notes_text}")
                    
            # Clean up whitespace and empty lines
            lines = [line.strip() for line in "\n".join(slide_text_runs).split("\n")]
            cleaned_text = "\n".join([line for line in lines if line])
            
            pages_data.append({
                "page_number": slide_num,
                "text": cleaned_text
            })
            
        logger.info(f"Successfully extracted {total_slides} slides from {file_path.name}")
        return {
            "filename": file_path.name,
            "total_pages": total_slides,
            "pages": pages_data
        }
    except Exception as e:
        logger.error(f"Error reading PPTX {file_path.name}: {e}")
        raise e
