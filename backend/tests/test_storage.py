import pytest
import time
from backend.app.storage.local import LocalStorage


def test_storage_put_get_exists_delete(tmp_path):
    store = LocalStorage(root_dir=str(tmp_path))
    key = "jobs/test_123/source.mp4"
    data = b"Hello world storage test bytes"

    assert not store.exists(key)
    store.put(key, data)
    assert store.exists(key)
    assert store.get(key) == data

    # Delete
    assert store.delete(key)
    assert not store.exists(key)


def test_storage_path_traversal_prevention(tmp_path):
    store = LocalStorage(root_dir=str(tmp_path))
    with pytest.raises(ValueError, match="Path traversal detected"):
        store.put("../../../evil.txt", b"hack")


def test_signed_tokens(tmp_path):
    store = LocalStorage(root_dir=str(tmp_path))
    token = store.create_signed_token(job_id="job_abc", kind="video", expires_in_seconds=5)
    payload = store.verify_signed_token(token)
    assert payload is not None
    assert payload["job_id"] == "job_abc"
    assert payload["kind"] == "video"

    # Bad token
    assert store.verify_signed_token("invalid.token.signature") is None
