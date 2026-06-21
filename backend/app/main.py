import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router as api_router

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="College Notes Assistant API",
    description="Backend API for RAG-based College Notes Assistant (DBMS, OS, CN, OOP)",
    version="1.0.0"
)

# Enable CORS for frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints router
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to the College Notes Assistant API. Use /docs for API documentation.",
        "supported_subjects": ["DBMS", "Operating Systems", "Computer Networks", "OOP"]
    }
