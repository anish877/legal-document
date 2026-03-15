from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.analysis import router as analysis_router


app = FastAPI(
    title="Legal Document Analyzer API",
    version="1.0.0",
    description="AI-powered analysis for legal PDF and text documents.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
