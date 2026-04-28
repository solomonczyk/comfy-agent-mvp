# Handoff After RC-FINAL1

## What is Accepted

RC-FINAL1 is accepted and frozen as a reproducible Reference Implementation baseline. This proof pack demonstrates:

**Accepted Capabilities**:
- Complete control flow from brief to final render
- Reference-locked character generation (SDXL)
- Frame generation with QC validation
- Scene assembly (single-frame video)
- QA review pipeline
- No-audio policy for RC scope
- State machine with ordered transitions
- Artifact validation and provenance tracking
- Ledger-based transition history

**Accepted Artifacts**:
- All control artifacts in `data/rc_mir_erdan_ep01/output/control/`
- Generated frame: `output/frames/ep01_shot01/000001.png` (480x640)
- Scene video: `output/scenes/ep01_shot01/scene.mp4` (24fps, 3.0s)
- Proof index: `output/control/RC_FINAL_PROOF_INDEX.json`

**Validation Status**:
- 67/67 artifact checks passed
- 139/139 tests passed
- Final state: episode_rendered
- Expected next action: none

## What is Intentionally Limited

These limitations are intentional for RC scope and are documented honestly:

**Audio**:
- Audio stage completed by no-audio RC policy
- No TTS synthesis
- No audio muxing
- No audio track in final output
- This is documented in `docs/KNOWN_LIMITATIONS.md`

**Final Render**:
- Final render output is final manifest, not full audio/video render
- No final MP4 with audio
- This is documented in `docs/KNOWN_LIMITATIONS.md`

**Scene**:
- Single-frame scene.mp4 created for RC proof
- Not a full multi-frame scene render
- This is documented in `docs/KNOWN_LIMITATIONS.md`

**Scope**:
- Single shot (ep01_shot01)
- Single episode
- Reference-locked character mode only
- GTX1060 hardware profile only
- These are documented in `docs/KNOWN_LIMITATIONS.md`

## What Not to Touch

### Frozen Artifacts (DO NOT MODIFY)

**Absolute Freeze** - These artifacts must never be modified:
```
data/rc_mir_erdan_ep01/output/
data/rc_mir_erdan_ep01/output/control/
data/rc_mir_erdan_ep01/output/frames/
data/rc_mir_erdan_ep01/output/scenes/
data/rc_mir_erdan_ep01/data/briefs/
data/rc_mir_erdan_ep01/data/
```

**Specific Files** (DO NOT MODIFY):
- `data/rc_mir_erdan_ep01/output/control/artifact_index.json`
- `data/rc_mir_erdan_ep01/output/control/ep01_shot01_ledger.json`
- `data/rc_mir_erdan_ep01/output/control/ep01/shot01_state.json`
- `data/rc_mir_erdan_ep01/output/control/RC_FINAL_PROOF_INDEX.json`
- `data/rc_mir_erdan_ep01/output/control/project_profile.json`
- `data/rc_mir_erdan_ep01/output/control/prompt_pack.json`
- All other artifacts in `data/rc_mir_erdan_ep01/output/control/`

### Frozen Documentation (DO NOT MODIFY)

These documents describe the frozen state and must not be modified:
- `docs/RC_FINAL1_FREEZE.md` - Freeze document
- `docs/ACCEPTANCE_REPORT.md` - Acceptance report
- `docs/KNOWN_LIMITATIONS.md` - Known limitations
- `docs/README_RUNBOOK.md` - Runbook

### Safe to Modify

**Pipeline Logic** (OK to modify for RC2):
- `app/control/` - Control flow implementation
- `app/comfy/` - ComfyUI integration
- `app/agent/` - Agent implementation
- `app/cli.py` - CLI entry point

**Tests** (OK to modify for RC2):
- `tests/` - Test suite
- Add new tests for RC2 features

**Scripts** (OK to modify for RC2):
- `scripts/` - Utility scripts
- Add new scripts for RC2 features

**RC2 Documentation** (OK to create/modify):
- `docs/RC2_BACKLOG.md` - RC2 backlog
- `docs/RC2_PLAN.md` - RC2 plan (to be created)
- New RC2 documentation

## Where Proof Artifacts Live

**Stable Project Root**:
```
f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01
```

**Artifact Locations**:
- Control artifacts: `output/control/`
- Generated frames: `output/frames/ep01_shot01/`
- Scene videos: `output/scenes/ep01_shot01/`
- Briefs: `data/briefs/`
- Configuration: `data/`

**Proof Index**:
- `output/control/RC_FINAL_PROOF_INDEX.json`

**Documentation**:
- `docs/README_RUNBOOK.md` - How to inspect and reproduce
- `docs/ACCEPTANCE_REPORT.md` - Acceptance criteria validation
- `docs/KNOWN_LIMITATIONS.md` - Honest limitation documentation
- `docs/RC_FINAL1_FREEZE.md` - Freeze document
- `docs/RC2_BACKLOG.md` - RC2 improvements backlog

## How to Inspect the RC

### Quick Validation
```bash
python scripts/validate_rc_artifacts.py --project-root "f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01" --episode ep01 --shot shot01
```

### Check State
```bash
python -m app control-status --episode ep01 --shot shot01 --project-root "f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01" --json
```

### View Artifacts
```bash
# View artifact index
cat data/rc_mir_erdan_ep01/output/control/artifact_index.json

# View ledger
cat data/rc_mir_erdan_ep01/output/control/ep01_shot01_ledger.json

# View state
cat data/rc_mir_erdan_ep01/output/control/ep01/shot01_state.json
```

### Inspect Frame
```bash
# View frame
data/rc_mir_erdan_ep01/output/frames/ep01_shot01/000001.png
```

### Inspect Scene
```bash
# Play scene video
data/rc_mir_erdan_ep01/output/scenes/ep01_shot01/scene.mp4
```

## Next Recommended Task

**RC2-PLAN1, not random feature work**

The next recommended task is to plan RC2 systematically, not to start random feature work. See `docs/RC2_BACKLOG.md` for the planned RC2 improvements.

### RC2-PLAN1 Steps

1. **Prioritize backlog items** - Review `docs/RC2_BACKLOG.md` and prioritize based on impact and dependencies
2. **Design RC2 architecture** - Design how RC2 will build upon RC-FINAL1
3. **Define RC2 acceptance criteria** - Define what RC2 must achieve to be accepted
4. **Create RC2 implementation plan** - Create a detailed implementation plan
5. **Create new project root** - Use a separate project root for RC2 (e.g., `data/rc2_mir_erdan_ep01`)

### Do Not Start Without Planning

Do not start implementing RC2 features without completing RC2-PLAN1 first. Random feature work without planning will:
- Break reproducibility
- Create inconsistent artifacts
- Make validation difficult
- Waste time on low-priority items

## Handoff Checklist

- ✅ RC-FINAL1 is accepted
- ✅ RC-FINAL1 is frozen
- ✅ All artifacts validate (67/67)
- ✅ All tests pass (139/139)
- ✅ Final state is terminal (episode_rendered)
- ✅ Known limitations are documented
- ✅ Freeze document exists
- ✅ RC2 backlog exists
- ✅ Handoff document exists
- ✅ Proof artifacts are in stable location
- ✅ Validation script exists
- ✅ Runbook exists

## Handoff Confirmation

**RC-FINAL1 is handed off**

The RC-FINAL1 proof pack is frozen and handed off for RC2 planning. Do not modify frozen artifacts. Start with RC2-PLAN1, not random feature work.

## Contact

For questions about RC-FINAL1:
- Review `docs/README_RUNBOOK.md` for inspection instructions
- Review `docs/KNOWN_LIMITATIONS.md` for limitations
- Review `docs/RC2_BACKLOG.md` for RC2 planning
- Run `scripts/validate_rc_artifacts.py` to verify artifact integrity
