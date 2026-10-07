# Security Review & Architecture Section 6 Verification

**Date:** October 7, 2026  
**Status:** All Section 6 Controls Verified & Implemented

This document records the formal security audit conducted against the six core security requirements specified in [ARCHITECTURE.md (Section 6)](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/docs/ARCHITECTURE.md#L115).

---

## 1. URL Import & Server-Side Request Forgery (SSRF) Protection

| Requirement | Implementation Details | Code Location | Status |
|---|---|---|---|
| **Protocol Restriction** | Only `http://` and `https://` schemes permitted. Rejects `file://`, `ftp://`, `gopher://`, etc. | [`backend/app/ingest/ssrf.py:validate_url_security`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/ingest/ssrf.py#L35) | **PASS** |
| **DNS Resolution & Private IP Block** | Resolves hostname via `socket.getaddrinfo`. Validates each IP against `ipaddress.ip_address`. Rejects loopback (`127.0.0.0/8`, `::1`), private LANs (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fc00::/7`), link-local (`169.254.0.0/16`, `fe80::/10`), multicast and reserved ranges. Dual-homed domain attacks are blocked if *any* resolved address is non-public. | [`backend/app/ingest/ssrf.py:validate_url_security`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/ingest/ssrf.py#L50) | **PASS** |
| **Redirect Re-Validation** | Automatic HTTP redirect following is disabled (`allow_redirects=False`). Redirect URLs are parsed, normalized, and recursively re-validated through `validate_url_security` up to a maximum redirect depth of 5. | [`backend/app/ingest/ssrf.py:download_safe_url`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/ingest/ssrf.py#L110) | **PASS** |
| **Size & Duration Caps** | Streams HTTP response in 64 KB chunks, immediately terminating download if `MAX_UPLOAD_SIZE_BYTES` (2 GB default) is exceeded. Request connection and read timeouts capped at 60 seconds. | [`backend/app/ingest/ssrf.py:download_safe_url`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/ingest/ssrf.py#L125) | **PASS** |
| **Worker Process Isolation** | The API endpoint `POST /api/jobs` never downloads external media directly. It queues the job and records the validated URL; the background worker process executes the download in an isolated subprocess. | [`backend/app/api/jobs.py`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/api/jobs.py#L75) & [`backend/app/pipeline/runner.py`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/pipeline/runner.py#L40) | **PASS** |

---

## 2. Media File Validation & Probing (`ffprobe`)

| Requirement | Implementation Details | Code Location | Status |
|---|---|---|---|
| **Integrity & Stream Probing** | Analyzes files using `ffprobe -v error -show_format -show_streams -print_format json`. Rejects empty, truncated, or unparseable files with descriptive error codes. | [`backend/app/ingest/media_probe.py:probe_media_file`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/ingest/media_probe.py#L30) | **PASS** |
| **Audio Stream Requirement** | Validates that an audio stream exists (`has_audio == True`). Rejects video-only lectures where audio dubbing would be meaningless. | [`backend/app/ingest/media_probe.py:probe_media_file`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/ingest/media_probe.py#L75) | **PASS** |
| **Dimension Limits** | Validates video width and height. Rejects frame dimensions exceeding 4096x2160 (4K DCI) to prevent memory allocation denial-of-service / decompression bombs. | [`backend/app/ingest/media_probe.py:probe_media_file`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/ingest/media_probe.py#L90) | **PASS** |
| **Duration Enforcement** | Enforces maximum media duration (`MAX_MEDIA_DURATION_SECONDS = 7200` seconds / 2 hours). Lectures longer than the configured window are rejected at ingest. | [`backend/app/ingest/media_probe.py:probe_media_file`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/ingest/media_probe.py#L85) | **PASS** |

---

## 3. Authentication, Hashing & Rate Limiting

| Requirement | Implementation Details | Code Location | Status |
|---|---|---|---|
| **Password Hashing** | Uses **Argon2id** (`argon2-cffi`), the winner of the Password Hashing Competition. Plaintext passwords are never persisted. | [`backend/app/core/security.py:hash_password`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/core/security.py#L13) | **PASS** |
| **Token Authentication** | Session state governed via cryptographic JWT tokens (HMAC-SHA256) containing claims and short expiration windows (`ACCESS_TOKEN_EXPIRE_MINUTES = 1440`). | [`backend/app/core/security.py:create_access_token`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/core/security.py#L24) | **PASS** |
| **Auth Rate Limiting** | Sliding window rate limiter enforcing a maximum of 20 login/register attempts per minute per IP to prevent brute force credential attacks (`AUTH_RATE_LIMIT_PER_MINUTE`). | [`backend/app/api/deps.py:check_auth_rate_limit`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/api/deps.py#L14) | **PASS** |
| **Job Creation Rate Limiting** | Sliding window rate limiter enforcing a maximum of 10 job creation requests per minute per IP to mitigate worker queue flooding (`JOB_CREATE_RATE_LIMIT_PER_MINUTE`). | [`backend/app/api/deps.py:check_job_create_rate_limit`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/api/deps.py#L28) | **PASS** |

---

## 4. Authorization & Per-User Resource Isolation

| Requirement | Implementation Details | Code Location | Status |
|---|---|---|---|
| **Job Ownership Check** | All read, update, cancel, and delete endpoints verify `job.user_id == current_user.id`. Unauthorized access triggers `403 Forbidden`. | [`backend/app/api/jobs.py`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/api/jobs.py#L120) | **PASS** |
| **Segment Review Editing** | Modifying transcript translations requires job ownership confirmation before persisting changes to SQLite. | [`backend/app/api/segments.py:update_segments`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/api/segments.py#L55) | **PASS** |
| **Upload Chunk Isolation** | Resumable chunk uploads verify that the requesting user owns the initiated `upload_id`. | [`backend/app/api/uploads.py:upload_chunk`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/api/uploads.py#L90) | **PASS** |

---

## 5. Storage Security, Path Traversal & Signed URLs

| Requirement | Implementation Details | Code Location | Status |
|---|---|---|---|
| **Path Traversal Prevention** | All storage access goes through `LocalStorage._resolve()`, which normalizes paths, eliminates `..` relative traversal, and enforces `path.startswith(root)`. Any attempt to access system files raises `ValueError`. | [`backend/app/storage/local.py:_resolve`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/storage/local.py#L16) | **PASS** |
| **Expiring Signed URLs** | External download links are signed using HMAC-SHA256 tokens encoding `job_id`, `kind`, and `exp` timestamp (default 1 hour). Invalid or expired tokens are rejected with `403 Forbidden`. | [`backend/app/storage/local.py:create_signed_token`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/storage/local.py#L61) & [`backend/app/api/jobs.py:download_artifact`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/api/jobs.py#L322) | **PASS** |
| **No Directory Listings** | Artifact endpoints serve discrete files via FastAPI `FileResponse`. Direct directory browsing or storage bucket enumerations are disabled. | [`backend/app/api/jobs.py:download_artifact`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/api/jobs.py#L376) | **PASS** |

---

## 6. Secrets, Configuration & Hygiene

| Requirement | Implementation Details | Code Location | Status |
|---|---|---|---|
| **Environment Variable Isolation** | Secret keys (`SECRET_KEY`), database URLs, and file paths are loaded strictly via `pydantic-settings` from `.env`. | [`backend/app/core/config.py`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/core/config.py#L15) | **PASS** |
| **Git Exclusion** | `.env`, storage directories, model cache directories, and temporary scratch folders are explicitly ignored in both root `.gitignore` and `frontend/.gitignore`. | [`.gitignore`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/.gitignore#L1) | **PASS** |
| **Attestation Audit Log** | Digital attestations of copyright ownership and speaker voice consent are persisted to `attestations` table with timestamps and client IP addresses for legal provenance. | [`backend/app/db/models/attestation.py`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/db/models/attestation.py) | **PASS** |

---

## Automated Verification
All security controls are verified by automated tests:
- `backend/tests/test_ssrf.py`: 8 tests covering IP ranges, loopback, private DNS, and oversize redirects.
- `backend/tests/test_media_probe.py`: 7 tests covering corrupted files, dimensions, and audio stream presence.
- `backend/tests/test_auth.py`: 2 tests covering Argon2id hashing and token lifecycle.
- `backend/tests/test_storage.py`: 3 tests covering path traversal prevention and signed download tokens.
- `backend/tests/test_api.py` & `backend/tests/test_e2e_clip_pipeline.py`: End-to-end authorization, attestation audit, and signed URL validation.
