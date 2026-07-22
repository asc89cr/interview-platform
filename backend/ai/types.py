"""Shared data types for the AI integration layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Turn:
    """A single spoken turn captured during a live session."""

    speaker: Literal["Interviewer", "Candidate"]
    text: str
    confidence: float = 1.0
    generated_answer: str | None = None


@dataclass
class CandidateProfile:
    """Lightweight view of a candidate used by the AI layer."""

    id: str
    target_role: str | None
    skills: list[str]
    weak_areas: list[str]
    custom_notes: str | None
    parsed_resume: dict | None  # structured JSON produced by profile_parser


@dataclass
class InterviewerProfile:
    """Lightweight view of an interviewer profile used by the AI layer."""

    id: str
    name: str
    company: str | None
    role: str | None
    interview_style: str  # technical | behavioral | mixed | case
    known_questions: list[str] = field(default_factory=list)
    notes: str | None = None


@dataclass
class AttachedFile:
    """A session-attached file with its extracted text content."""

    filename: str
    content: str  # plain-text content extracted from the file


@dataclass
class AnswerContext:
    """All context assembled by context_builder and consumed by answer_agent."""

    question_text: str
    question_type: Literal["technical", "behavioral", "small_talk"]
    candidate_profile: CandidateProfile
    interviewer_profile: InterviewerProfile
    attached_files: list[AttachedFile]
    conversation_history: list[Turn]  # already trimmed to last N turns
    system_prompt: str  # fully rendered prompt string


@dataclass
class ParsedResume:
    """Structured resume data extracted by profile_parser."""

    skills: list[str]
    experience: list[dict]   # [{title, company, duration, description}]
    education: list[dict]    # [{degree, institution, year}]
    achievements: list[str]
    raw_text: str


@dataclass
class CategoryScores:
    """Per-category interview performance scores (0–10 each)."""

    technical: float
    behavioral: float
    communication: float
    confidence: float


@dataclass
class EvidencedPoint:
    """A strength or weakness backed by a transcript quote."""

    point: str
    evidence: str  # verbatim or paraphrased transcript excerpt


@dataclass
class AnalysisReport:
    """Full post-interview analysis produced by analysis_agent."""

    session_id: str
    overall_score: float  # 0–100
    category_scores: CategoryScores
    strengths: list[EvidencedPoint]    # top 3
    weaknesses: list[EvidencedPoint]   # top 3
    interviewer_intent_summary: str
    recommended_practice: list[str]
