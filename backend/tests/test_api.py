import json
import pytest
from backend.app.storage.local import storage
from backend.app.db.models.artifact import Artifact
from backend.app.db.models.job import Job
from backend.app.pipeline.state_machine import JobStatus


def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_job_crud_and_review_flow(client, auth_headers, db):
    # 1. Create job
    create_resp = client.post("/api/jobs", json={
        "source_type": "youtube",
        "source_ref": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "target_lang": "ur",
        "clone_voice": True,
        "skip_review": False,
        "ownership_confirmed": True,
        "voice_consent": True
    }, headers=auth_headers)
    assert create_resp.status_code == 200
    job_data = create_resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "queued"
    assert job_data["target_lang"] == "ur"

    # 2. Get job
    get_resp = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == job_id

    # 3. Simulate job reaching awaiting_review
    job = db.query(Job).filter(Job.id == job_id).first()
    job.status = JobStatus.AWAITING_REVIEW.value
    db.commit()

    # 4. Put segments for review
    from backend.app.db.models.segment import Segment
    seg = Segment(
        job_id=job_id,
        idx=1,
        start=0.0,
        end=3.5,
        speaker="speaker_0",
        src_text="Welcome students.",
        tgt_text="طلباء خوش آمدید۔"
    )
    db.add(seg)
    db.commit()
    db.refresh(seg)

    # 5. Fetch segments
    segs_resp = client.get(f"/api/jobs/{job_id}/segments", headers=auth_headers)
    assert segs_resp.status_code == 200
    assert len(segs_resp.json()) == 1

    # 6. Edit segments
    edit_resp = client.put(f"/api/jobs/{job_id}/segments", json=[
        {"id": seg.id, "tgt_text": "تمام طلباء کو خوش آمدید۔"}
    ], headers=auth_headers)
    assert edit_resp.status_code == 200
    assert edit_resp.json()[0]["edited_by_user"] is True
    assert edit_resp.json()[0]["tgt_text"] == "تمام طلباء کو خوش آمدید۔"

    # 7. Approve job
    approve_resp = client.post(f"/api/jobs/{job_id}/approve", headers=auth_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "running"

    # 8. Test signed download url
    # Create fake final video artifact
    art_path = f"jobs/{job_id}/output/final.mp4"
    storage.put(art_path, b"TEST_MP4_CONTENT")
    art = Artifact(job_id=job_id, kind="final_video", path=art_path, stage="muxing")
    db.add(art)
    db.commit()

    url_resp = client.get(f"/api/jobs/{job_id}/download-url?kind=video", headers=auth_headers)
    assert url_resp.status_code == 200
    dl_url = url_resp.json()["download_url"]

    # Download with the signed url
    dl_resp = client.get(dl_url)
    assert dl_resp.status_code == 200
    assert dl_resp.content == b"TEST_MP4_CONTENT"


def test_chunked_upload_flow(client, auth_headers):
    # 1. Start upload
    init_resp = client.post("/api/uploads", json={
        "filename": "lecture_01.mp4",
        "total_size": 20
    }, headers=auth_headers)
    assert init_resp.status_code == 200
    upload_id = init_resp.json()["upload_id"]

    # 2. Upload chunks
    c1_resp = client.patch(
        f"/api/uploads/{upload_id}",
        content=b"0123456789",
        headers={**auth_headers, "Upload-Offset": "0"}
    )
    assert c1_resp.status_code == 200

    c2_resp = client.patch(
        f"/api/uploads/{upload_id}",
        content=b"ABCDEFGHIJ",
        headers={**auth_headers, "Upload-Offset": "10"}
    )
    assert c2_resp.status_code == 200

    # 3. Complete upload
    comp_resp = client.post(f"/api/uploads/{upload_id}/complete", headers=auth_headers)
    assert comp_resp.status_code == 200
    assert comp_resp.json()["size"] == 20
    assert storage.get(f"uploads/{upload_id}/source.mp4") == b"0123456789ABCDEFGHIJ"


def test_sse_events_stream(client, auth_headers, db):
    # Create job
    create_resp = client.post("/api/jobs", json={
        "source_type": "upload",
        "source_ref": "uploads/fake/source.mp4",
        "target_lang": "ur"
    }, headers=auth_headers)
    assert create_resp.status_code == 200
    job_id = create_resp.json()["id"]

    # Mark completed so generator exits cleanly after initial frame
    job = db.query(Job).filter(Job.id == job_id).first()
    job.status = JobStatus.COMPLETED.value
    db.commit()

    # Stream events
    with client.stream("GET", f"/api/jobs/{job_id}/events", headers=auth_headers) as resp:
        assert resp.status_code == 200
        lines = [line for line in resp.iter_lines() if line]
        full_event_text = "\n".join(lines)
        assert "event: progress" in full_event_text
        assert job_id in full_event_text
