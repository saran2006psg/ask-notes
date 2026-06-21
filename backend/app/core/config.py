import os
from pathlib import Path

# Base project directory (workspace root)
# Since config.py is at backend/app/core/config.py, the base directory is 3 levels up
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Notes directory where PDFs are placed
NOTES_DIR = BASE_DIR / "notes"

# Data output directory where extracted JSON text is stored
DATA_DIR = BASE_DIR / "data"
EXTRACTED_DIR = DATA_DIR / "extracted"

# Ensure directories exist
NOTES_DIR.mkdir(parents=True, exist_ok=True)
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

print(f"[Config] Project BASE_DIR: {BASE_DIR}")
print(f"[Config] NOTES_DIR: {NOTES_DIR}")
print(f"[Config] EXTRACTED_DIR: {EXTRACTED_DIR}")
