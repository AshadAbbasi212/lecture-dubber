import pytest
from backend.app.ingest.share_links import is_share_link, resolve_share_link


def test_is_share_link():
    assert is_share_link("https://www.dropbox.com/s/xyz123/lecture.mp4?dl=0") is True
    assert is_share_link("https://dropbox.com/scl/fi/xyz123/lecture.mp4") is True
    assert is_share_link("https://drive.google.com/file/d/1a2b3c4d5e/view?usp=sharing") is True
    assert is_share_link("https://drive.google.com/open?id=1a2b3c4d5e") is True
    assert is_share_link("https://example.com/videos/lecture.mp4") is False
    assert is_share_link("https://youtube.com/watch?v=dQw4w9WgXcQ") is False


def test_resolve_dropbox_share_links():
    # dl=0 replaced with dl=1
    url = "https://www.dropbox.com/s/abc123xyz/math_lecture.mp4?dl=0"
    resolved = resolve_share_link(url)
    assert "dl=1" in resolved
    assert "dl.dropboxusercontent.com" in resolved

    # scl format
    scl_url = "https://www.dropbox.com/scl/fi/abc123xyz/cs101.mp4?rlkey=secretkey"
    resolved_scl = resolve_share_link(scl_url)
    assert "dl=1" in resolved_scl


def test_resolve_google_drive_share_links():
    # file/d/{id} format
    view_url = "https://drive.google.com/file/d/1A2B3C4D5E6F7G/view?usp=sharing"
    resolved = resolve_share_link(view_url)
    assert resolved == "https://drive.google.com/uc?export=download&id=1A2B3C4D5E6F7G&confirm=t"

    # open?id={id} format
    id_url = "https://drive.google.com/open?id=9Z8Y7X6W5V4U3T"
    resolved_id = resolve_share_link(id_url)
    assert resolved_id == "https://drive.google.com/uc?export=download&id=9Z8Y7X6W5V4U3T&confirm=t"


def test_resolve_standard_url_unchanged():
    direct_url = "https://mirror.example.org/lectures/lecture_01.mp4"
    assert resolve_share_link(direct_url) == direct_url
