# Risks and fallbacks

| # | Risk | Impact | Mitigation / fallback |
|---|---|---|---|
| R1 | No commercially licensed local Urdu TTS with voice cloning | Urdu dub may not keep the speaker's voice | Phase 0 spike. Options: plain Urdu TTS + voice conversion; or Urdu with a standard voice and a clear UI notice; or fine-tune a permissively licensed model on licensed data (large effort) |
| R2 | Local translation quality for Urdu (and for rarer source languages) | Wrong or awkward explanations | Evaluate on real lecture text; keep the user review step; flag low-confidence segments; allow a larger or better model later |
| R3 | (Deferred to the lip-sync milestone) Lip-sync too slow or too big for 8 GB; 60-minute lectures | Jobs take many hours, or fail | Benchmark in Phase 0; lip-sync only face-visible shots; clip-level checkpoints; make lip-sync optional per job; show honest time estimates; document cloud-GPU path |
| R4 | Model licenses block commercial use | Cannot launch | License check is a Phase 0 gate; keep models swappable; enforce commercial compliance |
| R5 | YouTube downloading violates the platform's terms and copyright law; yt-dlp breaks or gets blocked | Legal exposure and unreliable feature | Ownership checkbox with stored attestation; takedown process; clear terms; keep the feature isolated and easy to disable; obtain legal advice before launch |
| R6 | Voice cloning misuse (impersonation) | Legal and reputational harm | Explicit voice-consent checkbox stored with the job; label output as AI-dubbed; abuse reporting; consider limiting cloning to the user's own uploads |
| R7 | Dependency conflicts between model repos on Windows | Setup pain | One venv per model, subprocess wrappers; WSL2 documented as fallback |
| R8 | ASR errors propagate into translation and dub | Bad output | Show detected language and confidence; allow edit of transcript text as well as translation (stretch goal) |
| R9 | Timing: Urdu and English speech lengths differ | Audio drifts or sounds rushed | Length-aware translation; bounded time-stretch; re-translate when needed |
| R10 | Disk and cleanup: 60-minute videos create many GB of artifacts | Disk fills up | Retention job; delete intermediates after completion; per-user quota |
| R11 | Single PC is a single point of failure | Downtime | Resumable jobs; backups of DB; documented migration to cloud workers |
