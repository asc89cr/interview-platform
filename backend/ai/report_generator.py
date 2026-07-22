"""PDF analysis report generator using ReportLab.

Generates a branded PDF from an AnalysisReport, uploads it to S3, and
returns the S3 URL. Available for Pro and Teams subscription tiers only —
callers must enforce tier access before invoking.
"""

from __future__ import annotations

import io
import os
import uuid

import boto3
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.ai.types import AnalysisReport

_S3_BUCKET: str = os.getenv("S3_BUCKET_NAME", "interview-platform-reports")
_BRAND_BLUE = colors.HexColor("#1a56db")
_SUCCESS_GREEN = colors.HexColor("#057a55")
_DANGER_RED = colors.HexColor("#e02424")
_LIGHT_GRAY = colors.HexColor("#f3f4f6")
_BORDER_GRAY = colors.HexColor("#d1d5db")


def generate_report_pdf(report: AnalysisReport) -> str:
    """Build a branded PDF report, upload to S3, and return the S3 URI.

    Args:
        report: Completed AnalysisReport from analysis_agent.

    Returns:
        S3 URI string, e.g. ``s3://interview-platform-reports/reports/<id>.pdf``.
    """
    pdf_bytes = _render_pdf(report)

    key = f"reports/{report.session_id}/{uuid.uuid4().hex}.pdf"
    s3 = boto3.client("s3")
    s3.upload_fileobj(
        io.BytesIO(pdf_bytes),
        _S3_BUCKET,
        key,
        ExtraArgs={"ContentType": "application/pdf"},
    )
    return f"s3://{_S3_BUCKET}/{key}"


def _render_pdf(report: AnalysisReport) -> bytes:
    """Build the PDF in memory and return the raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )
    doc.build(_build_story(report))
    return buffer.getvalue()


def _build_story(report: AnalysisReport) -> list:
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"], textColor=_BRAND_BLUE, fontSize=22, spaceAfter=6
    )
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], textColor=_BRAND_BLUE, fontSize=14,
        spaceBefore=16, spaceAfter=4
    )
    body = styles["BodyText"]
    strong_style = ParagraphStyle("Strong", parent=body, textColor=_SUCCESS_GREEN)
    weak_style = ParagraphStyle("Weak", parent=body, textColor=_DANGER_RED)

    story: list = []

    # ── Header ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Interview Performance Report", h1))
    story.append(Paragraph(f"Session: {report.session_id}", body))
    story.append(HRFlowable(width="100%", color=_BRAND_BLUE, spaceAfter=12))
    story.append(Spacer(1, 0.1 * inch))

    # ── Overall score ─────────────────────────────────────────────────────────
    story.append(Paragraph("Overall Score", h2))
    story.append(Paragraph(f"<b>{report.overall_score:.0f} / 100</b>", body))

    # ── Category breakdown ────────────────────────────────────────────────────
    story.append(Paragraph("Category Breakdown", h2))
    cs = report.category_scores
    table_data = [
        ["Category", "Score (0–10)"],
        ["Technical", f"{cs.technical:.1f}"],
        ["Behavioral", f"{cs.behavioral:.1f}"],
        ["Communication", f"{cs.communication:.1f}"],
        ["Confidence", f"{cs.confidence:.1f}"],
    ]
    tbl = Table(table_data, colWidths=[3 * inch, 2 * inch])
    tbl.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _BRAND_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER_GRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(tbl)
    story.append(Spacer(1, 0.15 * inch))

    # ── Strengths ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Top Strengths", h2))
    for i, s in enumerate(report.strengths, 1):
        story.append(Paragraph(f"<b>{i}. {s.point}</b>", strong_style))
        if s.evidence:
            story.append(Paragraph(f"<i>Evidence: &quot;{s.evidence}&quot;</i>", body))
        story.append(Spacer(1, 0.05 * inch))

    # ── Weaknesses ────────────────────────────────────────────────────────────
    story.append(Paragraph("Areas for Improvement", h2))
    for i, w in enumerate(report.weaknesses, 1):
        story.append(Paragraph(f"<b>{i}. {w.point}</b>", weak_style))
        if w.evidence:
            story.append(Paragraph(f"<i>Evidence: &quot;{w.evidence}&quot;</i>", body))
        story.append(Spacer(1, 0.05 * inch))

    # ── Interviewer intent ────────────────────────────────────────────────────
    story.append(Paragraph("Interviewer Intent Summary", h2))
    story.append(Paragraph(report.interviewer_intent_summary or "N/A", body))
    story.append(Spacer(1, 0.1 * inch))

    # ── Recommended practice ──────────────────────────────────────────────────
    story.append(Paragraph("Recommended Practice Topics", h2))
    for topic in report.recommended_practice:
        story.append(Paragraph(f"• {topic}", body))

    return story
