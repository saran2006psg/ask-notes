import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def _try_paddle_ocr(image_bytes: bytes) -> str:
    """
    Run PaddleOCR on a raw image bytes object. Returns extracted text or empty string.
    PaddleOCR is optional — only used when installed and needed (scanned pages).
    """
    try:
        import tempfile
        from PIL import Image
        import io
        from paddleocr import PaddleOCR

        ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img = Image.open(io.BytesIO(image_bytes))
            img.save(tmp.name)
            tmp_path = tmp.name

        result = ocr.ocr(tmp_path, cls=True)
        Path(tmp_path).unlink(missing_ok=True)

        lines = []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    text_info = line[1]
                    if text_info and text_info[0]:
                        lines.append(text_info[0])
        return "\n".join(lines)
    except ImportError:
        return ""
    except Exception as e:
        logger.warning(f"PaddleOCR failed: {e}")
        return ""


def _save_page_images(page, page_num: int, images_dir: Path) -> List[Dict[str, str]]:
    """
    Extract and save all images from a PDF page.
    Returns list of dicts with 'path' and 'filename' for each saved image.
    """
    saved_images = []
    images_dir.mkdir(parents=True, exist_ok=True)

    try:
        for img_idx, image_obj in enumerate(page.images):
            try:
                image_data = image_obj.get("data") or image_obj.get("raw", b"")
                if not image_data or len(image_data) < 500:
                    continue  # Skip tiny/corrupt images

                # Determine extension
                image_ext = image_obj.get("ext", "png").lower()
                if image_ext not in ("png", "jpg", "jpeg"):
                    image_ext = "png"

                # Try converting to PNG via Pillow for consistency
                try:
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(image_data))
                    # Convert to RGB if needed (e.g., CMYK)
                    if img.mode not in ("RGB", "RGBA", "L"):
                        img = img.convert("RGB")
                    image_ext = "png"
                    out_buf = io.BytesIO()
                    img.save(out_buf, format="PNG")
                    image_data = out_buf.getvalue()
                except Exception:
                    pass  # Keep raw bytes if Pillow fails

                img_filename = f"page_{page_num}_img_{img_idx + 1}.{image_ext}"
                img_path = images_dir / img_filename

                with open(img_path, "wb") as f:
                    f.write(image_data)

                saved_images.append({
                    "path": str(img_path),
                    "filename": img_filename,
                    "page": page_num
                })
                logger.debug(f"Saved PDF image: {img_filename}")

            except Exception as e:
                logger.warning(f"Failed to save image {img_idx} on page {page_num}: {e}")

    except Exception as e:
        logger.warning(f"Failed to iterate images on page {page_num}: {e}")

    return saved_images


def extract_pdf_data(file_path: Path, images_dir: Optional[Path] = None) -> dict:
    """
    Extracts text page-by-page from a PDF file.
    Falls back to PaddleOCR for pages with no selectable text (scanned).
    Optionally extracts embedded images if images_dir is provided.

    Returns:
        dict: {
            "filename": str,
            "total_pages": int,
            "pages": [
                {
                    "page_number": int,
                    "text": str,
                    "images": [{"path": str, "filename": str}]  # if images extracted
                }
            ]
        }
    """
    from pypdf import PdfReader

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

            # PaddleOCR fallback: if PyPDF returned no text, try OCR on rendered page
            if not text.strip():
                logger.info(f"Page {page_num} has no selectable text — attempting PaddleOCR.")
                try:
                    # Use pdf2image to render the page if available
                    from pdf2image import convert_from_path
                    images_pil = convert_from_path(
                        str(file_path), first_page=page_num, last_page=page_num, dpi=200
                    )
                    if images_pil:
                        import io
                        buf = io.BytesIO()
                        images_pil[0].save(buf, format="PNG")
                        text = _try_paddle_ocr(buf.getvalue())
                        if text:
                            logger.info(f"PaddleOCR extracted {len(text)} chars from page {page_num}.")
                except ImportError:
                    logger.debug("pdf2image not installed; cannot OCR this page.")
                except Exception as e:
                    logger.warning(f"PaddleOCR rendering failed for page {page_num}: {e}")

            # Clean up whitespace and empty lines
            lines = [line.strip() for line in text.split("\n")]
            cleaned_text = "\n".join([line for line in lines if line])

            page_data: Dict[str, Any] = {
                "page_number": page_num,
                "text": cleaned_text,
                "images": []
            }

            # Extract embedded images if images_dir is provided
            if images_dir:
                page_images_dir = images_dir
                saved = _save_page_images(page, page_num, page_images_dir)
                page_data["images"] = saved

            pages_data.append(page_data)

        logger.info(f"Successfully extracted {total_pages} pages from {file_path.name}")
        return {
            "filename": file_path.name,
            "total_pages": total_pages,
            "pages": pages_data
        }
    except Exception as e:
        logger.error(f"Error reading PDF {file_path.name}: {e}")
        raise e
