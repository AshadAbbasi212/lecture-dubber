import json
import os
import uuid
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.storage.local import storage
from backend.app.api.deps import get_current_user
from backend.app.db.models.user import User
from backend.app.ingest.media_probe import probe_media_file, standardize_to_mp4, MediaValidationError

router = APIRouter(prefix="/uploads", tags=["uploads"])


class UploadInitRequest(BaseModel):
    filename: str
    total_size: int  # in bytes


class UploadInitResponse(BaseModel):
    upload_id: str
    filename: str
    total_size: int
    max_chunk_size: int = 10 * 1024 * 1024  # 10 MB chunks recommended


class UploadStatusResponse(BaseModel):
    upload_id: str
    filename: str
    total_size: int
    bytes_uploaded: int
    chunks_received: int
    is_completed: bool


class UploadCompleteResponse(BaseModel):
    upload_id: str
    file_path: str
    size: int
    duration: float
    has_video: bool
    width: Optional[int] = None
    height: Optional[int] = None


@router.post("", response_model=UploadInitResponse)
def start_upload(req: UploadInitRequest, current_user: User = Depends(get_current_user)):
    # 1. Validate file extension
    ext = Path(req.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Permitted formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. Validate file size limit
    max_bytes = settings.MAX_UPLOAD_GB * 1024 * 1024 * 1024
    if req.total_size <= 0:
        raise HTTPException(status_code=400, detail="Total size must be greater than 0 bytes.")

    if req.total_size > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({req.total_size / (1024*1024*1024):.2f} GB) exceeds maximum upload limit of {settings.MAX_UPLOAD_GB} GB."
        )

    upload_id = str(uuid.uuid4())
    upload_dir = f"uploads/{upload_id}"
    meta_key = f"{upload_dir}/meta.json"
    meta_content = {
        "upload_id": upload_id,
        "user_id": current_user.id,
        "filename": req.filename,
        "total_size": req.total_size,
        "extension": ext
    }
    storage.put(meta_key, json.dumps(meta_content).encode("utf-8"))

    return UploadInitResponse(
        upload_id=upload_id,
        filename=req.filename,
        total_size=req.total_size
    )


@router.get("/{upload_id}", response_model=UploadStatusResponse)
def get_upload_status(upload_id: str, current_user: User = Depends(get_current_user)):
    """Allows client to check current upload offset for resumption."""
    upload_dir = f"uploads/{upload_id}"
    meta_key = f"{upload_dir}/meta.json"
    if not storage.exists(meta_key):
        raise HTTPException(status_code=404, detail="Upload session not found.")

    meta_raw = storage.get(meta_key)
    meta = json.loads(meta_raw.decode("utf-8"))

    if meta.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this upload session.")

    chunks_dir = storage.get_path(upload_dir)
    chunk_files = [f for f in chunks_dir.glob("chunk_*") if f.is_file()]
    bytes_uploaded = sum(f.stat().st_size for f in chunk_files)
    is_completed = storage.exists(f"{upload_dir}/source.mp4")

    return UploadStatusResponse(
        upload_id=upload_id,
        filename=meta["filename"],
        total_size=meta["total_size"],
        bytes_uploaded=bytes_uploaded,
        chunks_received=len(chunk_files),
        is_completed=is_completed
    )


@router.patch("/{upload_id}")
async def upload_chunk(
    upload_id: str,
    request: Request,
    content_range: Optional[str] = Header(None, alias="Content-Range"),
    upload_offset: Optional[int] = Header(None, alias="Upload-Offset"),
    current_user: User = Depends(get_current_user)
):
    upload_dir = f"uploads/{upload_id}"
    meta_key = f"{upload_dir}/meta.json"
    if not storage.exists(meta_key):
        raise HTTPException(status_code=404, detail="Upload session not found")

    meta = json.loads(storage.get(meta_key).decode("utf-8"))
    if meta.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload to this session.")

    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty chunk payload received.")

    offset = upload_offset if upload_offset is not None else 0
    chunk_key = f"{upload_dir}/chunk_{offset:012d}"
    storage.put(chunk_key, body)

    return {"uploaded": len(body), "offset": offset}


@router.post("/{upload_id}/complete", response_model=UploadCompleteResponse)
def complete_upload(upload_id: str, current_user: User = Depends(get_current_user)):
    upload_dir = f"uploads/{upload_id}"
    meta_key = f"{upload_dir}/meta.json"
    if not storage.exists(meta_key):
        raise HTTPException(status_code=404, detail="Upload session not found")

    meta = json.loads(storage.get(meta_key).decode("utf-8"))
    if meta.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to complete this upload session.")

    raw_assembled_key = f"{upload_dir}/assembled_raw{meta['extension']}"
    raw_assembled_path = storage.get_path(raw_assembled_key)
    raw_assembled_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect and sort chunks by filename (offset-indexed)
    chunks_dir = storage.get_path(upload_dir)
    chunk_files = sorted([f for f in chunks_dir.glob("chunk_*") if f.is_file()])

    if not chunk_files:
        raise HTTPException(status_code=400, detail="No uploaded chunks found to assemble.")

    total_bytes = 0
    with open(raw_assembled_path, "wb") as outfile:
        for cf in chunk_files:
            with open(cf, "rb") as infile:
                data = infile.read()
                outfile.write(data)
                total_bytes += len(data)
            cf.unlink()

    target_key = f"{upload_dir}/source.mp4"
    target_path = storage.get_path(target_key)

    try:
        # Step 1: Probe the uploaded media file
        probe_media_file(raw_assembled_path)

        # Step 2: Standardize to MP4 container (FastStart + AAC)
        standardize_to_mp4(raw_assembled_path, target_path)

        # If raw assembled file is different from source.mp4, clean it up
        if raw_assembled_path != target_path and raw_assembled_path.exists():
            raw_assembled_path.unlink()

        # Step 3: Final validation probe on standardized source.mp4
        final_probe = probe_media_file(target_path)

    except MediaValidationError as e:
        # Cleanup files on validation failure
        if raw_assembled_path.exists():
            raw_assembled_path.unlink()
        if target_path.exists():
            target_path.unlink()
        raise HTTPException(status_code=400, detail=str(e))

    return UploadCompleteResponse(
        upload_id=upload_id,
        file_path=str(target_key),
        size=target_path.stat().st_size,
        duration=final_probe.duration,
        has_video=final_probe.has_video,
        width=final_probe.width,
        height=final_probe.height
    )
