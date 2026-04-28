# Orchestrator Routing Contract

## Overview
This document defines the routing logic for the orchestrator. The orchestrator reads production cards, determines blocked states, routes work to appropriate roles, prevents downstream execution, and provides route preview output.

## How the Orchestrator Reads Cards

### Card Loading
1. **Scan project directory:** Recursively scan for all card JSON files
2. **Parse card schemas:** Validate each card against its type schema
3. **Build dependency graph:** Map all card references and dependencies
4. **Load card states:** Read current state of each card (Pending, Draft, Complete, Approved, Blocked)

### Card Validation
For each card, the orchestrator validates:
- **Completeness:** All required fields populated
- **Reference validity:** All referenced card IDs exist
- **Dependency satisfaction:** All dependency cards are in "Approved" state
- **Schema compliance:** Card matches expected schema for its type

### State Aggregation
The orchestrator aggregates:
- **Project state:** Overall pipeline state (Pre-Production, Asset-Ready, Workflow-Ready, Generation-Ready, etc.)
- **Role workload:** How many cards each role owns and their states
- **Blocker tree:** Which cards are blocking which downstream work
- **Critical path:** Minimum set of cards that must complete to unblock generation

## How the Orchestrator Determines Blocked State

### Block Detection Rules

#### 1. Missing Card Block
**Condition:** Required card type does not exist for context
**Example:** ShotCard exists but CharacterCard is missing
**Block:** Shot generation blocked
**Route to:** Character Director

#### 2. Incomplete Card Block
**Condition:** Card exists but required fields are empty
**Example:** CharacterCard exists but visual_references is empty
**Block:** Card approval blocked
**Route to:** Card owning role

#### 3. Reference Invalid Block
**Condition:** Card references non-existent card ID
**Example:** ShotCard references CharacterCard ID that doesn't exist
**Block:** Card approval blocked
**Route to:** Card owning role

#### 4. Dependency Not Approved Block
**Condition:** Card references dependency that is not in "Approved" state
**Example:** ShotCard references CharacterCard that is only "Draft"
**Block:** Card approval blocked
**Route to:** Dependency owning role

#### 5. QA Failure Block
**Condition:** QA check fails for generated artifact
**Example:** Identity QA fails for generated frames
**Block:** Downstream work blocked
**Route to:** Role responsible for fixing (Character Director + Workflow TD for identity issues)

#### 6. Resource Constraint Block
**Condition:** Required resources unavailable (GPU, storage, etc.)
**Example:** GPU memory insufficient for workflow
**Block:** Generation blocked
**Route to:** Executive Producer for resource allocation

### Blocker Tree Construction
The orchestrator builds a blocker tree:
```
Generation Blocked
├── ShotCard [shot_001] Blocked
│   └── CharacterCard [char_mir] Not Approved
│       └── visual_references Empty → Route to Character Director
└── ShotCard [shot_002] Blocked
    └── EnvironmentCard [env_forest] Not Approved
        └── visual_references Empty → Route to Environment Director
```

## How the Orchestrator Chooses Next Responsible Role

### Routing Decision Matrix

| Missing/Blocked Element | Route To | Reason |
|------------------------|----------|--------|
| ProjectCard | Executive Producer | Project not defined |
| EpisodeCard | Director | Episode not defined |
| ScenarioCard | Screenwriter | Scenario not defined |
| ShotCard | Shot Designer | Shot not defined |
| CharacterCard missing | Character Director | Character asset needed |
| CharacterCard incomplete | Character Director | Character needs completion |
| CharacterCard not approved | Character Director | Character needs approval |
| EnvironmentCard missing | Environment Director | Environment asset needed |
| EnvironmentCard incomplete | Environment Director | Environment needs completion |
| EnvironmentCard not approved | Environment Director | Environment needs approval |
| LightingCard missing | Cinematographer | Lighting needed |
| LightingCard incomplete | Cinematographer | Lighting needs completion |
| CameraCard missing | Cinematographer | Camera needed |
| CameraCard incomplete | Cinematographer | Camera needs completion |
| StyleCard missing | Director | Style needed |
| StyleCard incomplete | Director | Style needs completion |
| WardrobeCard missing | Wardrobe Director | Wardrobe needed |
| PropCard missing | Environment Director | Prop needed |
| VoiceCard missing | Audio Director | Voice needed |
| WorkflowRecipeCard missing | Workflow TD | Workflow needed |
| WorkflowRecipeCard not approved | Workflow TD | Workflow needs approval |
| Identity QA failed | Character Director + Workflow TD | Identity issue needs joint resolution |
| Frame QC failed (quality) | Workflow TD | Technical quality issue |
| Frame QC failed (composition) | Shot Designer | Composition issue |
| Video duration mismatch | Video Agent + Editor | Timing issue |
| Audio sync failure | Audio Agent + Video Agent | Sync issue |
| All cards approved | Image Generation Agent | Generation can proceed |

### Routing Priority
When multiple blockers exist, the orchestrator routes to:
1. **Root blockers first:** Resolve upstream dependencies before downstream
2. **Critical path first:** Cards on critical path to generation
3. **Role workload balance:** Distribute work across roles
4. **Earliest deadline:** Prioritize time-sensitive work

### Routing Output Format
The orchestrator produces a routing decision:
```json
{
  "route_to": "Character Director",
  "card_id": "char_mir",
  "action": "complete",
  "reason": "CharacterCard visual_references is empty",
  "blocking_downstream": ["shot_001", "shot_002"],
  "priority": "high"
}
```

## How the Orchestrator Prevents Downstream Execution

### Prevention Mechanisms

#### 1. State Gate Enforcement
- **Rule:** Downstream work cannot start until upstream card is "Approved"
- **Implementation:** Orchestrator checks card state before routing
- **Example:** Image Generation Agent cannot start if ShotCard is not "Approved"

#### 2. Dependency Validation
- **Rule:** All references must be satisfied before card approval
- **Implementation:** Orchestrator validates reference completeness
- **Example:** ShotCard cannot be "Approved" if CharacterCard is missing

#### 3. QA Gate Enforcement
- **Rule:** Failed QA blocks downstream work
- **Implementation:** Orchestrator tracks QA results and blocks routes
- **Example:** Video compilation blocked if frame QA failed

#### 4. Resource Gate Enforcement
- **Rule:** Insufficient resources block generation
- **Implementation:** Orchestrator checks resource availability
- **Example:** GPU memory check before routing to Image Generation Agent

### Prevention Examples

#### Example 1: Missing Character Card
```
State:
- ShotCard [shot_001]: Complete (references char_mir)
- CharacterCard [char_mir]: MISSING

Orchestrator Action:
- Block ShotCard approval
- Route to Character Director
- Prevent Image Generation Agent execution
```

#### Example 2: Identity QA Failure
```
State:
- ShotCard [shot_001]: Approved
- CharacterCard [char_mir]: Approved
- Generation: Complete
- Identity QA: FAILED

Orchestrator Action:
- Block video compilation
- Route to Character Director + Workflow TD
- Prevent Video Agent execution
```

#### Example 3: Workflow Not Approved
```
State:
- ShotCard [shot_001]: Approved
- All asset cards: Approved
- WorkflowRecipeCard: DRAFT (not approved)

Orchestrator Action:
- Block generation
- Route to Workflow TD
- Prevent Image Generation Agent execution
```

## Route Preview Output Format

### JSON Structure
```json
{
  "project_state": "Generation-Ready",
  "overall_status": "blocked",
  "total_cards": 45,
  "cards_by_state": {
    "pending": 5,
    "draft": 8,
    "complete": 12,
    "approved": 15,
    "blocked": 5
  },
  "critical_path": [
    "char_mir",
    "env_forest",
    "shot_001",
    "shot_002"
  ],
  "blockers": [
    {
      "blocked_card": "shot_001",
      "blocked_card_type": "ShotCard",
      "reason": "CharacterCard [char_mir] not approved",
      "blocking_card": "char_mir",
      "blocking_card_type": "CharacterCard",
      "route_to": "Character Director",
      "action": "approve",
      "priority": "high"
    },
    {
      "blocked_card": "shot_002",
      "blocked_card_type": "ShotCard",
      "reason": "EnvironmentCard [env_forest] visual_references empty",
      "blocking_card": "env_forest",
      "blocking_card_type": "EnvironmentCard",
      "route_to": "Environment Director",
      "action": "complete",
      "priority": "high"
    }
  ],
  "role_workload": {
    "Character Director": {
      "total_cards": 3,
      "pending": 1,
      "draft": 1,
      "approved": 1
    },
    "Environment Director": {
      "total_cards": 2,
      "pending": 0,
      "draft": 1,
      "approved": 1
    },
    "Workflow TD": {
      "total_cards": 1,
      "pending": 0,
      "draft": 1,
      "approved": 0
    }
  },
  "next_actions": [
    {
      "sequence": 1,
      "role": "Character Director",
      "card_id": "char_mir",
      "action": "approve",
      "unblocks": ["shot_001", "shot_003"]
    },
    {
      "sequence": 2,
      "role": "Environment Director",
      "card_id": "env_forest",
      "action": "complete",
      "unblocks": ["shot_002"]
    },
    {
      "sequence": 3,
      "role": "Workflow TD",
      "card_id": "workflow_main",
      "action": "approve",
      "unblocks": ["shot_001", "shot_002", "shot_003"]
    }
  ],
  "ready_for_generation": false,
  "ready_cards": ["shot_004"],
  "generation_queue": []
}
```

### CLI Output Format
```
PROJECT STATE: BLOCKED
Overall Status: 3 blockers preventing generation

CRITICAL PATH (4 cards):
  1. char_mir [CharacterCard] - BLOCKED
  2. env_forest [EnvironmentCard] - BLOCKED
  3. shot_001 [ShotCard] - BLOCKED
  4. shot_002 [ShotCard] - BLOCKED

BLOCKERS:
  [HIGH] shot_001 blocked: CharacterCard [char_mir] not approved
         → Route to: Character Director
         → Action: approve card

  [HIGH] shot_002 blocked: EnvironmentCard [env_forest] visual_references empty
         → Route to: Environment Director
         → Action: complete card

  [MEDIUM] shot_003 blocked: WorkflowRecipeCard not approved
         → Route to: Workflow TD
         → Action: approve card

NEXT ACTIONS (in order):
  1. Character Director → approve char_mir (unblocks: shot_001, shot_003)
  2. Environment Director → complete env_forest (unblocks: shot_002)
  3. Workflow TD → approve workflow_main (unblocks: shot_001, shot_002, shot_003)

ROLE WORKLOAD:
  Character Director: 3 cards (1 pending, 1 draft, 1 approved)
  Environment Director: 2 cards (0 pending, 1 draft, 1 approved)
  Workflow TD: 1 card (0 pending, 1 draft, 0 approved)

READY FOR GENERATION: NO
Ready cards: shot_004
Generation queue: []
```

## Special Routing Cases

### Circular Dependencies
**Detection:** Orchestrator detects when Card A depends on Card B, and Card B depends on Card A
**Action:** Flag as manual resolution required, escalate to Director
**Route:** Director must break circular dependency by restructuring

### Multiple Owners
**Detection:** Card has conflicting ownership claims
**Action:** Flag as manual resolution required, escalate to Director
**Route:** Director must assign single owner

### Orphaned Cards
**Detection:** Card exists but no other cards reference it
**Action:** Flag for review (may be intentional or error)
**Route:** No automatic routing, manual review required

### Stale Cards
**Detection:** Card is "Approved" but referenced cards have been modified
**Action:** Flag card for re-approval
**Route:** Back to owning role for re-approval

## Orchestrator Constraints

### What the Orchestrator Cannot Do
- **Cannot modify cards:** Only reads card state
- **Cannot approve cards:** Only routes to owning role for approval
- **Cannot execute workflows:** Only routes to generation agents
- **Cannot make creative decisions:** Only makes routing decisions
- **Cannot override role gates:** Respects all role blocking capabilities
- **Cannot create cards:** Only detects missing cards and routes to owning role

### Orchestrator Guarantees
- **Deterministic routing:** Same input always produces same routing decision
- **Complete blocker detection:** All blockers are identified before routing
- **No downstream execution without approval:** Strict gate enforcement
- **Audit trail:** All routing decisions are logged
- **State consistency:** Card states are validated before use

## Integration Points

### Card Schema Validation
Orchestrator integrates with card schema validation system to ensure:
- Cards match expected schema for their type
- Required fields are present
- Field types are correct
- Reference IDs are valid format

### QA System Integration
Orchestrator integrates with QA system to:
- Receive QA results
- Update card states based on QA outcomes
- Route failed artifacts to appropriate roles
- Block downstream work on QA failure

### Resource Monitoring Integration
Orchestrator integrates with resource monitoring to:
- Check GPU availability before routing to generation
- Check storage availability before generation
- Route to Executive Producer if resources insufficient

### Workflow Execution Integration
Orchestrator integrates with workflow execution to:
- Receive generation status updates
- Update card states on generation completion
- Route failures back to appropriate roles
- Queue generation work when ready
