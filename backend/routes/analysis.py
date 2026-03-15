from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from backend.models.schemas import (
    ClauseExtractionResponse,
    ClauseMap,
    DocumentAnalysisResponse,
    DocumentInput,
    EntityExtractionResponse,
    RiskAnalysisResponse,
    SummaryResponse,
)
from backend.services.analysis_job_service import analysis_job_service
from backend.services.analysis_service import analysis_service


router = APIRouter(tags=["analysis"])


@router.post("/upload-document", response_model=DocumentAnalysisResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentAnalysisResponse:
    try:
        return await analysis_service.process_uploaded_file(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {exc}") from exc


@router.post("/analysis-jobs")
async def create_analysis_job(file: UploadFile = File(...)) -> dict:
    try:
        file_bytes = await file.read()
        return await analysis_job_service.create_job(file.filename or "uploaded_document", file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis job: {exc}") from exc


@router.get("/analysis-jobs/{job_id}")
async def get_analysis_job(job_id: str) -> dict:
    try:
        return await analysis_job_service.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Analysis job not found.") from exc


@router.get("/analysis-jobs/{job_id}/events")
async def stream_analysis_job(job_id: str) -> StreamingResponse:
    try:
        event_generator = await analysis_job_service.stream_events(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Analysis job not found.") from exc

    return StreamingResponse(
        event_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_document(payload: DocumentInput) -> SummaryResponse:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text payload cannot be empty.")
    analysis = analysis_service.get_analysis(payload.text)
    return SummaryResponse(
        summary=analysis["summary"],
        detailed_summary=analysis.get("detailed_summary", ""),
        verdict=analysis["verdict"],
    )


@router.post("/extract-entities", response_model=EntityExtractionResponse)
async def extract_entities(payload: DocumentInput) -> EntityExtractionResponse:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text payload cannot be empty.")
    analysis = analysis_service.get_analysis(payload.text)
    return EntityExtractionResponse(entities=analysis["entities"])


@router.post("/extract-clauses", response_model=ClauseExtractionResponse)
async def extract_clauses(payload: DocumentInput) -> ClauseExtractionResponse:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text payload cannot be empty.")
    analysis = analysis_service.get_analysis(payload.text)
    return ClauseExtractionResponse(clauses=ClauseMap(**analysis["clauses"]), verdict=analysis["verdict"])


@router.post("/analyze-risks", response_model=RiskAnalysisResponse)
async def analyze_risks(payload: DocumentInput) -> RiskAnalysisResponse:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text payload cannot be empty.")
    analysis = analysis_service.get_analysis(payload.text)
    return RiskAnalysisResponse(risks=analysis["risks"])
