# RC2 Implementation Plan

## RC1 Frozen Baseline Summary

**RC1 Status**: ACCEPTED and FROZEN
**Project Root**: `f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01`
**Final State**: episode_rendered
**Expected Next Action**: none
**Validation**: 67/67 checks passed
**Tests**: 139/139 passed

**RC1 Capabilities**:
- Complete control flow from brief to final render
- Reference-locked character generation (SDXL)
- Frame generation with QC validation
- Scene assembly (single-frame video)
- QA review pipeline
- No-audio policy for RC scope
- State machine with ordered transitions
- Artifact validation and provenance tracking

**RC1 Limitations** (intentionally frozen):
- Audio stage completed by no-audio RC policy
- Final render output is final manifest, not full audio/video render
- Single-frame scene.mp4 created for RC proof
- Single shot, single episode scope
- Reference-locked character mode only
- GTX1060 hardware profile only

**DO NOT MUTATE RC1**: All artifacts in `data/rc_mir_erdan_ep01/` are frozen and must not be modified.

## Candidate RC2 Upgrades Evaluation

### 1. Real Audio Generation / attach_audio Production Path

**Priority**: HIGH
**Value**: HIGH - Addresses major RC1 limitation (no audio)
**Risk**: MEDIUM - Requires TTS integration, audio muxing, external dependencies
**Files Likely Touched**:
- `app/audio/mux.py` (existing)
- `app/audio/scene_audio.py` (existing)
- `app/control/handlers.py` (attach_audio handler)
- `app/cli.py` (attach_audio command)
- New: `app/audio/tts.py` (TTS integration)
- New: `app/audio/synthesis.py` (audio synthesis)

**Acceptance Criteria**:
- TTS synthesis produces audio files from script
- Audio duration matches scene duration
- Audio is correctly muxed with scene.mp4
- Audio quality validation passes
- Final MP4 includes audio track
- No fake audio claim in manifests

**Implementation Complexity**: HIGH
**Risks Mutating RC1**: LOW - Will use new project root (e.g., `data/rc2_mir_erdan_ep01`)
**Recommended Order**: 2nd (after Director-lite for better operator experience)

### 2. Real Final MP4 Render Instead of Final Manifest

**Priority**: HIGH
**Value**: HIGH - Addresses major RC1 limitation (no final MP4)
**Risk**: LOW - Uses existing scene.mp4, adds audio muxing if audio exists
**Files Likely Touched**:
- `app/control/handlers.py` (render_episode handler)
- `app/cli.py` (render_episode command)
- New: `app/video/render.py` (final MP4 rendering)
- New: `app/video/codec.py` (codec configuration)

**Acceptance Criteria**:
- Final MP4 file is produced (not just manifest)
- MP4 includes video track
- MP4 includes audio track (if audio exists)
- MP4 is playable in standard players
- MP4 meets quality specifications
- Final manifest references actual MP4 file

**Implementation Complexity**: MEDIUM
**Risks Mutating RC1**: LOW - Will use new project root
**Recommended Order**: 3rd (after audio production path)

### 3. Director-Lite Operator Command Layer

**Priority**: MEDIUM/HIGH
**Value**: HIGH - Improves operator experience, enables Windsurf-free operation
**Risk**: LOW - CLI interface only, no pipeline logic changes
**Files Likely Touched**:
- `app/cli.py` (add director-lite commands)
- New: `app/director/parser.py` (command parser)
- New: `app/director/commands.py` (command implementations)
- New: `app/director/history.py` (command history)
- New: `app/director/help.py` (help system)

**Acceptance Criteria**:
- Director-lite commands parse correctly
- Command syntax is intuitive
- Command help is comprehensive
- Commands validate before execution
- Command history is preserved
- Commands integrate with existing CLI
- No pipeline mutations

**Implementation Complexity**: MEDIUM
**Risks Mutating RC1**: NONE - Pure CLI interface, read-only operations
**Recommended Order**: 1st (low risk, high value, enables better operator experience for subsequent tasks)

### 4. Package/Export Proof Pack Command

**Priority**: MEDIUM
**Value**: MEDIUM - Improves reproducibility, enables sharing
**Risk**: LOW - Pure export command, read-only
**Files Likely Touched**:
- `app/cli.py` (add export command)
- New: `scripts/export_proof_pack.py` (export script)
- New: `app/export/packager.py` (packaging logic)

**Acceptance Criteria**:
- Proof packs can be exported to archive
- Export includes all required artifacts
- Export includes validation report
- Export includes runbook
- Export includes checksum verification
- Export is verifiable and reproducible

**Implementation Complexity**: LOW
**Risks Mutating RC1**: NONE - Read-only export of frozen artifacts
**Recommended Order**: 4th (utility improvement, not blocking)

### 5. Multi-Shot Episode Support

**Priority**: MEDIUM
**Value**: MEDIUM - Expands scope to realistic production
**Risk**: HIGH - Requires state machine redesign, complex orchestration
**Files Likely Touched**:
- `app/control/` (episode-level state machine)
- `app/agent/` (episode-level orchestration)
- New: `app/episode/orchestrator.py` (episode orchestrator)
- New: `app/episode/brief.py` (episode brief format)
- New: `app/episode/ledger.py` (episode ledger)

**Acceptance Criteria**:
- Multiple shots can be defined in episode brief
- Shots are processed in correct order
- Cross-shot consistency is validated
- Episode-level state is tracked
- Episode-level QA passes
- Episode-level ledger is maintained

**Implementation Complexity**: HIGH
**Risks Mutating RC1**: LOW - Will use new project root
**Recommended Order**: 5th (complex, requires stable single-shot baseline)

## Candidate Comparison Table

| Candidate | Priority | Value | Risk | Complexity | Mutates RC1? | Recommended Order |
|-----------|----------|-------|------|------------|--------------|-------------------|
| Director-Lite | MEDIUM/HIGH | HIGH | LOW | MEDIUM | NONE | 1st |
| Real Audio | HIGH | HIGH | MEDIUM | HIGH | LOW | 2nd |
| Real Final MP4 | HIGH | HIGH | LOW | MEDIUM | LOW | 3rd |
| Package/Export | MEDIUM | MEDIUM | LOW | LOW | NONE | 4th |
| Multi-Shot | MEDIUM | MEDIUM | HIGH | HIGH | LOW | 5th |

## Selected First RC2 Task

**RC2-DIRECTOR1 — Director-lite Operator CLI**

### Why Selected

1. **Low Risk**: Pure CLI interface, no pipeline logic changes, no risk to RC1 artifacts
2. **High Value**: Enables Windsurf-free operation, improves operator experience
3. **Foundation**: Better CLI commands will make subsequent RC2 tasks easier to test and operate
4. **Independence**: Does not depend on other RC2 features (audio, final MP4, multi-shot)
5. **Simplicity**: MEDIUM complexity, clear acceptance criteria, bounded scope

### Recommended First Task Options Comparison

**A. RC2-AUDIO1 (Real Audio)**
- Pros: Addresses major RC1 limitation
- Cons: HIGH complexity, MEDIUM risk, external dependencies (TTS), requires scene.mp4 with audio
- Verdict: Good but complex for first task

**B. RC2-RENDER1 (Real Final MP4)**
- Pros: Addresses major RC1 limitation, LOW risk
- Cons: Depends on audio being available first, less value without audio
- Verdict: Good second task after audio

**C. RC2-DIRECTOR1 (Director-lite CLI)**
- Pros: LOW risk, HIGH value, independent, improves operator experience
- Cons: Does not address audio/final MP4 limitations directly
- Verdict: **BEST FIRST TASK** - low risk, high value, enables better operations for subsequent tasks

## RC2-DIRECTOR1 Implementation Plan

### Task Name
RC2-DIRECTOR1 — Director-lite Operator Command Layer

### Goal
Provide a simplified operator command interface that enables Windsurf-free operation of the ComfyUI Agent pipeline.

### Non-Goals
- Full-blown director interface (Director-lite only)
- Production-grade video editing
- Real-time collaboration
- UI/dashboard (CLI-only)
- Pipeline logic changes (read-only commands only)

### Exact Boundary

**In Scope**:
- Command parser for director-lite syntax
- Command implementations for common operations:
  - `status` - Check pipeline state
  - `inspect` - Inspect artifacts
  - `validate` - Validate artifacts
  - `history` - Show command history
  - `help` - Show command help
- Command history tracking
- Command help system
- Integration with existing CLI
- Read-only operations only (no pipeline mutations)

**Out of Scope**:
- Pipeline execution commands (generate_frames, assemble_scene, etc.)
- Write operations on frozen RC1 artifacts
- UI/dashboard
- Real-time monitoring
- Multi-user collaboration
- Complex command scripting

### Acceptance Criteria

1. **Command Parsing**
   - Director-lite commands parse correctly
   - Invalid commands are rejected with helpful error messages
   - Command syntax is intuitive and consistent

2. **Command Implementations**
   - `status` command shows current pipeline state
   - `inspect` command shows artifact details
   - `validate` command runs artifact validation
   - `history` command shows command history
   - `help` command shows comprehensive help

3. **Command Help**
   - Help is available for all commands
   - Help includes syntax, examples, and parameters
   - Help is comprehensive and accurate

4. **Command History**
   - Command history is preserved across sessions
   - History can be viewed and searched
   - History is limited to reasonable size (e.g., 100 commands)

5. **Integration**
   - Director-lite commands integrate with existing CLI
   - Existing CLI commands continue to work
   - No breaking changes to existing CLI

6. **No Pipeline Mutations**
   - All director-lite commands are read-only
   - No commands modify frozen RC1 artifacts
   - No commands trigger pipeline actions

7. **Testing**
   - All commands have unit tests
   - Integration tests verify CLI integration
   - Manual testing verifies operator experience

### Implementation Steps

1. **Design Command Syntax**
   - Define director-lite command grammar
   - Design command help format
   - Design history storage format

2. **Implement Command Parser**
   - Create `app/director/parser.py`
   - Implement command parsing logic
   - Add error handling and validation

3. **Implement Commands**
   - Create `app/director/commands.py`
   - Implement `status` command
   - Implement `inspect` command
   - Implement `validate` command
   - Implement `history` command
   - Implement `help` command

4. **Implement History**
   - Create `app/director/history.py`
   - Implement history storage
   - Implement history retrieval
   - Implement history search

5. **Implement Help**
   - Create `app/director/help.py`
   - Implement help generation
   - Implement command-specific help
   - Implement examples

6. **Integrate with CLI**
   - Modify `app/cli.py` to add director-lite commands
   - Add director-lite command group
   - Ensure existing commands continue to work

7. **Write Tests**
   - Write unit tests for parser
   - Write unit tests for commands
   - Write integration tests for CLI
   - Write manual test plan

8. **Documentation**
   - Document command syntax
   - Document command usage
   - Document integration with existing CLI
   - Update README

### Files to Create

- `app/director/__init__.py`
- `app/director/parser.py`
- `app/director/commands.py`
- `app/director/history.py`
- `app/director/help.py`
- `tests/test_director_parser.py`
- `tests/test_director_commands.py`
- `tests/test_director_integration.py`

### Files to Modify

- `app/cli.py` (add director-lite command group)
- `README.md` (document director-lite commands)

### Rollback Plan

If RC2-DIRECTOR1 fails acceptance:
1. Revert changes to `app/cli.py`
2. Delete new `app/director/` directory
3. Delete new test files
4. Remove director-lite documentation from README
5. RC1 remains frozen and valid

Rollback is safe because:
- No RC1 artifacts are modified
- No pipeline logic is changed
- Changes are isolated to new code
- Existing CLI continues to work

### Proof Requirements

RC2-DIRECTOR1 must prove:
1. Director-lite commands work correctly
2. Commands integrate with existing CLI without breaking changes
3. Commands are read-only and do not mutate RC1 artifacts
4. Command history is preserved
5. Command help is comprehensive
6. All tests pass
7. RC1 validation still passes (67/67)
8. RC1 state is still terminal (episode_rendered)

### Validation Commands for RC2-DIRECTOR1

After implementation, verify:
```bash
# Test director-lite commands
python -m app director-lite status
python -m app director-lite inspect --artifact frames_manifest
python -m app director-lite validate
python -m app director-lite history
python -m app director-lite help

# Verify RC1 still frozen and valid
python -m app control-status --episode ep01 --shot shot01 --project-root "f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01" --json
python scripts/validate_rc_artifacts.py --project-root "f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01" --episode ep01 --shot shot01

# Verify tests still pass
python -m pytest tests/test_director_parser.py tests/test_director_commands.py tests/test_director_integration.py -q -s --tb=short
python -m pytest tests/test_action_runner.py tests/test_action_plan.py tests/test_control_status_cli.py tests/test_control_service.py tests/test_attach_audio.py tests/test_render_episode.py tests/test_shot_state_storage.py -q -s --tb=short
```

### Success Criteria

RC2-DIRECTOR1 is successful if:
- All acceptance criteria are met
- All tests pass
- RC1 validation still passes (67/67)
- RC1 state is still terminal (episode_rendered)
- No RC1 artifacts were modified
- Director-lite commands are intuitive and useful
- Documentation is complete and accurate

## Next Steps After RC2-DIRECTOR1

After RC2-DIRECTOR1 is accepted, proceed to:
1. RC2-AUDIO1 (Real audio generation)
2. RC2-RENDER1 (Real final MP4 render)
3. RC2-EXPORT1 (Package/export proof pack)
4. RC2-EPISODE1 (Multi-shot episode support)

Each subsequent RC2 task will build on the stable RC1 baseline and the Director-lite CLI for better operator experience.
