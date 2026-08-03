import uuid
from datetime import datetime

from pydantic import BaseModel

# ── Candidate Profile ─────────────────────────────────────────────────────────

class CandidateProfileCreate(BaseModel):
    resume_url: str | None = None
    target_role: str | None = None
    target_salary_usd: int | None = None
    skills: list[str] = []
    weak_areas: list[str] = []
    custom_notes: str | None = None


class CandidateProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_url: str | None = None
    parsed_resume: dict | None = None
    target_role: str | None = None
    target_salary_usd: int | None = None
    skills: list[str]
    weak_areas: list[str]
    custom_notes: str | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class CandidateProfileUpdate(BaseModel):
    resume_url: str | None = None
    target_role: str | None = None
    target_salary_usd: int | None = None
    skills: list[str] | None = None
    weak_areas: list[str] | None = None
    custom_notes: str | None = None


# ── Interviewer Profile ───────────────────────────────────────────────────────

class InterviewerProfileCreate(BaseModel):
    name: str
    company: str | None = None
    role: str | None = None
    interview_style: str = "mixed"
    known_questions: list[str] = []
    notes: str | None = None


class InterviewerProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    company: str | None = None
    role: str | None = None
    interview_style: str
    known_questions: list[str]
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InterviewerProfileUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    role: str | None = None
    interview_style: str | None = None
    known_questions: list[str] | None = None
    notes: str | None = None


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
    audio_url: str | None = None


class TurnRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    speaker: str
    text: str
    generated_answer: str | None = None
    timestamp: datetime
    audio_url: str | None = None

    model_config = {"from_attributes": True}


# ── Session ───────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    candidate_profile_id: uuid.UUID | None = None
    interviewer_profile_id: uuid.UUID | None = None


class SessionRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    candidate_profile_id: uuid.UUID | None = None
    interviewer_profile_id: uuid.UUID | None = None
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionReadDetail(SessionRead):
    """Session with nested relations for full-detail endpoints."""
    attached_files: list[AttachedFileRead] = []
    turns: list[TurnRead] = []


class SessionUpdate(BaseModel):
    status: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
