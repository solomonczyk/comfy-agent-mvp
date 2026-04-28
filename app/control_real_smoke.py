"""MK-CTRL12 — Manual real generate smoke command.

Manual, explicit, safe CLI for real generate_frames execution through the control stack.
Default run is safe (dry_validate only). Real execution requires explicit flags.

No top-level imports from production systems.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .control import (
    ActionPlanBuilder,
    HandlerPayload,
    HandlerResult,
    RealGenerateFramesHandler,
    ShotController,
    ShotControlService,
    ShotExecutionGate,
    ShotLedgerStorage,
    ShotStateReport,
)


class ManualGenerateRunner:
    """Abstraction for manual generate_frames execution.

    Default: fake runner that returns simulated frame paths.
    Real mode: lazy import of ExecutionRunner only when explicitly enabled.
    """

    def __init__(self, fake: bool = True) -> None:
        self.fake = fake
        self._real_runner: Any = None

    def run(self, **kwargs: Any) -> dict[str, Any]:
        if self.fake:
            return self._fake_run(**kwargs)
        else:
            return self._real_run(**kwargs)

    def _fake_run(self, **kwargs: Any) -> dict[str, Any]:
        """Simulate successful generation."""
        episode_id = kwargs.get("episode_id", "unknown")
        shot_id = kwargs.get("shot_id", "unknown")
        output_dir = kwargs.get("output_dir", "output")
        return {
            "frame_paths": [
                f"{output_dir}/{episode_id}/{shot_id}/frame_{i:04d}.png"
                for i in range(1, 3)
            ],
            "manifest_path": f"{output_dir}/{episode_id}/{shot_id}/manifest.json",
            "preview_path": f"{output_dir}/{episode_id}/{shot_id}/preview.png",
        }

    def _real_run(self, **kwargs: Any) -> dict[str, Any]:
        """Lazy import and call real ExecutionRunner."""
        if self._real_runner is None:
            # Lazy import only when explicitly needed
            from .runner import ExecutionRunner

            self._real_runner = ExecutionRunner()

        # Build request for ExecutionRunner
        from .control import GenerateFramesRequest

        request = GenerateFramesRequest(
            episode_id=kwargs.get("episode_id", ""),
            shot_id=kwargs.get("shot_id", ""),
            brief_path=kwargs.get("brief_path"),
            output_dir=kwargs.get("output_dir", ""),
            workflow_template_path=kwargs.get("workflow_template_path"),
            checkpoint=kwargs.get("checkpoint"),
            steps=kwargs.get("steps"),
            seed=kwargs.get("seed"),
            extra=kwargs.get("extra", {}),
        )

        result = self._real_runner.generate_frames(request)
        return result.to_dict() if hasattr(result, "to_dict") else result


def build_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manual smoke command for real generate_frames execution"
    )
    parser.add_argument(
        "--episode-id",
        required=True,
        help="Episode identifier (e.g., ep01)",
    )
    parser.add_argument(
        "--shot-id",
        required=True,
        help="Shot identifier (e.g., shot01)",
    )
    parser.add_argument(
        "--action",
        required=True,
        help="Action to execute (e.g., generate_frames)",
    )
    parser.add_argument(
        "--brief",
        required=True,
        help="Path to brief file",
    )
    parser.add_argument(
        "--output",
        default="output/manual_smoke",
        help="Output directory (default: output/manual_smoke)",
    )
    parser.add_argument(
        "--dry-validate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Dry validate only (default: True)",
    )
    parser.add_argument(
        "--allow-real-execution",
        action="store_true",
        default=False,
        help="Allow real execution (default: False)",
    )
    parser.add_argument(
        "--enable-real-handler",
        action="store_true",
        default=False,
        help="Enable real handler (default: False)",
    )
    parser.add_argument(
        "--print-payload",
        action="store_true",
        help="Print HandlerPayload JSON before execution",
    )
    parser.add_argument(
        "--print-response",
        action="store_true",
        help="Print ShotControlResponse JSON after execution",
    )
    parser.add_argument(
        "--ledger-root",
        default="output/control",
        help="Ledger root directory (default: output/control)",
    )
    return parser


def main() -> int:
    args = build_args_parser().parse_args()

    # Validate brief path exists
    brief_path = Path(args.brief)
    if not brief_path.exists():
        print(f"Error: Brief file not found: {args.brief}", file=sys.stderr)
        return 1

    # Build runner factory
    def runner_factory():
        fake = not args.enable_real_handler
        return ManualGenerateRunner(fake=fake)

    # Build handler
    handler = RealGenerateFramesHandler(
        runner_factory=runner_factory,
        enable_real_execution=args.enable_real_handler,
        output_root=Path(args.output),
    )

    # Build handler registry
    from .control import HandlerRegistry
    registry = HandlerRegistry()
    registry.register(
        "generate_frames",
        handler,
        enabled=True,
        description="Real-ready generate_frames handler (manual smoke)",
    )

    # Build ShotControlService
    controller = ShotController(Path(args.ledger_root))
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()
    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=Path(args.ledger_root),
    )

    # Execute through service
    response = service.execute(args.episode_id, args.shot_id, args.action)

    # Print result
    if args.print_response:
        print("ShotControlResponse:")
        print(json.dumps(response.to_dict(), indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
