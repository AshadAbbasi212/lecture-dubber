# First prompt for Antigravity

Copy everything in the block below into the Antigravity agent (Claude model).

```
You are building the project in this workspace: "Lecture Dubber", a platform that
translates educational video lectures, dubs them in the original speaker's
cloned voice, and lets users download the result (lip-sync comes later).

Before doing anything else, read these files completely and in this order:
AGENTS.md, README.md, docs/REQUIREMENTS.md, docs/ARCHITECTURE.md,
docs/PIPELINE.md, docs/MODEL_CHOICES.md, docs/RISKS.md, docs/TASKS.md.

Then:
1. Summarize back to me, in under 25 lines, what you understood: the goal, the
   hard constraints (commercial license, fully local models, Windows, 8 GB VRAM,
   Urdu + English targets, 30 to 60 minute lectures), and the plan.
2. List anything in the docs that is unclear or that you think is wrong.
3. Start Phase 0 of docs/TASKS.md (research spikes and environment check). Run
   scripts/check_prereqs.ps1 first. Use web access to verify model licenses and
   language support. Record every decision, with sources, in docs/DECISIONS.md.
4. Stop at the end of Phase 0 and show me the results and your recommended model
   for each stage. Do not start Phase 1 until I approve.

Scope decision: v1 is built WITHOUT lip-sync. Skip the lip-sync spike (task 0.7)
and do not build lip-sync. Lip-sync is Phase 8, after I approve. Keep the design
ready for it.

Follow AGENTS.md for all rules.
```

## Tips

- If Antigravity auto-loads `AGENTS.md`, the prompt still works; the repetition is harmless.
- Approve one phase at a time. Phase 0 is where the project's biggest risks get
  resolved, so read `docs/DECISIONS.md` carefully.
- If the agent needs a decision only you can make (for example legal wording or
  retention period), it will ask.
