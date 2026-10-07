# Lecture Dubber

A platform where a user uploads a lecture video (or pastes a link), gets it
**translated and dubbed in the original speaker's voice**, then
downloads the result.

This folder is a **starter kit**: requirements, architecture, task list and a
tiny backend skeleton. It is meant to be opened in **Antigravity** with a Claude
model, which then builds the real application by following `docs/TASKS.md`.

> **Scope decision:** v1 is built **without lip-sync**. Lip-sync is a planned later
> milestone (Phase 8 in `docs/TASKS.md`). The design leaves room for it.

## How to use this with Antigravity

1. Unzip this folder and open it as a workspace in Antigravity.
2. Select a Claude model for the agent.
3. Open `docs/FIRST_PROMPT.md`, copy the prompt, and paste it into the agent.
   (`AGENTS.md` in the root holds the standing rules; if Antigravity does not
   load it automatically, the first prompt tells the agent to read it.)
4. Let the agent work through `docs/TASKS.md` phase by phase. Start with
   **Phase 0 (research spikes)**: they settle the risky model choices
   (mainly Urdu voice generation) before any app code is written.
5. Review each phase before telling the agent to continue.

## Project at a glance

| Item | Decision |
|---|---|
| Product type | Startup / commercial product (licenses matter) |
| Source languages | Any (auto-detected) |
| Target languages (v1) | English, Urdu |
| Compute | Own Windows PC, NVIDIA GPU, 8 GB VRAM |
| AI models | 100% local / open-source (translation and voice included) |
| v1 features | Voice cloning, edit translation before voice generation (no lip-sync yet) |
| Input | Upload, direct links, YouTube links (with ownership checkbox) |
| Accounts | Sign-up / login, no payments yet |
| Stack | Python FastAPI backend + Next.js (React) frontend |
| Typical video | 30 to 60 minutes |

## Folder map

```
AGENTS.md              Standing rules for the AI agent
docs/
  FIRST_PROMPT.md      Prompt to paste into Antigravity
  REQUIREMENTS.md      What we are building and the constraints
  ARCHITECTURE.md      How it is structured
  PIPELINE.md          Stage-by-stage processing design
  MODEL_CHOICES.md     Candidate models, license notes, what to verify
  RISKS.md             Known risks and fallbacks
  TASKS.md             Ordered build plan with acceptance criteria
  SETUP_WINDOWS.md     Windows environment setup
  DECISIONS.md         Agent records research results here
scripts/               PowerShell helpers (prereq check, repo fetch)
backend/               FastAPI skeleton
frontend/              Next.js app goes here
storage/               Local file storage (git-ignored)
third_party/           Cloned model repos (git-ignored)
models/                Model weights and per-model venvs (git-ignored)
```

## Important caveat

Model license and language-support notes in `docs/MODEL_CHOICES.md` were written
from memory and **must be re-verified online** by the agent in Phase 0 before
anything is adopted. This is a commercial product, so a non-commercial model
license is a blocker, not a footnote.
