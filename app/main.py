# app/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Data Flow Insight",
    description="Natural language query interface for service configuration and execution logs.",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}