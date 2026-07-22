import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Candidate Profile ─────────────────────────────────────────────────────────

class CandidateProfileCreate(BaseModel):
    resume_url: Optional[str] = None
    target_role: Optional[str] = None
    target_salary_usd: Optional[int] = None
    skills: list[str] = []
    weak_areas: list[str] = []
    custom_notes: Optional[str] = None


class CandidateProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_url: Optional[str] = None
    parsed_resume: Optional[dict] = None
    target_role: Optional[str] = None
    target_salary_usd: Optional[int] = None
    skills: list[str]
    weak_areas: list[str]
    custom_notes: Optional[str] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class CandidateProfileUpdate(BaseModel):
    resume_url: Optional[str] = None
    target_role: Optional[str] = None
    target_salary_usd: Optional[int] = None
    skills: Optional[list[str]] = None
    weak_areas: Optional[list[str]] = None
    custom_notes: Optional[str] = None


# ── Interviewer Profile ───────────────────────────────────────────────────────

class InterviewerProfileCreate(BaseModel):
    name: str
    company: Optional[str] = None
    role: Optional[str] = None
    interview_style: str = "mixed"
    known_questions: list[str] = []
    notes: Optional[str] = None


class InterviewerProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    company: Optional[str] = None
    role: Optional[str] = None
    interview_style: str
    known_questions: list[str]
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InterviewerProfileUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    interview_style: Optional[str] = None
    known_questions: Optional[list[str]] = None
    notes: Optional[str] = None


# ── Attached File ─────────────────────────────────────────────────────────────

class AttachedFileRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    label: str
    file_url: str
    file_type: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ── Turn ──────────────────────────────────────────────────────────────────────

class TurnCreate(BaseModel):
    speaker: str  # Interviewer | Candidate
    text: str
    audio_url: Optional[str] = None


class TurnRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    speaker: str
    text: str
    generated_answer: Optional[str] = None
    timestamp: datetime
    audio_url: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Session ───────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    candidate_profile_id: Optional[uuid.UUID] = None
    interviewer_profile_id: Optional[uuid.UUID] = None


class SessionRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    candidate_profile_id: Optional[uuid.UUID] = None
    interviewer_profile_id: Optional[uuid.UUID] = None
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionReadDetail(SessionRead):
    """Session with nested relations for full-detail endpoints."""
    attached_files: list[AttachedFileRead] = []
    turns: list[TurnRead] = []


class SessionUpdate(BaseModel):
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
