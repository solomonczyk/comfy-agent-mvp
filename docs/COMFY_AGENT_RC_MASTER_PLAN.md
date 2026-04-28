# COMFY_AGENT_RC_MASTER_PLAN.md

## 0. Purpose of this document

This document is the master RC plan for the local reusable ComfyUI Agent system.

It defines:

- the final Release Candidate goal;
- the Golden Path that must work end-to-end;
- the architecture boundaries;
- the must-have components;
- the task blocks for implementation;
- the artifact contract;
- the error taxonomy;
- the acceptance gates;
- the definition of done;
- the scope cuts required to finish within the deadline.

This document is not a brainstorming note.  
It is the working execution plan for completing the project.

---

## 1. Final RC goal

The goal is to finish a **local reusable ComfyUI Agent RC**.

The system must allow the operator to initialize a project, describe characters and scene intent, generate frames through ComfyUI, validate results, retry safely when needed, continue through controlled pipeline actions, and inspect artifacts without relying on Windsurf for normal operation.

The system must not be a one-off Alya project.

Alya / Mir Erdan is the first real proof case, but the core system must be reusable for other characters and projects through configuration.

### Final target

```text
User / Operator
    ↓
Operator CLI / UI-lite
    ↓
ProducerDirectorAgent-lite
    ↓
ProjectProfile + PromptPack
    ↓
Preflight
    ↓
Reference staging
    ↓
WorkflowGraphEditor-lite
    ↓
ComfyUI submit
    ↓
Artifacts + observed settings
    ↓
QC
    ↓
RetryPolicy-lite
    ↓
Controlled downstream actions
    ↓
Final proof pack
```

---

## 2. What this project is

This project is:

```text
A local ComfyUI control-agent system that can:
- read project configuration;
- prepare references;
- build or patch ComfyUI workflows;
- validate graph correctness before submit;
- run controlled generation actions;
- collect artifacts;
- perform QC;
- decide retry/accept/reject;
- maintain ledger/state;
- expose operator commands;
- produce a reproducible proof pack.
```

---

## 3. What this project is not

This RC is not:

```text
- a full enterprise multi-agent platform;
- a universal natural-language workflow builder for every possible ComfyUI graph;
- a polished SaaS product;
- a complete UI dashboard platform;
- a full IPAdapter/InstantID character consistency system;
- a model training framework;
- a marketplace workflow engine;
- a Grafana/Prometheus monitoring stack;
- a Telegram bot;
- a RAG system.
```

Those can be future extensions.  
The RC must focus on a stable, reusable, demonstrable production path.

---

## 4. Golden Path

The Golden Path is the mandatory end-to-end scenario.

Every task must help this path work.

```text
init-project
→ project_profile.json
→ prompt_pack.json
→ agent preflight
→ stable dry proof
→ real generate_frames
→ artifact collection
→ QC
→ retry if needed
→ assemble_scene
→ qa_review
→ render/output if ready
→ final proof pack
```

If a task does not help the Golden Path, it goes to backlog.

---

## 5. RC Definition of Done

The project is considered RC-complete only if:

```text
[ ] Project can be initialized by command.
[ ] Agent can be used without Windsurf for normal operation.
[ ] ProjectProfile controls characters and references.
[ ] No character-specific hardcode remains in core code.
[ ] PromptPack is the source of truth for generation prompts.
[ ] Workflow can be safely edited and validated.
[ ] Preflight blocks invalid runtime before real submit.
[ ] Real generate_frames produces frame_count > 0.
[ ] QC rejects broken/contact-sheet/empty outputs.
[ ] Retry is bounded and logged.
[ ] Ledger and ArtifactIndex are complete.
[ ] Operator can inspect status and artifacts.
[ ] Controlled downstream actions work or limitations are documented.
[ ] Runbook and acceptance report exist.
[ ] A second dummy character/profile test proves portability.
[ ] Final proof pack is reproducible from stable project root.
```

---

## 6. Core architecture

### 6.1 High-level architecture

```text
Operator CLI / UI-lite
        ↓
ProducerDirectorAgent-lite
        ↓
ProjectBootstrap / ProjectProfileResolver
        ↓
PromptPackBuilder + PromptPackValidator
        ↓
PreflightService
        ↓
ReferenceStagingStrategy
        ↓
ComfyNodeSchemaRegistry
        ↓
WorkflowGraphEditor-lite
        ↓
WorkflowPatcher / ComfySubmitter
        ↓
ComfyUI
        ↓
ArtifactCollector
        ↓
WorkflowSettingsExtractor
        ↓
QCService
        ↓
RetryPolicy-lite
        ↓
ShotLedger / ControlStatus
        ↓
ArtifactIndex
        ↓
Operator Preview / Runbook
```

---

## 7. Mandatory components

### 7.1 ProjectProfile

Project-specific data must live in `project_profile.json`, not in Python core code.

ProjectProfile must describe:

- project id;
- characters;
- aliases;
- reference image paths;
- reference role;
- clean reference strategy;
- default generation settings;
- recipe mapping if needed.

Example:

```json
{
  "project_id": "mir_erdan",
  "characters": {
    "Alya": {
      "character_id": "alya",
      "name": "Alya",
      "aliases": ["Аля", "alya", "Alya"],
      "reference_image_path": "F:\\VideoProjects\\МИР\\Эрдан\\референсы\\Аля.png",
      "reference_role": "character_identity",
      "clean_reference": {
        "strategy": "single_panel_crop",
        "output_name": "alya_clean_single_portrait_v2_480x640.png",
        "target_width": 480,
        "target_height": 640,
        "crop_box_mode": "relative",
        "crop_box": [0.0, 0.0, 0.3333, 0.42],
        "centering": [0.5, 0.35],
        "force_regenerate": true
      }
    }
  }
}
```

A new character must be addable through config without editing core code.

---

### 7.2 PromptPack

PromptPack is the source of truth for generation intent.

It must include:

- episode id;
- shot id;
- generation mode;
- character name;
- reference image path;
- reference role;
- positive prompt;
- negative prompt;
- width;
- height;
- steps;
- denoise;
- optional recipe hints.

Example:

```json
{
  "episode_id": "ep01",
  "shot_id": "shot01",
  "generation_mode": "reference_locked",
  "character_name": "Alya",
  "characters": ["Alya"],
  "reference_image_path": "F:\\VideoProjects\\МИР\\Эрдан\\референсы\\Аля.png",
  "reference_role": "character_identity",
  "positive_prompt": "vertical portrait composition, ordinary tired young woman 24 years old...",
  "negative_prompt": "glamour, fashion model, beauty portrait, studio portrait...",
  "denoise": 0.5,
  "width": 480,
  "height": 640,
  "steps": 16
}
```

Forbidden production placeholders:

```text
beautiful anime girl
detailed, high quality as only positive content
blurry as only negative prompt
empty positive_prompt
empty negative_prompt
```

---

### 7.3 ReferenceStagingStrategy

Reference staging must be generic and strategy-driven.

Core code must not contain Alya-specific logic such as:

```text
if character == "Alya":
    crop top-left panel
```

Instead:

```text
project_profile.character.clean_reference.strategy
→ create_clean_reference_from_strategy()
```

Required initial strategy:

```text
single_panel_crop
```

Behavior:

```text
- open original image
- compute crop_box from profile
- crop selected panel
- ImageOps.fit to target dimensions
- save using output_name from profile
- return clean reference path
```

Original reference path must be preserved for traceability.

LoadImage must use clean/staged project-local path when required.

---

### 7.4 WorkflowGraphEditor-lite

The system must safely edit workflow JSON.

Minimum required methods:

```text
find_nodes(class_type)
set_input(node_id, input_name, value)
connect(from_node, output_index, to_node, input_name)
add_node(class_type, inputs)
replace_node_type(node_id, new_class_type, inputs)
remove_if_unreferenced(node_id)
validate_no_dangling_links()
validate_contract()
```

This must support known production edits:

```text
- set checkpoint;
- set prompt text;
- set sampler settings;
- replace missing resize node with available resize node;
- connect LoadImage → ImageScale → VAEEncode → KSampler;
- ensure EmptyLatentImage is not active source in reference_locked mode.
```

---

### 7.5 ComfyNodeSchemaRegistry

The system must read ComfyUI `object_info` and use actual node schemas.

Required:

```text
- check ComfyUI availability;
- read object_info;
- confirm node class exists;
- inspect required inputs;
- choose ImageScale if ImageResize is unavailable;
- block if no valid resize node exists.
```

Never guess node field names when object_info is available.

---

### 7.6 PreflightService

Before real execution, preflight must verify:

```text
- ComfyUI is reachable;
- object_info is available;
- required nodes exist;
- checkpoint exists;
- project_profile is valid;
- prompt_pack is valid;
- reference image exists;
- clean reference exists or can be generated;
- workflow graph is valid;
- no unsafe production paths exist;
- no placeholder prompts remain.
```

Preflight must return structured JSON:

```json
{
  "status": "READY",
  "checks": {
    "comfyui_alive": true,
    "object_info": true,
    "required_nodes": true,
    "checkpoint": true,
    "project_profile": true,
    "prompt_pack": true,
    "reference": true,
    "workflow_graph": true,
    "path_safety": true
  }
}
```

If blocked, it must return a clear blocker code.

---

### 7.7 ProducerDirectorAgent-lite

The project must be usable without Windsurf.

The Director-lite must:

```text
- accept a goal;
- inspect current state;
- run preflight;
- choose next allowed action;
- execute one action at a time;
- collect artifacts;
- run QC;
- decide accept/retry/reject/next;
- write ledger;
- return operator-friendly status.
```

This is not a full autonomous multi-agent swarm.  
It is a controlled orchestrator with role services.

Recommended internal roles:

```text
ScriptwriterService
PromptCompilerService
WorkflowEngineerService
QCReviewerService
RetryStrategistService
RenderControllerService
```

---

### 7.8 Operator CLI

Minimum CLI commands:

```powershell
python -m app init-project --project-root "..." --project-id "..."

python -m app agent-status --project-root "..."

python -m app agent-preflight --project-root "..."

python -m app agent-next --project-root "..."

python -m app agent-run --project-root "..." --goal "..."

python -m app agent-retry --project-root "..."

python -m app agent-resume --project-root "..."

python -m app agent-artifacts --project-root "..."
```

The CLI must return:

```text
status
current_state
next_action
blockers
artifact links
recommended next command
```

UI-lite is desirable, but CLI is mandatory.

---

### 7.9 QCService

Minimum QC checks:

```text
- file exists;
- image readable;
- dimensions valid;
- not black frame;
- not contact sheet/grid;
- no UI strip/text panel;
- artifact severity;
- frame_count > 0 for generation outputs.
```

QC verdicts:

```text
accept
warn
retry_candidate
reject
```

QC must write:

```text
qc_report.json
```

---

### 7.10 RetryPolicy-lite

Retry must be deterministic, bounded, and logged.

Default:

```text
max_retries = 2
```

Retry may change only controlled fields:

```text
- seed;
- denoise within allowed range;
- prompt additions;
- negative prompt additions;
- approved reference strategy;
- approved workflow fallback.
```

Structural failures must block instead of retrying:

```text
- missing node;
- missing checkpoint;
- invalid workflow graph;
- dirty reference;
- invalid prompt pack.
```

Retry must write:

```text
retry_decision.json
```

---

### 7.11 ArtifactIndex

The system must maintain:

```text
artifact_index.json
```

Example:

```json
{
  "episode_id": "ep01",
  "shot_id": "shot01",
  "state": "frames_generated",
  "artifacts": {
    "project_profile": "output/control/project_profile.json",
    "prompt_pack": "output/control/prompt_pack.json",
    "preflight": "output/control/ep01_shot01_preflight.json",
    "action_plan": "output/control/ep01_shot01_action_plan.json",
    "submitted_workflow": "output/control/ep01_shot01_submitted_workflow.json",
    "observed_settings": "output/control/ep01_shot01_observed_settings.json",
    "frames_manifest": "output/control/frames_manifest.json",
    "qc_report": "output/control/qc_report.json",
    "retry_decision": "output/control/retry_decision.json",
    "ledger": "output/control/shot_ledger.json",
    "preview_frame": "output/frames/ep01_shot01/frame_0001.png"
  }
}
```

---

### 7.12 Ledger

Every action must write ledger records.

Ledger must show:

```text
- action requested;
- action allowed/blocked;
- handler invoked;
- result;
- artifact paths;
- state transition;
- failure/retry reason;
- no downstream action evidence.
```

---

## 8. Artifact contract

For each shot, the following artifacts should exist when relevant:

```text
output/control/project_profile.json
output/control/prompt_pack.json
output/control/ep01_shot01_preflight.json
output/control/ep01_shot01_action_plan.json
output/control/ep01_shot01_submitted_workflow.json
output/control/ep01_shot01_observed_settings.json
output/control/frames_manifest.json
output/control/qc_report.json
output/control/retry_decision.json
output/control/artifact_index.json
output/control/shot_ledger.json
output/frames/<episode>_<shot>/...
output/scenes/...
```

Final production proof must not contain:

```text
AppData
Temp
pytest-of-*
temporary fixture paths
```

---

## 9. Error taxonomy

Use structured statuses and blocker codes.

### General statuses

```text
READY
DONE
PARTIAL
BLOCKED
FAILED
RETRY_CANDIDATE
MAX_RETRIES_REACHED
```

### Blocker codes

```text
BLOCKED_BY_INVALID_PROJECT_PROFILE
BLOCKED_BY_INVALID_PROMPT_PACK
BLOCKED_BY_PLACEHOLDER_PROMPT
BLOCKED_BY_MISSING_REFERENCE
BLOCKED_BY_DIRTY_REFERENCE
BLOCKED_BY_COMFYUI_DOWN
BLOCKED_BY_MISSING_NODE
BLOCKED_BY_MISSING_CHECKPOINT
BLOCKED_BY_INVALID_WORKFLOW_GRAPH
BLOCKED_BY_UNSAFE_PATH
BLOCKED_BY_DOWNSTREAM_ACTION
```

### Failure codes

```text
FAILED_COMFY_SUBMIT
FAILED_FRAME_COUNT_ZERO
FAILED_QC_REJECT
FAILED_ARTIFACT_MISSING
FAILED_OBSERVED_SETTINGS_MISSING
```

Every blocked or failed result must include:

```text
status
reason
blocking file/path/node if relevant
recommended next action
```

---

## 10. No silent fallback rule

The system must not silently fallback.

Forbidden:

```text
checkpoint missing → silently use another checkpoint
node missing → silently use random node
prompt missing → use placeholder
reference dirty → submit anyway
recipe validator fails → continue as if valid
```

Allowed:

```text
explicit fallback with proof
or structured BLOCKED status
```

---

## 11. Release Gate Matrix

| Block | Required proof |
| --- | --- |
| ProjectProfile | actual project_profile.json + tests |
| ReferenceStrategy | clean reference path + preview + no hardcode proof |
| PromptPack | actual prompt_pack + CLIPTextEncode node proof |
| WorkflowEditor | submitted_workflow before/after + graph validation |
| NodeSchemaRegistry | object_info/schema proof |
| Preflight | structured READY/BLOCKED JSON |
| Real generation | frames_manifest with frame_count > 0 |
| QC | qc_report.json |
| Retry | retry_decision.json + ledger record |
| Agent CLI | actual command output |
| ArtifactIndex | artifact_index.json |
| Final RC | ACCEPTANCE_REPORT.md + proof pack |

No artifact proof means the gate is not accepted.

---

## 12. Task blocks

### RC-CORE1 — ProjectProfile + init-project + generic reference strategy

Goal:

```text
Make the project reusable and remove one-off character hardcoding.
```

Required:

```text
[ ] ProjectProfile models
[ ] CharacterProfile resolver by alias
[ ] CleanReferenceConfig
[ ] init-project command
[ ] generic clean_reference strategy engine
[ ] single_panel_crop strategy
[ ] no Alya hardcode in core
[ ] second dummy character portability test
```

Acceptance:

```text
[ ] Project initializes from CLI.
[ ] Alya exists only in project_profile/prompt_pack/test fixtures.
[ ] Clean reference uses profile strategy.
[ ] New dummy character works through profile without core code changes.
[ ] Tests green.
```

---

### RC-RUNTIME1 — Preflight + NodeSchemaRegistry + CheckpointResolver

Goal:

```text
Prevent invalid real ComfyUI runs.
```

Required:

```text
[ ] ComfyUI alive check
[ ] object_info check
[ ] required node check
[ ] ImageScale schema proof
[ ] checkpoint existence check
[ ] path safety check
[ ] structured preflight JSON
```

Acceptance:

```text
[ ] Missing node blocks before submit.
[ ] Missing checkpoint blocks before submit.
[ ] Valid environment returns READY.
```

---

### RC-WF1 — WorkflowGraphEditor-lite

Goal:

```text
Safely edit and validate workflow graphs.
```

Required:

```text
[ ] find nodes
[ ] set input
[ ] connect nodes
[ ] add known node
[ ] replace known node
[ ] validate no dangling links
[ ] validate reference_locked graph
```

Acceptance:

```text
[ ] LoadImage → ImageScale → VAEEncode → KSampler proven.
[ ] EmptyLatentImage not active source.
[ ] Invalid graph blocks before submit.
```

---

### RC-AGENT1 — ProducerDirectorAgent-lite + Operator CLI

Goal:

```text
Make the system usable without Windsurf.
```

Required:

```text
[ ] agent-status
[ ] agent-preflight
[ ] agent-next
[ ] agent-run
[ ] agent-retry
[ ] agent-resume
[ ] agent-artifacts
```

Acceptance:

```text
[ ] Agent can inspect state.
[ ] Agent can choose next allowed action.
[ ] Agent can run one action.
[ ] Agent outputs status and artifact links.
```

---

### RC-DRY1 — Stable dry proof

Goal:

```text
Prove production-like path without real ComfyUI execution.
```

Required:

```text
[ ] stable project root
[ ] project_profile
[ ] prompt_pack
[ ] clean reference
[ ] submitted_workflow
[ ] observed_settings
[ ] preflight
[ ] artifact_index
[ ] no temp paths
```

Acceptance:

```text
[ ] Dry proof uses stable project root only.
[ ] No AppData/Temp/pytest.
[ ] Graph and prompts correct.
```

---

### RC-REAL1 — Real generate_frames

Goal:

```text
Generate real frame(s) through ComfyUI.
```

Required:

```text
[ ] preflight READY
[ ] one generate_frames action
[ ] submitted_workflow written
[ ] observed_settings written
[ ] frames_manifest written
[ ] frame_count > 0
[ ] ledger updated
```

Acceptance:

```text
[ ] exit code 0
[ ] frame_count > 0
[ ] generated frame exists
[ ] no downstream actions executed
```

---

### RC-QC1 — QCService + RetryPolicy-lite

Goal:

```text
Validate outputs and retry safely when appropriate.
```

Required:

```text
[ ] QC report
[ ] black frame check
[ ] contact sheet/grid check
[ ] UI strip/text panel check
[ ] retry policy max 2
[ ] retry_decision
[ ] ledger records
```

Acceptance:

```text
[ ] Bad outputs rejected.
[ ] Retry is bounded.
[ ] Structural failures block instead of retry.
```

---

### RC-FLOW1 — Controlled downstream

Goal:

```text
Continue pipeline after accepted frames.
```

Required:

```text
[ ] assemble_scene
[ ] qa_review
[ ] render_episode or documented limitation
[ ] state transitions
[ ] blocked actions proof
```

Acceptance:

```text
[ ] Actions run only in correct order.
[ ] No hidden downstream execution.
[ ] Final artifact or documented limitation exists.
```

---

### RC-FINAL1 — Runbook + acceptance pack

Goal:

```text
Package the project as a usable RC.
```

Required:

```text
[ ] README_RUNBOOK.md
[ ] ACCEPTANCE_REPORT.md
[ ] KNOWN_LIMITATIONS.md
[ ] demo script
[ ] validate_rc_artifacts.py
[ ] final proof pack
```

Acceptance:

```text
[ ] Operator can reproduce Golden Path.
[ ] Proof pack contains required artifacts.
[ ] Known limitations are explicit.
```

---

## 13. Testing rules

Every task must follow this order:

```text
1. py_compile for changed Python files
2. focused tests
3. targeted suite
4. full scoped acceptance suite
```

Do not:

```text
- skip tests;
- xfail tests;
- delete assertions;
- weaken graph gates;
- claim failures are pre-existing without baseline proof.
```

---

## 14. Proof rules

Every completed implementation must return:

```text
1. Status
2. Files modified
3. Root cause
4. What changed
5. Exact commands
6. Test counts
7. Last 20 lines if requested
8. Actual JSON/artifact fragments
9. Regression protection
10. Risks/limitations
11. Explicit confirmation
```

Summary is not proof.

---

## 15. Scope cuts

If deadline pressure is high, cut these:

```text
- advanced Web UI;
- Telegram bot;
- IPAdapter/InstantID;
- full autonomous multi-agent swarm;
- advanced semantic vision judge;
- Grafana/Prometheus;
- RAG;
- workflow generation from natural language;
- marketplace templates.
```

Do not cut:

```text
- ProjectProfile;
- Director-lite;
- Operator CLI;
- PreflightService;
- WorkflowGraphEditor-lite;
- QCService;
- RetryPolicy-lite;
- ArtifactIndex;
- Ledger;
- Runbook.
```

---

## 16. Final demo commands

The final project should support a sequence like:

```powershell
python -m app init-project --project-root "f:\ComfyUI\projects\mir_erdan_ep01" --project-id "mir_erdan"

python -m app agent-preflight --project-root "f:\ComfyUI\projects\mir_erdan_ep01"

python -m app agent-run --project-root "f:\ComfyUI\projects\mir_erdan_ep01" --goal "generate ep01 shot01 with Alya"

python -m app agent-status --project-root "f:\ComfyUI\projects\mir_erdan_ep01"

python -m app agent-artifacts --project-root "f:\ComfyUI\projects\mir_erdan_ep01"
```

---

## 17. Final notes

The project must end as a reusable local production assistant, not a one-off script.

Alya is the first proof case.

The core system must be reusable for the next project and the next character.

All final claims must be backed by actual artifacts, not summaries.
