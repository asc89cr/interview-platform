"""Resume PDF parsing: pdfplumber text extraction + GPT-4o-mini structured output.

Runs as a background task triggered on resume upload.
Stores the result in the ``candidate_profiles.parsed_resume`` JSONB column
(callers are responsible for the DB write after receiving ParsedResume).
"""

from __future__ import annotations

import io
import json
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import boto3
import httpx
import pdfplumber
from openai import AsyncOpenAI

from backend.ai.types import ParsedResume

logger = logging.getLogger(__name__)

_MODEL = "gpt-4o-mini"
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "profile_extract.txt"
_MAX_RESUME_CHARS = 6_000  # keep well within the model's context budget

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


async def parse_resume(resume_s3_url: str) -> ParsedResume:
    """Download a resume PDF from S3 (or presigned URL), extract text, and
    return a structured ParsedResume via GPT-4o-mini.

    Args:
        resume_s3_url: Either an ``s3://bucket/key`` URI or an HTTPS presigned URL.
    """
    pdf_bytes = await _download(resume_s3_url)
    raw_text = _extract_text(pdf_bytes)
    return await _parse_with_llm(raw_text)


async def _download(url: str) -> bytes:
    """Download PDF bytes from S3 URI or HTTPS presigned URL."""
    if url.startswith("s3://"):
        parsed = urlparse(url)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=bucket, Key=key)
        return obj["Body"].read()

    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.get(url)
        resp.raise_for_status()
        return resp.content


def _extract_text(pdf_bytes: bytes) -> str:
    """Extract plain text from all pages of a PDF."""
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
    return "\n\n".join(pages)


async def _parse_with_llm(raw_text: str) -> ParsedResume:
    """Send extracted text to GPT-4o-mini and parse the structured JSON response."""
    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

    response = await _get_client().chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Resume text:\n\n{raw_text[:_MAX_RESUME_CHARS]}"},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw_json = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        logger.error("Profile parser received invalid JSON (first 200 chars): %s", raw_json[:200])
        data = {}

    return ParsedResume(
        skills=data.get("skills", []),
        experience=data.get("experience", []),
        education=data.get("education", []),
        achievements=data.get("achievements", []),
        raw_text=raw_text,
    )
