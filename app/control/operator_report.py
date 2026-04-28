"""MK-OBS1.4 — Operator Report HTML generator.

Generates a human-readable HTML report for operators to review
generation settings, node settings, and visual QA verdicts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class OperatorReportGenerator:
    """Generates HTML operator reports."""

    def __init__(
        self,
        project_id: str,
        episode_id: str,
        shot_id: str,
        current_state: str,
        expected_next_action: str,
        reference_lock_status: dict[str, Any] | None,
        prompt_pack: dict[str, Any] | None,
        beat_data: list[dict[str, Any]],
    ) -> None:
        """
        Initialize report generator.

        Args:
            project_id: Project identifier
            episode_id: Episode identifier
            shot_id: Shot identifier
            current_state: Current shot state
            expected_next_action: Next expected action
            reference_lock_status: Reference lock approval status
            prompt_pack: Prompt pack dictionary
            beat_data: List of beat data with settings and QA verdicts
        """
        self.project_id = project_id
        self.episode_id = episode_id
        self.shot_id = shot_id
        self.current_state = current_state
        self.expected_next_action = expected_next_action
        self.reference_lock_status = reference_lock_status or {}
        self.prompt_pack = prompt_pack or {}
        self.beat_data = beat_data

    def generate_html(self) -> str:
        """
        Generate HTML report.

        Returns:
            HTML string
        """
        html_parts = [
            self._html_header(),
            self._html_body(),
            self._html_footer(),
        ]
        return "\n".join(html_parts)

    def _html_header(self) -> str:
        """Generate HTML header with CSS."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Operator Report - {self.project_id}/{self.episode_id}/{self.shot_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007acc;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .info-item {{
            background-color: #f9f9f9;
            padding: 10px 15px;
            border-radius: 4px;
        }}
        .info-label {{
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
        }}
        .info-value {{
            color: #333;
            margin-top: 5px;
        }}
        .status-approved {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-denied {{
            color: #dc3545;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #007acc;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .qa-pass {{
            background-color: #d4edda;
            color: #155724;
        }}
        .qa-fail {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .preview-cell {{
            width: 150px;
        }}
        .preview-img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">"""

    def _html_body(self) -> str:
        """Generate HTML body content."""
        parts = [
            f"<h1>Operator Report: {self.project_id}/{self.episode_id}/{self.shot_id}</h1>",
            self._html_section_overview(),
            self._html_section_reference_lock(),
            self._html_section_prompt_pack(),
            self._html_section_beat_table(),
        ]
        return "\n".join(parts)

    def _html_section_overview(self) -> str:
        """Generate overview section."""
        return f"""<h2>Overview</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Project ID</div>
                <div class="info-value">{self.project_id}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Episode ID</div>
                <div class="info-value">{self.episode_id}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Shot ID</div>
                <div class="info-value">{self.shot_id}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Current State</div>
                <div class="info-value">{self.current_state}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Expected Next Action</div>
                <div class="info-value">{self.expected_next_action}</div>
            </div>
        </div>"""

    def _html_section_reference_lock(self) -> str:
        """Generate reference lock section."""
        approved = self.reference_lock_status.get("approved", False)
        status_class = "status-approved" if approved else "status-denied"
        status_text = "APPROVED" if approved else "DENIED"
        reason = self.reference_lock_status.get("reason", "No reason provided")

        return f"""<h2>Reference Lock Status</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Status</div>
                <div class="info-value {status_class}">{status_text}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Reason</div>
                <div class="info-value">{reason}</div>
            </div>
        </div>"""

    def _html_section_prompt_pack(self) -> str:
        """Generate prompt pack summary section."""
        checkpoint = self.prompt_pack.get("checkpoint", "N/A")
        beats_count = len(self.prompt_pack.get("beats", []))
        global_negative = self.prompt_pack.get("global_negative", "N/A")
        global_negative_display = global_negative[:100] + "..." if len(global_negative) > 100 else global_negative

        return f"""<h2>Prompt Pack Summary</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Checkpoint</div>
                <div class="info-value">{checkpoint}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Number of Beats</div>
                <div class="info-value">{beats_count}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Global Negative</div>
                <div class="info-value">{global_negative_display}</div>
            </div>
        </div>"""

    def _html_section_beat_table(self) -> str:
        """Generate beat table section."""
        if not self.beat_data:
            return "<h2>Beat Data</h2><p>No beat data available.</p>"

        rows = []
        for beat in self.beat_data:
            qa_verdict = beat.get("qa_verdict", "pending")
            qa_class = "qa-pass" if qa_verdict == "pass" else "qa-fail" if qa_verdict == "fail" else ""
            frame_path = beat.get("frame_path", "")
            preview_html = ""
            if frame_path and Path(frame_path).exists():
                preview_html = f'<img src="{frame_path}" class="preview-img" alt="Frame preview">'
            else:
                preview_html = '<span style="color: #999;">No frame</span>'

            row = f"""<tr>
                <td>{beat.get("beat_id", "N/A")}</td>
                <td class="preview-cell">{preview_html}</td>
                <td>{beat.get("frame_path", "N/A")}</td>
                <td>{beat.get("seed", "N/A")}</td>
                <td>{beat.get("checkpoint", "N/A")}</td>
                <td>{beat.get("steps", "N/A")}</td>
                <td>{beat.get("sampler", "N/A")}</td>
                <td>{beat.get("scheduler", "N/A")}</td>
                <td>{beat.get("prompt_source", "N/A")}</td>
                <td>{beat.get("node_settings_status", "N/A")}</td>
                <td class="{qa_class}">{qa_verdict}</td>
            </tr>"""
            rows.append(row)

        return f"""<h2>Beat Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Beat ID</th>
                    <th>Preview</th>
                    <th>Frame Path</th>
                    <th>Seed</th>
                    <th>Checkpoint</th>
                    <th>Steps</th>
                    <th>Sampler</th>
                    <th>Scheduler</th>
                    <th>Prompt Source</th>
                    <th>Node Settings Status</th>
                    <th>QA Verdict</th>
                </tr>
            </thead>
            <tbody>
                {"\n".join(rows)}
            </tbody>
        </table>"""

    def _html_footer(self) -> str:
        """Generate HTML footer."""
        return """    </div>
</body>
</html>"""


def generate_operator_report(
    output_path: str | Path,
    project_id: str,
    episode_id: str,
    shot_id: str,
    current_state: str,
    expected_next_action: str,
    reference_lock_status: dict[str, Any] | None,
    prompt_pack: dict[str, Any] | None,
    beat_data: list[dict[str, Any]],
) -> None:
    """
    Generate operator report HTML file.

    Args:
        output_path: Path to output HTML file
        project_id: Project identifier
        episode_id: Episode identifier
        shot_id: Shot identifier
        current_state: Current shot state
        expected_next_action: Next expected action
        reference_lock_status: Reference lock approval status
        prompt_pack: Prompt pack dictionary
        beat_data: List of beat data with settings and QA verdicts
    """
    generator = OperatorReportGenerator(
        project_id=project_id,
        episode_id=episode_id,
        shot_id=shot_id,
        current_state=current_state,
        expected_next_action=expected_next_action,
        reference_lock_status=reference_lock_status,
        prompt_pack=prompt_pack,
        beat_data=beat_data,
    )

    html = generator.generate_html()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    # CLI for testing
    import sys

    if len(sys.argv) < 8:
        print("Usage: python -m app.control.operator_report <output.html> <project_id> <episode_id> <shot_id> <current_state> <expected_next_action> <beat_data.json>")
        sys.exit(1)

    output_path = sys.argv[1]
    project_id = sys.argv[2]
    episode_id = sys.argv[3]
    shot_id = sys.argv[4]
    current_state = sys.argv[5]
    expected_next_action = sys.argv[6]
    beat_data_path = sys.argv[7]

    with open(beat_data_path, "r", encoding="utf-8") as f:
        beat_data = json.load(f)

    generate_operator_report(
        output_path=output_path,
        project_id=project_id,
        episode_id=episode_id,
        shot_id=shot_id,
        current_state=current_state,
        expected_next_action=expected_next_action,
        reference_lock_status={"approved": True, "reason": "All references approved"},
        prompt_pack={"checkpoint": "test.safetensors", "beats": [], "global_negative": "test"},
        beat_data=beat_data,
    )

    print(f"Operator report generated: {output_path}")
