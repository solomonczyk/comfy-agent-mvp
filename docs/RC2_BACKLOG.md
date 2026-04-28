# RC2 Backlog

## Overview

This backlog contains planned improvements for RC2 (Reference Implementation 2). These are post-RC improvements that build upon the frozen RC-FINAL1 baseline. Do not start RC2 features until RC-FINAL1 is frozen and accepted.

## RC2 Goals

RC2 aims to address the known limitations of RC-FINAL1 and demonstrate production-ready capabilities:
- Real audio generation and attachment
- Real final MP4 rendering
- Multi-shot episode support
- Improved operator interfaces
- Enhanced retry policies
- Multi-character support

## Backlog Items

### 1. Real Audio Generation / attach_audio Production Path

**Priority**: HIGH
**RC1 Limitation**: Audio stage completed by no-audio RC policy
**RC2 Goal**: Implement real TTS synthesis and audio muxing

**Tasks**:
- Integrate TTS engine (Silero or similar)
- Implement scene audio generation from script
- Implement audio-to-video synchronization
- Add audio quality validation
- Update attach_audio handler for production path
- Add audio configuration to prompt_pack.json

**Acceptance Criteria**:
- TTS synthesis produces audio files
- Audio is correctly muxed with scene.mp4
- Audio duration matches scene duration
- Audio quality validation passes
- Final MP4 includes audio track

### 2. Real Final MP4 Render Instead of Final Manifest

**Priority**: HIGH
**RC1 Limitation**: Final render output is final manifest, not full audio/video render
**RC2 Goal**: Produce actual MP4 file with audio

**Tasks**:
- Implement final MP4 rendering from scene.mp4 + audio
- Add video codec configuration
- Add bitrate/quality settings
- Implement final render validation
- Update render_episode handler for production path
- Add final render metadata to manifest

**Acceptance Criteria**:
- Final MP4 file is produced
- MP4 includes video and audio tracks
- MP4 is playable in standard players
- MP4 meets quality specifications
- Final manifest references actual MP4 file

### 3. Multi-Shot Episode Support

**Priority**: MEDIUM
**RC1 Limitation**: Single shot, single episode scope
**RC2 Goal**: Support multiple shots per episode

**Tasks**:
- Design multi-shot episode state machine
- Implement shot-level orchestration
- Add episode-level ledger
- Implement cross-shot consistency checks
- Add episode-level QA
- Design episode brief format

**Acceptance Criteria**:
- Multiple shots can be defined in episode brief
- Shots are processed in correct order
- Cross-shot consistency is validated
- Episode-level state is tracked
- Episode-level QA passes

### 4. Director-Lite Operator Command Layer

**Priority**: MEDIUM
**RC1 Limitation**: CLI-only interface
**RC2 Goal**: Provide simplified operator command interface

**Tasks**:
- Design director-lite command syntax
- Implement command parser
- Add command history
- Implement command help system
- Add command validation
- Integrate with existing CLI

**Acceptance Criteria**:
- Director-lite commands are intuitive
- Command syntax is documented
- Command help is comprehensive
- Commands validate before execution
- Command history is preserved

### 5. UI-Lite Dashboard

**Priority**: LOW
**RC1 Limitation**: CLI-only interface
**RC2 Goal**: Provide simple web dashboard for monitoring

**Tasks**:
- Design UI-lite dashboard layout
- Implement Flask/FastAPI backend
- Implement React/Vue frontend
- Add real-time status display
- Add artifact viewer
- Add simple control buttons

**Acceptance Criteria**:
- Dashboard displays pipeline state
- Dashboard shows artifact progress
- Dashboard allows simple operations
- Dashboard is responsive
- Dashboard is accessible

### 6. Stronger WorkflowGraphEditor

**Priority**: MEDIUM
**RC1 Limitation**: Basic workflow submission
**RC2 Goal**: Provide workflow editing and validation

**Tasks**:
- Design workflow graph editor UI
- Implement node drag-and-drop
- Implement connection editing
- Add workflow validation
- Add workflow templates
- Add workflow versioning

**Acceptance Criteria**:
- Workflows can be edited visually
- Workflow changes are validated
- Workflow templates are available
- Workflow versions are tracked
- Workflow editor is stable

### 7. Stronger RetryPolicy-Lite

**Priority**: MEDIUM
**RC1 Limitation**: Basic retry decision
**RC2 Goal**: Provide configurable retry policies

**Tasks**:
- Design retry policy DSL
- Implement policy parser
- Add policy templates
- Implement policy evaluation
- Add policy metrics
- Add policy testing

**Acceptance Criteria**:
- Retry policies are configurable
- Policy DSL is expressive
- Policy templates cover common cases
- Policy evaluation is correct
- Policy metrics are tracked

### 8. Multi-Character Proof Beyond Mira Fixture

**Priority**: LOW
**RC1 Limitation**: Reference-locked character mode only
**RC2 Goal**: Support multiple characters in scenes

**Tasks**:
- Design multi-character reference system
- Implement character registry expansion
- Add multi-character workflow templates
- Implement character interaction rules
- Add multi-character QA
- Test with multiple character fixtures

**Acceptance Criteria**:
- Multiple characters can be defined
- Characters interact correctly in scenes
- Multi-character workflows work
- Character registry is extensible
- Multi-character QA passes

### 9. Package/Export Proof Pack Command

**Priority**: LOW
**RC1 Limitation**: Manual artifact inspection
**RC2 Goal**: Provide automated proof pack export

**Tasks**:
- Design proof pack format
- Implement export command
- Add artifact packaging
- Add validation report generation
- Add runbook generation
- Add checksum verification

**Acceptance Criteria**:
- Proof packs can be exported
- Export includes all artifacts
- Export includes validation report
- Export includes runbook
- Export is verifiable

## RC2 Planning

### RC2-PLAN1
- Prioritize backlog items
- Design RC2 architecture
- Define RC2 acceptance criteria
- Create RC2 implementation plan

### RC2-Implementation
- Implement backlog items in priority order
- Test each item against acceptance criteria
- Update documentation
- Validate against RC-FINAL1 baseline

### RC2-Acceptance
- Run full test suite
- Validate all artifacts
- Create RC2 acceptance report
- Freeze RC2 as RC-FINAL2

## Dependencies

- All RC2 work depends on frozen RC-FINAL1
- Real audio depends on TTS engine integration
- Real final MP4 depends on real audio
- Multi-shot episode depends on shot-level stability
- UI-lite dashboard depends on stable backend API

## Non-Goals

These are explicitly out of scope for RC2:
- Full-blown director interface (Director-Lite only)
- Production-grade video editing (basic rendering only)
- Distributed rendering (single-machine only)
- Cloud deployment (local only)
- Real-time collaboration (single-operator only)

## Notes

- RC2 should maintain backward compatibility with RC-FINAL1 where possible
- RC2 artifacts should be stored in a separate project root (e.g., `data/rc2_mir_erdan_ep01`)
- RC2 should reuse RC-FINAL1 validation scripts where applicable
- RC2 should document all changes from RC-FINAL1
