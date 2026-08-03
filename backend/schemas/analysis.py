import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CategoryScores(BaseModel):
    """Scores breakdown used in AnalysisReport.category_scores."""
    technical: float | None = Field(None, ge=0, le=10)
    behavioral: float | None = Field(None, ge=0, le=10)
    communication: float | None = Field(None, ge=0, le=10)


class AnalysisReportRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    overall_score: float | None = Field(None, ge=0, le=10)
    category_scores: dict | None = None
    strengths: list[str]
    weaknesses: list[str]
    interviewer_intent_summary: str | None = None
    recommended_practice: list[str]
    pdf_report_url: str | None = None
    generated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisReportCreate(BaseModel):
    """Used internally by the AI Integration Agent to persist results."""
    overall_score: float | None = Field(None, ge=0, le=10)
    category_scores: CategoryScores | None = None
    strengths: list[str] = []
    weaknesses: list[str] = []
    interviewer_intent_summary: str | None = None
    recommended_practice: list[str] = []
    pdf_report_url: str | None = None
