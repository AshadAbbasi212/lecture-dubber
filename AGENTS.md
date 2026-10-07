# Standing rules for the AI agent

You are building **Lecture Dubber**. Read these files in order before writing code:
`README.md` → `docs/REQUIREMENTS.md` → `docs/ARCHITECTURE.md` → `docs/PIPELINE.md`
→ `docs/MODEL_CHOICES.md` → `docs/RISKS.md` → `docs/TASKS.md`.

## Working rules

1. **Follow `docs/TASKS.md` in order.** Finish a phase, summarize what you did,
   and wait for the user's go-ahead before starting the next phase.
2. **Phase 0 first.** Do not write application code until the research spikes are
   done and their results are recorded in `docs/DECISIONS.md`.
3. **Verify, never assume.** Model licenses, language support, VRAM needs and repo
   status in `docs/MODEL_CHOICES.md` were written from memory. Check the official
   repo / model card / license file for each model before adopting it. This is a
   **commercial** product: non-commercial or research-only licenses are blockers.
   Record the license text or link you relied on in `docs/DECISIONS.md`.
4. **Everything runs locally.** No hosted AI APIs for translation, TTS, ASR or
   lip-sync. (Downloading models and packages is fine.)
5. **Target hardware:** Windows, one NVIDIA GPU with 8 GB VRAM. Run GPU stages
   one at a time and free VRAM between them. Prefer running each heavy model in
   its own subprocess (and its own virtualenv) so dependency pins never collide.
6. **Swappable models.** Hide every model behind a small interface
   (`ASREngine`, `Translator`, `TTSEngine`, `VoiceConverter`, `LipSyncEngine`)
   so a model can be replaced without touching the pipeline.
7. **Every pipeline stage is idempotent and resumable.** Write artifacts to
   storage, record them in the DB, and skip a stage if its output already exists.
   Lectures are 30 to 60 minutes; a crash must not force a full restart.
8. **Windows first.** Provide PowerShell scripts. If a repo does not work on
   native Windows, say so and propose WSL2 as a documented fallback instead of
   silently switching.
9. **Security basics are not optional:** SSRF protection on URL import, file-type
   validation with ffprobe, size and duration limits, per-user file isolation,
   hashed passwords, signed download links, no secrets in git.
10. **Small, reviewable commits.** Add tests for non-GPU logic (timing fit,
    segment merging, URL validation, state machine). Keep a short changelog.
11. **Ask the user** when a decision is genuinely theirs (pricing, legal wording,
    which of two acceptable models to ship). Do not ask about things you can
    research or decide yourself.
12. **v1 has NO lip-sync.** Do not install, benchmark or build lip-sync, face
    detection or face restoration in v1. Do keep the `LipSyncEngine` interface stub
    and the reserved `lipsyncing` state so it can be added later (Phase 8).
13. **Be honest about results.** If a model's Urdu quality is poor, or lip-sync is
    too slow on 8 GB, report it with measurements. Do not hide it.
