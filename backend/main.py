import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.analysis import router as analysis_router


app = FastAPI(
    title="Legal Document Analyzer API",
    version="1.0.0",
    description="AI-powered analysis for legal PDF and text documents.",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=False if allowed_origins == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
