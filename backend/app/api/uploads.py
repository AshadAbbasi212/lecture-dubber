import os
import uuid
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.storage.local import storage
from backend.app.api.deps import get_current_user
from backend.app.db.models.user import User

router = APIRouter(prefix="/uploads", tags=["uploads"])


class UploadInitRequest(BaseModel):
    filename: str
    total_size: int  # in bytes


class UploadInitResponse(BaseModel):
    upload_id: str
    max_chunk_size: int = 10 * 1024 * 1024  # 10 MB chunks recommended


class UploadCompleteResponse(BaseModel):
    upload_id: str
    file_path: str
    size: int


@router.post("", response_model=UploadInitResponse)
def start_upload(req: UploadInitRequest, current_user: User = Depends(get_current_user)):
    max_bytes = settings.MAX_UPLOAD_GB * 1024 * 1024 * 1024
    if req.total_size > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_GB} GB."
        )

    upload_id = str(uuid.uuid4())
    upload_dir = f"uploads/{upload_id}"
    meta_key = f"{upload_dir}/meta.json"
    storage.put(meta_key, f'{{"filename": "{req.filename}", "total_size": {req.total_size}}}'.encode("utf-8"))

    return UploadInitResponse(upload_id=upload_id)


@router.patch("/{upload_id}")
async def upload_chunk(
    upload_id: str,
    request: Request,
    content_range: Optional[str] = Header(None, alias="Content-Range"),
    upload_offset: Optional[int] = Header(None, alias="Upload-Offset"),
    current_user: User = Depends(get_current_user)
):
    upload_dir = f"uploads/{upload_id}"
    if not storage.exists(f"{upload_dir}/meta.json"):
        raise HTTPException(status_code=404, detail="Upload session not found")

    body = await request.body()
    offset = upload_offset if upload_offset is not None else 0
    chunk_key = f"{upload_dir}/chunk_{offset:012d}"
    storage.put(chunk_key, body)

    return {"uploaded": len(body), "offset": offset}


@router.post("/{upload_id}/complete", response_model=UploadCompleteResponse)
def complete_upload(upload_id: str, current_user: User = Depends(get_current_user)):
    upload_dir = f"uploads/{upload_id}"
    if not storage.exists(f"{upload_dir}/meta.json"):
        raise HTTPException(status_code=404, detail="Upload session not found")

    target_key = f"{upload_dir}/source.mp4"
    target_path = storage.get_path(target_key)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect and sort chunks
    chunks_dir = storage.get_path(upload_dir)
    chunk_files = sorted([f for f in chunks_dir.glob("chunk_*") if f.is_file()])

    total_bytes = 0
    with open(target_path, "wb") as outfile:
        for cf in chunk_files:
            with open(cf, "rb") as infile:
                data = infile.read()
                outfile.write(data)
                total_bytes += len(data)
            # Remove chunk once merged
            cf.unlink()

    return UploadCompleteResponse(
        upload_id=upload_id,
        file_path=str(target_key),
        size=total_bytes
    )
