import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CategoryScores(BaseModel):
    """Scores breakdown used in AnalysisReport.category_scores."""
    technical: Optional[float] = Field(None, ge=0, le=10)
    behavioral: Optional[float] = Field(None, ge=0, le=10)
    communication: Optional[float] = Field(None, ge=0, le=10)


class AnalysisReportRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    overall_score: Optional[float] = Field(None, ge=0, le=10)
    category_scores: Optional[dict] = None
    strengths: list[str]
    weaknesses: list[str]
    interviewer_intent_summary: Optional[str] = None
    recommended_practice: list[str]
    pdf_report_url: Optional[str] = None
    generated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisReportCreate(BaseModel):
    """Used internally by the AI Integration Agent to persist results."""
    overall_score: Optional[float] = Field(None, ge=0, le=10)
    category_scores: Optional[CategoryScores] = None
    strengths: list[str] = []
    weaknesses: list[str] = []
    interviewer_intent_summary: Optional[str] = None
    recommended_practice: list[str] = []
    pdf_report_url: Optional[str] = None
