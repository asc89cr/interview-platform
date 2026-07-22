"""File attachment endpoint — creates a DB record and returns a presigned S3 URL."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.db.base import get_db
from backend.db.models.attached_file import AttachedFile
from backend.db.models.session import Session
from backend.db.models.user import User
from backend.schemas.session import AttachedFileRead
from backend.services.s3 import generate_presigned_upload_url, make_session_file_key, s3_object_url

router = APIRouter(tags=["files"])


class FileAttachRequest(BaseModel):
    label: str
    filename: str
    content_type: str = "application/octet-stream"


class FileAttachResponse(BaseModel):
    file: AttachedFileRead
    upload: dict  # presigned POST payload {url, fields, key}


@router.post(
    "/sessions/{session_id}/files",
    response_model=FileAttachResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attach_file(
    session_id: uuid.UUID,
    body: FileAttachRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an AttachedFile record and return a presigned S3 POST URL.

    The client should upload the file directly to S3 using the returned
    ``upload`` payload, then the file is accessible at ``file.file_url``.
    """
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    key = make_session_file_key(str(session_id), body.filename)

    attached = AttachedFile(
        session_id=session_id,
        label=body.label,
        file_url=s3_object_url(key),
        file_type=body.content_type,
    )
    db.add(attached)
    await db.flush()

    presigned = generate_presigned_upload_url(key, body.content_type)
    return FileAttachResponse(
        file=AttachedFileRead.model_validate(attached),
        upload=presigned,
    )
