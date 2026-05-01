# COMBINE Master Plan V2

## V2 Goal

Create a universal internal multi-agent combiner that:
- Works across all route families (UGC, portrait, product, cinematic, etc.)
- Has no single-use-case anchoring in core
- Uses internal orchestrator for state management
- Requires only operator + combine in final runtime
- Does not depend on Windsurf in production

## D0-D14 Master Plan

### D0: Architecture Freeze (Current)
- Create architecture documentation
- Freeze Windsurf boundary
- Freeze anti-anchor route model
- Add internal orchestrator skeleton
- Add universal state machine draft
- Add route classifier skeleton
- Add CLI stubs (combine-status, combine-run-stage)
- Add state machine tests

### D1-D3: Role Contracts
- Define role agent interfaces
- Create role agent stubs
- Define role-to-stage mapping

### D4-D6: Brief → Route → Production Plan
- Implement brief parser
- Implement route classifier
- Implement production plan generator
- Add route-specific policies

### D7-D9: Prompt/Workflow/Preflight
- Implement prompt template system
- Implement workflow selector
- Implement preflight validation
- Add generation authorization

### D10-D11: Controlled Generation
- Implement generation stage
- Implement retry logic
- Implement generation quality gates

### D12: Visual QA/Operator Review/Retry Policy
- Implement visual QA stage
- Implement operator review interface
- Implement retry/correction policy

### D13: Assembly/Video/Pack
- Implement assembly stage
- Implement video rendering
- Implement final packaging

### D14: Unified Acceptance
- Implement final QC stage
- Implement operator acceptance
- Create acceptance test suite across route families

## Phase List

### Phase 1: Architecture Freeze
- Architecture documentation
- Windsurf boundary definition
- Anti-anchor route model
- Orchestrator skeleton
- State machine draft
- Route classifier skeleton
- CLI stubs
- State machine tests

### Phase 2: Orchestrator Skeleton
- Role contracts
- Role agent stubs
- Stage execution framework
- Artifact ledger
- State persistence

### Phase 3: Brief → Route → Production Plan
- Brief parsing
- Route classification
- Production plan generation
- Route-specific policies

### Phase 4: Prompt/Workflow/Preflight
- Prompt templates
- Workflow selection
- Preflight validation
- Generation authorization

### Phase 5: Controlled Generation
- Generation execution
- Retry logic
- Quality gates

### Phase 6: Visual QA/Operator Review/Retry Policy
- Visual QA
- Operator review
- Retry/correction policy

### Phase 7: Assembly/Video/Pack
- Asset assembly
- Video rendering
- Final packaging

### Phase 8: Unified Acceptance
- Final QC
- Operator acceptance
- Acceptance test suite

## Anti-Anchor Principle

The core orchestrator must NOT be anchored to:
- UGC
- Meta Ads
- Portrait
- Product cards
- Cinematic scene
- Any single route/use case

All route families are treated equally in the core.

## Route Families

Allowed route families for V2:
- portrait_character_identity
- product_visual
- ugc_testimonial
- platform_ad_creative
- social_short_vertical
- cinematic_scene
- educational_explainer
- image_to_video
- video_to_video
- batch_variations
- custom

## Acceptance Scenarios

Acceptance must be demonstrated across multiple route families:
- Portrait/character identity
- Product visual
- UGC/testimonial
- Platform ad creative
- Cinematic scene
- Custom route

No single route family is treated as the "default" or "primary" use case.
