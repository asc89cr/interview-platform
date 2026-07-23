"""Context assembly for the real-time answer agent.

Combines candidate profile, interviewer profile, attached files, and
conversation history into an AnswerContext ready for answer_agent.
"""

from __future__ import annotations

import json
from pathlib import Path

from typing import Literal

from backend.ai.types import (
    AnswerContext,
    AttachedFile,
    CandidateProfile,
    InterviewerProfile,
    Turn,
)

_PROMPT_DIR = Path(__file__).parent.parent / "prompts"
_MAX_HISTORY_TURNS = 6
_FILE_CONTENT_LIMIT = 800  # chars per attached file injected into prompt

# Keywords that signal a behavioral question (STAR-style answer needed).
_BEHAVIORAL_KEYWORDS: frozenset[str] = frozenset({
    "tell me about a time",
    "describe a situation",
    "describe a time",
    "give me an example",
    "how did you handle",
    "what would you do if",
    "walk me through",
    "how do you work",
    "greatest strength",
    "greatest weakness",
    "biggest challenge",
    "proudest achievement",
    "most proud",
    "conflict with",
    "difficult colleague",
    "difficult coworker",
    "you failed",
    "failure",
    "leadership",
    "motivated",
    "team player",
    "how do you prioritize",
    "under pressure",
    "tight deadline",
})

# Keywords that signal casual / small-talk (brief, friendly answer).
_SMALL_TALK_KEYWORDS: frozenset[str] = frozenset({
    "how are you",
    "nice to meet",
    "good morning",
    "good afternoon",
    "how was your",
    "weekend",
    "weather",
    "did you find",
    "thanks for coming",
    "tell me about yourself",
    "introduce yourself",
})


def detect_question_type(text: str) -> Literal["technical", "behavioral", "small_talk"]:
    """Return 'technical', 'behavioral', or 'small_talk' based on keywords."""
    lower = text.lower()
    for kw in _BEHAVIORAL_KEYWORDS:
        if kw in lower:
            return "behavioral"
    for kw in _SMALL_TALK_KEYWORDS:
        if kw in lower:
            return "small_talk"
    return "technical"


def build_context(
    turn: Turn,
    candidate_profile: CandidateProfile,
    interviewer_profile: InterviewerProfile,
    attached_files: list[AttachedFile],
    conversation_history: list[Turn],
) -> AnswerContext:
    """Assemble an AnswerContext from all available session data.

    Selects the appropriate system prompt (technical vs behavioral) and
    injects candidate/interviewer data via template substitution.
    Trims conversation history to the last ``_MAX_HISTORY_TURNS`` turns.
    """
    question_type = detect_question_type(turn.text)

    prompt_file = "answer_behavioral.txt" if question_type == "behavioral" else "answer_system.txt"
    raw_prompt = (_PROMPT_DIR / prompt_file).read_text(encoding="utf-8")

    system_prompt = _render_prompt(
        raw_prompt, candidate_profile, interviewer_profile, attached_files, question_type
    )

    return AnswerContext(
        question_text=turn.text,
        question_type=question_type,
        candidate_profile=candidate_profile,
        interviewer_profile=interviewer_profile,
        attached_files=attached_files,
        conversation_history=conversation_history[-_MAX_HISTORY_TURNS:],
        system_prompt=system_prompt,
    )


def _render_prompt(
    prompt: str,
    candidate: CandidateProfile,
    interviewer: InterviewerProfile,
    files: list[AttachedFile],
    question_type: str,
) -> str:
    """Replace {{PLACEHOLDER}} tokens in a prompt template."""
    skills_str = ", ".join(candidate.skills) if candidate.skills else "not specified"
    weak_areas_str = ", ".join(candidate.weak_areas) if candidate.weak_areas else "none"
    files_str = (
        "\n\n".join(f"### {f.filename}\n{f.content[:_FILE_CONTENT_LIMIT]}" for f in files)
        if files
        else "None"
    )
    known_q_str = (
        "\n".join(f"- {q}" for q in interviewer.known_questions)
        if interviewer.known_questions
        else "None on record"
    )

    # Full resume JSON only for behavioral questions to manage token budget.
    resume_str = ""
    if question_type == "behavioral" and candidate.parsed_resume:
        resume_str = json.dumps(candidate.parsed_resume, indent=2)[:2000]

    replacements = {
        "{{CANDIDATE_ROLE}}": candidate.target_role or "not specified",
        "{{CANDIDATE_SKILLS}}": skills_str,
        "{{CANDIDATE_WEAK_AREAS}}": weak_areas_str,
        "{{CANDIDATE_NOTES}}": candidate.custom_notes or "",
        "{{CANDIDATE_RESUME}}": resume_str,
        "{{INTERVIEWER_NAME}}": interviewer.name,
        "{{INTERVIEWER_COMPANY}}": interviewer.company or "the company",
        "{{INTERVIEWER_STYLE}}": interviewer.interview_style,
        "{{KNOWN_QUESTIONS}}": known_q_str,
        "{{ATTACHED_FILES}}": files_str,
    }

    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    return prompt
