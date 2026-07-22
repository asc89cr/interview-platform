"""S3 presigned URL generation and object management.

Reads credentials from environment variables:
    AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY
    AWS_REGION          (default: us-east-1)
    S3_BUCKET_NAME      (default: interview-platform-files)
"""
from __future__ import annotations

import os
import uuid

import boto3

_BUCKET = os.getenv("S3_BUCKET_NAME", "interview-platform-files")
_REGION = os.getenv("AWS_REGION", "us-east-1")
_UPLOAD_EXPIRES = 300   # seconds — presigned POST URL TTL
_DOWNLOAD_EXPIRES = 600  # seconds — presigned GET URL TTL


def _client():
    return boto3.client(
        "s3",
        region_name=_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def generate_presigned_upload_url(
    key: str,
    content_type: str,
    expires: int = _UPLOAD_EXPIRES,
) -> dict:
    """Return a presigned POST dict the client uses to upload directly to S3.

    Returns:
        {"url": str, "fields": dict, "key": str}
    """
    s3 = _client()
    response = s3.generate_presigned_post(
        Bucket=_BUCKET,
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[{"Content-Type": content_type}],
        ExpiresIn=expires,
    )
    return {"url": response["url"], "fields": response["fields"], "key": key}


def generate_presigned_download_url(
    key: str,
    expires: int = _DOWNLOAD_EXPIRES,
) -> str:
    """Return a presigned GET URL for reading an S3 object."""
    s3 = _client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": _BUCKET, "Key": key},
        ExpiresIn=expires,
    )


def make_resume_key(user_id: str) -> str:
    """Generate a unique S3 key for a resume upload."""
    return f"resumes/{user_id}/{uuid.uuid4()}.pdf"


def make_session_file_key(session_id: str, filename: str) -> str:
    """Generate a unique S3 key for a session file attachment."""
    return f"sessions/{session_id}/{uuid.uuid4()}_{filename}"


def s3_object_url(key: str) -> str:
    """Return the public-style S3 object URL for a given key."""
    return f"https://{_BUCKET}.s3.{_REGION}.amazonaws.com/{key}"
