import json
import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class ImageDescriptionService:
    """
    Uses Gemini Vision (gemini-2.0-flash) to generate concise academic descriptions
    of images extracted from study documents (diagrams, charts, tables, figures).
    Descriptions are cached in a sidecar .desc.json file alongside each image.
    """

    DESCRIPTION_PROMPT = (
        "You are an academic assistant. Describe this image extracted from a study document "
        "in 2-4 sentences. Focus on what the image shows, labels, relationships, and any "
        "key concepts it illustrates. Be precise and educational. "
        "If it is a diagram, describe its structure. "
        "If it is a chart or table, describe the data shown. "
        "Do NOT start with 'This image shows' — be direct and informative."
    )

    def __init__(self):
        self.client = None
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel("gemini-2.0-flash")
                logger.info("ImageDescriptionService: Initialized with Gemini Vision (gemini-2.0-flash).")
            except ImportError:
                logger.warning("ImageDescriptionService: google-generativeai not installed. Image descriptions disabled.")
            except Exception as e:
                logger.error(f"ImageDescriptionService: Failed to initialize Gemini: {e}")
        else:
            logger.warning("ImageDescriptionService: No GEMINI_API_KEY found. Image descriptions disabled.")

    def _cache_path(self, image_path: Path) -> Path:
        """Return the sidecar cache file path for a given image."""
        return image_path.with_suffix(".desc.json")

    def describe_image(self, image_path: Path) -> Optional[str]:
        """
        Generate a textual description of an image using Gemini Vision.
        Returns cached description if available. Returns None on failure.
        """
        if not image_path.exists():
            logger.warning(f"ImageDescriptionService: Image not found: {image_path}")
            return None

        # Check cache first
        cache_path = self._cache_path(image_path)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                return cached.get("description")
            except Exception:
                pass  # Ignore corrupt cache, re-generate

        if self.client is None:
            return None

        try:
            import google.generativeai as genai
            from PIL import Image as PILImage

            img = PILImage.open(image_path)
            response = self.client.generate_content([self.DESCRIPTION_PROMPT, img])
            description = response.text.strip()

            # Cache it
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump({"image_path": str(image_path), "description": description}, f, indent=2)

            logger.info(f"ImageDescriptionService: Described image: {image_path.name}")
            return description

        except Exception as e:
            logger.error(f"ImageDescriptionService: Failed to describe {image_path.name}: {e}")
            return None

    def describe_images(self, image_paths: List[Path]) -> List[Optional[str]]:
        """Describe a batch of images. Returns a list of descriptions (or None for failures)."""
        return [self.describe_image(p) for p in image_paths]
