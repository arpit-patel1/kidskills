from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.database.database import engine
from app.models.models import Base
from app.api.routes import router as challenge_router

# Initialize app
app = FastAPI(title="AI Kids Challenge Game API")

# Load environment variables
load_dotenv()

# Configure CORS
origins = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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