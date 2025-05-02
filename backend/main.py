import sys
from loguru import logger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

from app.database.database import engine
from app.models.models import Base
from app.api.routes import router as challenge_router

# --- Loguru Configuration ---
# Remove default handlers to avoid duplicate logs with Uvicorn's default loggers
logger.remove()

# Add a sink for console output
logger.add(
    sys.stderr,
    level="INFO",  # Log INFO level and above to console
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Add a sink for file output
log_file_path = os.path.join(os.path.dirname(__file__), "logs", "backend.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True) # Ensure logs directory exists
logger.add(
    log_file_path,
    level="DEBUG",  # Log DEBUG level and above to file
    rotation="10 MB",  # Rotate the log file when it reaches 10 MB
    retention="7 days",  # Keep logs for 7 days
    compression="zip",  # Compress rotated files
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)
logger.info("Logger initialized. Logging to console (INFO) and file (DEBUG).")
# --- End Loguru Configuration ---

# Initialize app
app = FastAPI(title="AI Kids Challenge Game API")

# Load environment variables
load_dotenv()

# Configure CORS
origins = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",
    "http://192.168.1.182:3000",  # Allow the specific IP
    "http://192.168.1.*:3000",    # Allow all devices on the 192.168.1.* subnet
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for home network use
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount static files directory ---
app.mount("/static", StaticFiles(directory="static"), name="static")
# --- End mount ---

# Create database tables
Base.metadata.create_all(bind=engine)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to AI Kids Challenge Game API"}

# Include routers
app.include_router(challenge_router, prefix="/api", tags=["api"])

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True) 