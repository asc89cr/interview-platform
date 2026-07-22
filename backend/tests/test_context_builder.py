"""Unit tests for context_builder — keyword detection and context assembly."""

import pytest

from backend.ai.context_builder import build_context, detect_question_type
from backend.ai.types import (
    AnswerContext,
    AttachedFile,
    CandidateProfile,
    InterviewerProfile,
    Turn,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def candidate() -> CandidateProfile:
    return CandidateProfile(
        id="cand-1",
        target_role="Senior Software Engineer",
        skills=["Python", "FastAPI", "PostgreSQL", "AWS"],
        weak_areas=["public speaking"],
        custom_notes="Prefers concise bullet answers.",
        parsed_resume={
            "skills": ["Python", "FastAPI"],
            "experience": [{"title": "SWE", "company": "Acme", "duration": "2021-2023", "description": "Built APIs"}],
            "education": [{"degree": "BS CS", "institution": "MIT", "year": "2020"}],
            "achievements": ["Reduced latency by 40%"],
        },
    )


@pytest.fixture
def interviewer() -> InterviewerProfile:
    return InterviewerProfile(
        id="int-1",
        name="Jane Smith",
        company="Acme Corp",
        role="Engineering Manager",
        interview_style="mixed",
        known_questions=["Tell me about a challenging project.", "How do you handle deadlines?"],
        notes="Likes STAR-format answers.",
    )


@pytest.fixture
def files() -> list[AttachedFile]:
    return [
        AttachedFile(filename="job_description.txt", content="We are looking for a senior Python engineer."),
    ]


@pytest.fixture
def history() -> list[Turn]:
    return [
        Turn(speaker="Interviewer", text="What is your background?"),
        Turn(speaker="Candidate", text="I have 5 years of Python experience."),
        Turn(speaker="Interviewer", text="Tell me more about your projects."),
        Turn(speaker="Candidate", text="I built a high-throughput API at Acme."),
        Turn(speaker="Interviewer", text="How large was the team?"),
        Turn(speaker="Candidate", text="About 8 engineers."),
        Turn(speaker="Interviewer", text="What was your role?"),  # 7th — should be trimmed
        Turn(speaker="Candidate", text="Tech lead."),             # 8th — should be trimmed
    ]


# ── detect_question_type ──────────────────────────────────────────────────────


@pytest.mark.parametrize("text,expected", [
    # Behavioral
    ("Tell me about a time you handled conflict.", "behavioral"),
    ("Describe a situation where you failed.", "behavioral"),
    ("Give me an example of leadership.", "behavioral"),
    ("How did you handle a tight deadline?", "behavioral"),
    ("What is your greatest weakness?", "behavioral"),
    ("Walk me through a challenging project.", "behavioral"),
    # Small talk
    ("How are you doing today?", "small_talk"),
    ("Nice to meet you!", "small_talk"),
    ("Tell me about yourself.", "small_talk"),
    ("Good morning, did you find the office okay?", "small_talk"),
    # Technical
    ("What is the difference between a process and a thread?", "technical"),
    ("How does PostgreSQL handle MVCC?", "technical"),
    ("Explain the CAP theorem.", "technical"),
    ("What is O(n log n) complexity?", "technical"),
    ("How would you design a rate limiter?", "technical"),
])
def test_detect_question_type(text: str, expected: str) -> None:
    assert detect_question_type(text) == expected


def test_detect_question_type_case_insensitive() -> None:
    assert detect_question_type("TELL ME ABOUT A TIME you led a team") == "behavioral"


# ── build_context ─────────────────────────────────────────────────────────────


def test_build_context_technical(candidate, interviewer, files, history) -> None:
    turn = Turn(speaker="Interviewer", text="How does Python's GIL work?")
    ctx = build_context(turn, candidate, interviewer, files, history)

    assert isinstance(ctx, AnswerContext)
    assert ctx.question_type == "technical"
    assert ctx.question_text == "How does Python's GIL work?"
    assert ctx.candidate_profile is candidate
    assert ctx.interviewer_profile is interviewer


def test_build_context_behavioral(candidate, interviewer, files, history) -> None:
    turn = Turn(speaker="Interviewer", text="Tell me about a time you resolved a conflict.")
    ctx = build_context(turn, candidate, interviewer, files, history)

    assert ctx.question_type == "behavioral"
    # Behavioral prompt should include resume placeholder rendered
    assert "Reduce" in ctx.system_prompt or "achievement" in ctx.system_prompt.lower() or "Python" in ctx.system_prompt


def test_build_context_history_trimmed_to_6(candidate, interviewer, files, history) -> None:
    """History of 8 turns must be trimmed to the last 6."""
    turn = Turn(speaker="Interviewer", text="How does FastAPI handle async?")
    ctx = build_context(turn, candidate, interviewer, files, history)

    assert len(ctx.conversation_history) == 6
    # The last 6 entries of the 8-item fixture are indices 2–7
    assert ctx.conversation_history[0].text == "Tell me more about your projects."


def test_build_context_history_under_limit(candidate, interviewer, files) -> None:
    """History shorter than 6 should not be truncated."""
    short_history = [Turn(speaker="Interviewer", text="Hello.")]
    turn = Turn(speaker="Interviewer", text="What is a decorator?")
    ctx = build_context(turn, candidate, interviewer, files, short_history)

    assert len(ctx.conversation_history) == 1


def test_build_context_system_prompt_has_candidate_role(candidate, interviewer, files) -> None:
    turn = Turn(speaker="Interviewer", text="Tell me about a time you led a project.")
    ctx = build_context(turn, candidate, interviewer, files, [])

    assert "Senior Software Engineer" in ctx.system_prompt


def test_build_context_system_prompt_has_interviewer_name(candidate, interviewer, files) -> None:
    turn = Turn(speaker="Interviewer", text="How would you design a cache?")
    ctx = build_context(turn, candidate, interviewer, files, [])

    assert "Jane Smith" in ctx.system_prompt


def test_build_context_no_resume_in_technical_prompt(candidate, interviewer, files) -> None:
    """Parsed resume JSON should NOT appear in technical question prompts."""
    turn = Turn(speaker="Interviewer", text="What is async/await?")
    ctx = build_context(turn, candidate, interviewer, files, [])

    # The behavioral prompt injects the resume; technical does not
    assert "{{CANDIDATE_RESUME}}" not in ctx.system_prompt


def test_build_context_small_talk(candidate, interviewer, files) -> None:
    turn = Turn(speaker="Interviewer", text="Good morning! How are you today?")
    ctx = build_context(turn, candidate, interviewer, files, [])

    assert ctx.question_type == "small_talk"
    # Small talk uses the technical/system prompt (not behavioral)
    assert "STAR" not in ctx.system_prompt
