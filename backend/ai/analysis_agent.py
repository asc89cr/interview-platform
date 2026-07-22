"""Post-interview analysis agent using GPT-4o.

Processes the full session transcript and returns a structured AnalysisReport.
Designed to run as an async background task after a session ends (~30–60 s).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from openai import AsyncOpenAI

from backend.ai.types import AnalysisReport, CategoryScores, EvidencedPoint, Turn

logger = logging.getLogger(__name__)

_MODEL = "gpt-4o"  # more reasoning power than mini for deep analysis
_MAX_TOKENS = 2_000
_TEMPERATURE = 0.3  # more deterministic for scoring consistency
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "analysis_system.txt"

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


async def analyze_session(session_id: str, turns: list[Turn]) -> AnalysisReport:
    """Analyze a full interview transcript and return a structured AnalysisReport.

    Args:
        session_id: The UUID string of the session (stored in the report).
        turns: All Turn objects from the session in chronological order.

    Returns:
        AnalysisReport with scores, evidenced strengths/weaknesses, intent
        summary, and practice recommendations.

    Raises:
        ValueError: If the LLM response cannot be parsed as valid JSON.
    """
    transcript = _format_transcript(turns)
    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

    response = await _get_client().chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Interview transcript:\n\n{transcript}"},
        ],
        temperature=_TEMPERATURE,
        max_tokens=_MAX_TOKENS,
        response_format={"type": "json_object"},
    )

    raw_json = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        logger.error("Analysis agent returned invalid JSON for session %s: %s", session_id, exc)
        raise ValueError(f"Analysis agent returned invalid JSON for session {session_id}") from exc

    return _build_report(session_id, data)


def _format_transcript(turns: list[Turn]) -> str:
    """Render turns as a numbered, readable transcript."""
    lines: list[str] = []
    for i, turn in enumerate(turns, 1):
        lines.append(f"[{i}] {turn.speaker}: {turn.text}")
        if turn.generated_answer:
            lines.append(f"    [AI Answer used]: {turn.generated_answer}")
    return "\n".join(lines)


def _build_report(session_id: str, data: dict) -> AnalysisReport:
    """Deserialize the GPT JSON response into a typed AnalysisReport."""
    cat = data.get("category_scores", {})
    category_scores = CategoryScores(
        technical=float(cat.get("technical", 0)),
        behavioral=float(cat.get("behavioral", 0)),
        communication=float(cat.get("communication", 0)),
        confidence=float(cat.get("confidence", 0)),
    )

    def _parse_evidenced(raw: list) -> list[EvidencedPoint]:
        result: list[EvidencedPoint] = []
        for item in raw[:3]:  # cap at 3
            if isinstance(item, dict):
                result.append(
                    EvidencedPoint(
                        point=item.get("point", ""),
                        evidence=item.get("evidence", ""),
                    )
                )
            elif isinstance(item, str):
                result.append(EvidencedPoint(point=item, evidence=""))
        return result

    return AnalysisReport(
        session_id=session_id,
        overall_score=float(data.get("overall_score", 0)),
        category_scores=category_scores,
        strengths=_parse_evidenced(data.get("strengths", [])),
        weaknesses=_parse_evidenced(data.get("weaknesses", [])),
        interviewer_intent_summary=data.get("interviewer_intent_summary", ""),
        recommended_practice=data.get("recommended_practice", []),
    )
