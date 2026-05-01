# COMBINE Internal Multi-Agent Architecture

## Final Runtime

The final runtime consists of:
- **Operator**: Human operator who provides briefs, reviews outputs, and makes acceptance decisions
- **Combine**: Internal multi-agent orchestrator that manages state, routes, and execution

## Windsurf Role

Windsurf is a **temporary build-helper only** during development:
- Allowed: Edit code, run CLI, return logs/proof, commit/push
- Forbidden: Orchestrator, production decision-maker, QA agent, director, source of state transitions
- Final runtime must NOT require Windsurf

## Internal Orchestrator Role

The internal orchestrator is responsible for:
- State machine management and transitions
- Route classification and routing decisions
- Stage execution coordination
- Artifact ledger management
- Enforcing gates and forbidden transitions

## Role Agents Map

The orchestrator coordinates with role agents for:
- Route classification (determines route family from brief)
- Production planning (creates production plan from route + brief)
- Workflow planning (selects ComfyUI workflows for route)
- Generation authorization (validates preflight before generation)
- Visual QA (assesses generated assets)
- Assembly (combines assets into final output)

Role agents are internal components, not external services.

## State Machine Ownership

The state machine is owned by the internal orchestrator:
- All state transitions are validated against the universal state machine
- No external handoff as production brain
- State transitions are deterministic and auditable

## Artifact/Ledger Ownership

The orchestrator manages:
- Artifact index (tracks all generated assets)
- Ledger events (records all state transitions and stage executions)
- No external ledger dependency

## Gates and Forbidden Transitions

### Forbidden Transitions
- Generation cannot happen before preflight/authorization
- QA cannot happen before generated artifacts exist
- Assembly cannot happen before accepted visuals/assets
- Final export cannot happen before final QC

### Gates
- Each stage must complete successfully before transition
- Manual review gates exist at critical points
- Operator approval required for final acceptance

## No External Handoff

The orchestrator does NOT:
- Hand off to external services as production brain
- Require external orchestration systems
- Depend on external state management

## No Route-Specific Core Assumptions

The core orchestrator is universal:
- No hardcoded UGC route
- No hardcoded Meta/Ads route
- No hardcoded portrait route
- No hardcoded product route
- All route families are treated equally
- Custom routes are supported

Route-specific logic exists only in:
- Route family policies
- Route-specific stage implementations
- Optional route overlays

## Architecture Principles

1. **Universal Core**: Core orchestrator works for all route families
2. **Anti-Anchor**: No single use case is treated as universal default
3. **State-Driven**: All execution is driven by state machine
4. **Artifact-Centric**: All decisions are based on artifact state
5. **Operator-in-the-Loop**: Human operator makes final acceptance decisions
6. **No External Dependencies**: Final runtime does not require Windsurf or external services
