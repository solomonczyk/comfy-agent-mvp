# Production Cards Implementation Plan

## Overview
This document defines the implementation phases for production cards, from architecture freeze to integration with existing multi-shot state. The plan prioritizes architecture definition before code implementation to prevent repeated generation loops.

## Phase 1: Architecture Docs Freeze Only

**Goal:** Complete and freeze all architecture documentation before any code implementation.

**Deliverables:**
- PRODUCTION_OPERATING_MODEL.md ✓
- PRODUCTION_ASSET_TAXONOMY.md ✓
- ROLE_OWNERSHIP_AND_GATES.md ✓
- ORCHESTRATOR_ROUTING_CONTRACT.md ✓
- PRODCARDS_IMPLEMENTATION_PLAN.md (this document)

**What to Implement:**
- Documentation only
- No code changes
- No schema definitions
- No CLI tools

**What Not to Implement Yet:**
- Card schema JSON files
- Validation code
- Routing logic code
- CLI tools
- Integration with existing state

**Risks:**
- Low risk (documentation only)
- Architecture may need refinement based on feedback

**Acceptance Criteria:**
- All 5 architecture documents created
- Documents reviewed and approved
- No code changes committed
- Architecture frozen for Phase 2

**Success Metrics:**
- Clear separation of concerns defined
- Role ownership unambiguous
- Routing logic complete
- Implementation path clear

---

## Phase 2: Card Schemas + Project Template Folders

**Goal:** Define JSON schemas for all 15 card types and create project folder templates.

**Deliverables:**
- JSON schema files for all 15 card types
- Project template folder structure
- Example card files for each type
- Schema validation documentation

**What to Implement:**
- JSON Schema definitions for:
  - ProjectCard
  - EpisodeCard
  - ScenarioCard
  - ShotCard
  - CharacterCard
  - EnvironmentCard
  - LightingCard
  - CameraCard
  - StyleCard
  - WardrobeCard
  - PropCard
  - VoiceCard
  - WorkflowRecipeCard
  - QARequirementCard
  - ReleasePackageCard
- Folder structure templates:
  - `project_root/cards/`
  - `project_root/cards/project/`
  - `project_root/cards/episode/`
  - `project_root/cards/scenario/`
  - `project_root/cards/shot/`
  - `project_root/cards/asset/`
- Example card files with sample data

**What Not to Implement Yet:**
- Validation code
- Routing logic
- CLI tools
- Integration with existing multi-shot state
- Generation workflow integration

**Risks:**
- Medium risk (schema design decisions)
- Schema may need iteration based on usage
- Folder structure may need adjustment

**Acceptance Criteria:**
- All 15 card schemas defined and validated
- Schema files pass JSON Schema validation
- Example cards load successfully
- Folder structure documented
- No breaking changes to existing code

**Success Metrics:**
- Schemas are complete and consistent
- Example cards are valid
- Folder structure supports workflow
- Documentation clear

---

## Phase 3: Validation CLI

**Goal:** Create CLI tool to validate card completeness, references, and dependencies.

**Deliverables:**
- CLI command: `python -m app.cli validate-cards`
- Validation logic for:
  - Card completeness (required fields)
  - Reference validity (referenced cards exist)
  - Dependency satisfaction (upstream cards approved)
  - Schema compliance (card matches schema)
- Validation output in JSON and human-readable formats
- Error reporting with specific remediation guidance

**What to Implement:**
- Validation engine
- CLI interface
- JSON Schema validator integration
- Dependency graph builder
- Reference checker
- Error reporter

**What Not to Implement Yet:**
- Routing logic
- Orchestrator integration
- Generation workflow integration
- Multi-shot state migration

**Risks:**
- Medium risk (validation logic complexity)
- Edge cases in reference validation
- Performance on large projects

**Acceptance Criteria:**
- CLI validates all card types correctly
- Completeness checks work
- Reference validation works
- Dependency validation works
- Error messages are actionable
- Performance acceptable (< 5 seconds for 100 cards)

**Success Metrics:**
- Validation catches all defined error conditions
- False positive rate < 5%
- False negative rate = 0%
- Error messages guide users to fix issues

---

## Phase 4: Routing Preview CLI

**Goal:** Create CLI tool to show current pipeline state, blockers, and next actions.

**Deliverables:**
- CLI command: `python -m app.cli route-preview`
- Routing logic implementation
- Blocker detection
- Critical path analysis
- Role workload calculation
- Next action sequencing
- Output in JSON and human-readable formats

**What to Implement:**
- Routing engine
- Blocker tree construction
- Critical path algorithm
- Role workload tracker
- Next action sequencer
- CLI interface
- Output formatters

**What Not to Implement Yet:**
- Automatic routing (execution)
- Integration with generation agents
- Multi-shot state migration
- Web UI

**Risks:**
- High risk (routing logic complexity)
- Edge cases in dependency resolution
- Priority calculation accuracy

**Acceptance Criteria:**
- CLI shows accurate pipeline state
- Blocker detection complete
- Critical path correct
- Next actions sequenced logically
- Output matches contract specification
- Performance acceptable (< 5 seconds for 100 cards)

**Success Metrics:**
- Routing decisions are deterministic
- All blockers identified
- Critical path accurate
- Next actions are actionable

---

## Phase 5: Integration with Existing Multi-Shot State

**Goal:** Migrate existing RC2 multi-shot data to new card structure.

**Deliverables:**
- Migration script: `python scripts/migrate_to_prodcards.py`
- Migrated card files for RC2 multi-shot episode
- Validation report on migrated data
- Gap analysis (what data is missing)
- Manual completion guide

**What to Implement:**
- Migration logic
- Data extraction from existing structure
- Card creation from existing data
- Validation of migrated cards
- Gap detection
- Migration report

**What Not to Implement Yet:**
- Identity workflow repair
- Generation retry
- Production card execution

**Risks:**
- High risk (data migration complexity)
- Existing data may not map cleanly to new structure
- Missing data may require manual intervention
- Migration may be lossy

**Acceptance Criteria:**
- Migration script completes without errors
- Migrated cards pass validation
- Gap analysis complete
- Manual completion guide clear
- No data loss (or documented loss)

**Success Metrics:**
- Migration success rate > 90%
- Validation passes on migrated cards
- Gaps clearly identified
- Manual intervention minimized

---

## Phase 6: Identity Workflow Repair / Generation Retry

**Goal:** Use production cards to fix identity workflow issues and retry generation.

**Deliverables:**
- Fixed CharacterCard for Mir character
- Fixed WorkflowRecipeCard with approved identity workflow
- Validated complete card set for RC2 multi-shot
- Generation retry with new cards
- QA verification of retry results

**What to Implement:**
- CharacterCard completion (add missing references)
- WorkflowRecipeCard approval (identity workflow)
- Card validation
- Generation execution with validated cards
- QA verification

**What Not to Implement Yet:**
- Full production pipeline
- Web UI
- Automated release packaging

**Risks:**
- High risk (generation may still fail)
- Identity workflow may need further iteration
- Character Director approval required

**Acceptance Criteria:**
- CharacterCard complete and approved
- WorkflowRecipeCard complete and approved
- All prerequisite cards validated
- Generation succeeds
- Identity QA passes
- Multi-shot consistency verified

**Success Metrics:**
- Generation success rate > 95%
- Identity QA pass rate = 100%
- Multi-shot consistency verified
- RC2 multi-shot unblocked

---

## Implementation Order Rationale

### Why Architecture First?
- Prevents building on unclear requirements
- Reduces rework from architectural changes
- Enables early feedback on design
- Separates concerns before code

### Why Schemas Before Validation?
- Validation needs schemas to validate against
- Schemas define contract for all phases
- Early schema validation catches design issues

### Why Validation Before Routing?
- Routing needs validated cards to make decisions
- Validation ensures data quality before routing
- Clearer error messages from validation

### Why Routing Preview Before Integration?
- Routing logic is complex, needs independent testing
- Preview mode allows testing without side effects
- Integration can rely on proven routing logic

### Why Integration Before Retry?
- Integration validates architecture against real data
- Gaps identified during integration inform retry
- Retry benefits from complete card ecosystem

### Why Retry Last?
- Retry is highest risk (may still fail)
- Benefits from all previous phases
- Clear success criteria defined by architecture

## Risk Mitigation

### Phase 1 Risks
**Risk:** Architecture may need refinement
**Mitigation:** Plan for revision cycle, freeze only after review

### Phase 2 Risks
**Risk:** Schema design may need iteration
**Mitigation:** Use example cards to test schemas, allow schema versioning

### Phase 3 Risks
**Risk:** Validation edge cases
**Mitigation:** Comprehensive test suite, manual validation review

### Phase 4 Risks
**Risk:** Routing logic complexity
**Mitigation:** Unit test routing decisions, manual review of critical paths

### Phase 5 Risks
**Risk:** Data migration loss
**Mitigation:** Backup existing data, manual review of migrated cards

### Phase 6 Risks
**Risk:** Generation may still fail
**Mitigation:** Character Director approval required, fallback to manual review

## Success Criteria for Entire Plan

### Overall Success
- All phases completed in order
- No shortcuts or phase skipping
- Each phase passes acceptance criteria
- Architecture remains consistent through all phases
- RC2 multi-shot generation succeeds

### Failure Modes
- **Architecture revision required:** Return to Phase 1
- **Schema revision required:** Return to Phase 2
- **Validation issues:** Fix in Phase 3
- **Routing issues:** Fix in Phase 4
- **Migration issues:** Manual intervention in Phase 5
- **Generation failure:** Character Director review in Phase 6

### Rollback Plan
If any phase fails critically:
- Document failure reason
- Roll back to previous stable state
- Revise plan based on lessons learned
- Re-attempt failed phase with revised approach

## Timeline Estimate

- **Phase 1:** 1 day (documentation)
- **Phase 2:** 2-3 days (schemas + templates)
- **Phase 3:** 3-5 days (validation CLI)
- **Phase 4:** 5-7 days (routing CLI)
- **Phase 5:** 3-5 days (integration + migration)
- **Phase 6:** 5-10 days (repair + retry, depends on Character Director approval)

**Total:** 19-31 days (approximately 4-6 weeks)

## Dependencies

### External Dependencies
- Character Director approval (Phase 6)
- Executive Producer approval (Phase 1)
- Workflow TD approval (Phase 6)

### Internal Dependencies
- Each phase depends on completion of previous phases
- Phase 6 depends on all previous phases
- No phase can start before its predecessor completes

## Resource Requirements

### Personnel
- Architect/Developer (all phases)
- Character Director (Phase 6)
- Workflow TD (Phase 6)
- Executive Producer (Phase 1 review)

### Technical Resources
- Development environment
- Test data (RC2 multi-shot)
- ComfyUI instance (Phase 6)
- GPU resources (Phase 6)

## Next Steps

After architecture freeze (Phase 1):
1. Review architecture documents with stakeholders
2. Get approval to proceed to Phase 2
3. Begin schema definition
4. Set up validation test suite
