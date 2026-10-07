from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.db.models.job import Job
from backend.app.db.models.segment import Segment
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/jobs/{job_id}/segments", tags=["segments"])


class SegmentResponse(BaseModel):
    id: str
    idx: int
    start: float
    end: float
    speaker: str
    src_text: str
    tgt_text: str
    edited_by_user: bool


class SegmentUpdateRequest(BaseModel):
    id: str
    tgt_text: str


@router.get("", response_model=List[SegmentResponse])
def get_segments(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    segments = db.query(Segment).filter(Segment.job_id == job.id).order_by(Segment.idx.asc()).all()
    return [
        SegmentResponse(
            id=s.id,
            idx=s.idx,
            start=s.start,
            end=s.end,
            speaker=s.speaker,
            src_text=s.src_text,
            tgt_text=s.tgt_text,
            edited_by_user=s.edited_by_user
        )
        for s in segments
    ]


@router.put("", response_model=List[SegmentResponse])
def update_segments(
    job_id: str,
    updates: List[SegmentUpdateRequest],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    updated_ids = {u.id: u.tgt_text for u in updates}
    segments = db.query(Segment).filter(Segment.job_id == job.id).all()

    for seg in segments:
        if seg.id in updated_ids:
            new_text = updated_ids[seg.id]
            if seg.tgt_text != new_text:
                seg.tgt_text = new_text
                seg.edited_by_user = True

    db.commit()

    refreshed = db.query(Segment).filter(Segment.job_id == job.id).order_by(Segment.idx.asc()).all()
    return [
        SegmentResponse(
            id=s.id,
            idx=s.idx,
            start=s.start,
            end=s.end,
            speaker=s.speaker,
            src_text=s.src_text,
            tgt_text=s.tgt_text,
            edited_by_user=s.edited_by_user
        )
        for s in refreshed
    ]
