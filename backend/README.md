# Backend

FastAPI app plus a separate worker process. See `docs/ARCHITECTURE.md`.

Current state: only a health-check skeleton. The agent builds the rest in Phase 1+.

Quick start:

```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
# open http://127.0.0.1:8000/api/health
```
