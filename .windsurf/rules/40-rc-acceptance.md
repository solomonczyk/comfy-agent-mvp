# RC Acceptance Rules

- Project can be initialized by command.
- Agent can run without Windsurf for normal use.
- ProjectProfile controls characters/references.
- No character-specific hardcode remains in core.
- Workflow can be safely edited and validated.
- Preflight blocks invalid runtime before real submit.
- Real generate_frames produces frame_count > 0.
- QC rejects broken/contact-sheet/empty outputs.
- Retry is bounded and logged.
- Ledger and ArtifactIndex are complete.
- Operator can inspect status and artifacts.
- Runbook and acceptance report exist.
- Second dummy character/profile test proves portability.
- Final proof pack is reproducible.

Golden Path:
init-project → project_profile → prompt_pack → preflight → dry proof → real generate_frames → QC → retry if needed → controlled downstream → final proof pack
