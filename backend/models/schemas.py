from typing import Any

from pydantic import BaseModel, Field


class DocumentInput(BaseModel):
    text: str = Field(..., description="Plain legal document text.")


class ClauseDetail(BaseModel):
    clause: str = ""
    present: bool
    text: str = ""
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class PartyEntity(BaseModel):
    name: str
    role: str = "Party"


class ClauseMap(BaseModel):
    payment_clause: ClauseDetail
    confidentiality_clause: ClauseDetail
    termination_clause: ClauseDetail
    governing_law_clause: ClauseDetail


class EntityMap(BaseModel):
    judges: list[str] = Field(default_factory=list)
    parties: list[PartyEntity] = Field(default_factory=list)
    case_numbers: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    money: list[str] = Field(default_factory=list)
    monetary_values: list[str] = Field(default_factory=list)


class InsightMap(BaseModel):
    document_type: str = ""
    parties_inferred: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    financial_terms: list[str] = Field(default_factory=list)
    important_clauses: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    summary: str
    detailed_summary: str = ""
    verdict: str


class EntityExtractionResponse(BaseModel):
    entities: EntityMap


class ClauseExtractionResponse(BaseModel):
    clauses: ClauseMap
    verdict: str


class RiskItem(BaseModel):
    title: str
    level: str
    description: str
    recommendation: str


class RiskAnalysisResponse(BaseModel):
    risks: list[RiskItem]


class DocumentMetadata(BaseModel):
    filename: str
    file_type: str
    pages: int | None = None
    scanned_pdf: bool = False
    text_length: int
    chunk_count: int


class DocumentAnalysisResponse(BaseModel):
    extracted_text: str
    summary: str
    detailed_summary: str = ""
    entities: EntityMap
    insights: InsightMap = Field(default_factory=InsightMap)
    clauses: ClauseMap
    verdict: str
    risks: list[RiskItem]
    metadata: DocumentMetadata
    debug: dict[str, Any] = Field(default_factory=dict)
