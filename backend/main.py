from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Keyword RAG Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import endpoints

app.include_router(endpoints.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Keyword RAG Service API is running"}
