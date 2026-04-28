"""MK-P1 — Brief/TZ parser.

Supports two input formats:
  1. dict / JSON string — if brief is already structured (from LLM agent)
  2. Markdown — heuristic section parsing via ## Meta / ## Characters / ## Scenes

Both Russian and English field names are accepted.
"""
from __future__ import annotations

import json
import re

from .models import BriefModel, CharacterDef, ProjectMeta, SceneDef


class BriefParseError(ValueError):
    def __init__(self, msg: str, field: str = "") -> None:
        super().__init__(msg)
        self.field = field


class BriefParser:
    """Parse a raw brief (markdown text, JSON string, or dict) into a BriefModel."""

    def parse(self, source: str | dict) -> BriefModel:
        if isinstance(source, dict):
            return self._from_dict(source)
        stripped = source.strip()
        if stripped.startswith("{"):
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise BriefParseError(f"Invalid JSON brief: {exc}", "root") from exc
            return self._from_dict(data)
        return self._from_markdown(stripped)

    # ── dict path ───────────────────────────────────────────────

    def _from_dict(self, d: dict) -> BriefModel:
        try:
            return BriefModel.model_validate(d)
        except Exception as exc:
            raise BriefParseError(str(exc)) from exc

    # ── markdown path ────────────────────────────────────────────

    def _from_markdown(self, text: str) -> BriefModel:
        sections = self._split_sections(text)

        meta = self._parse_meta(sections.get("meta", ""))
        chars = self._parse_characters(sections.get("characters", ""))
        scenes = self._parse_scenes(sections.get("scenes", ""))

        return BriefModel(meta=meta, characters=chars, scenes=scenes)

    def _split_sections(self, text: str) -> dict[str, str]:
        """Split by ## headings, case-insensitive."""
        result: dict[str, str] = {}
        current_key: str | None = None
        buf: list[str] = []

        for line in text.splitlines():
            m = re.match(r"^##\s+(.+)$", line.strip())
            if m:
                if current_key:
                    result[current_key] = "\n".join(buf).strip()
                current_key = m.group(1).strip().lower()
                buf = []
            else:
                buf.append(line)

        if current_key:
            result[current_key] = "\n".join(buf).strip()
        return result

    def _parse_meta(self, block: str) -> ProjectMeta:
        kv = self._kv(block)
        title = kv.get("title") or kv.get("название")
        if not title:
            raise BriefParseError("meta.title is required", "meta.title")
        dur_raw = kv.get("duration") or kv.get("длительность") or "30"
        try:
            dur = float(re.sub(r"[^\d.]", "", dur_raw))
        except ValueError:
            dur = 30.0
        if dur <= 0:
            dur = 30.0
        return ProjectMeta(
            title=title,
            aspect_ratio=kv.get("aspect_ratio", "4:3"),
            fps=int(kv.get("fps", 8)),
            target_duration_sec=dur,
            style_hint=kv.get("style") or kv.get("стиль"),
            mood=kv.get("mood") or kv.get("настроение"),
            episode_id=kv.get("episode_id"),
            shot_id=kv.get("shot_id"),
        )

    def _parse_characters(self, block: str) -> list[CharacterDef]:
        chars: list[CharacterDef] = []
        if not block or not block.strip():
            return chars
        entries = re.split(r"\n(?=-\s|\#{3}\s)", block.strip())
        for entry in entries:
            kv = self._kv(entry)
            name = kv.get("name") or kv.get("имя")
            desc = kv.get("visual") or kv.get("description") or kv.get("описание")
            if not name or not desc:
                continue
            chars.append(CharacterDef(
                name=name,
                visual_description=desc,
                voice_id=kv.get("voice_id") or kv.get("голос"),
                lora_ref=kv.get("lora"),
            ))
        return chars

    def _parse_scenes(self, block: str) -> list[SceneDef]:
        scenes: list[SceneDef] = []
        entries = re.split(r"\n(?=-\s|\#{3}\s)", block.strip())
        for i, entry in enumerate(entries, start=1):
            kv = self._kv(entry)
            action = kv.get("action") or kv.get("действие")
            if not action:
                continue
            chars_raw = kv.get("characters") or kv.get("персонажи") or ""
            chars_list = [c.strip() for c in re.split(r"[,;]", chars_raw) if c.strip()]
            dur_raw = kv.get("duration") or kv.get("длительность") or "1.5"
            try:
                dur = float(re.sub(r"[^\d.]", "", dur_raw))
            except ValueError:
                dur = 1.5
            if dur <= 0:
                dur = 1.5
            kf_raw = kv.get("keyframes") or kv.get("кадры") or ""
            kf_list = [k.strip() for k in kf_raw.split("|") if k.strip()]
            # MK-REAL2R-2: Parse description field for detailed scene description
            description = kv.get("description")
            scenes.append(SceneDef(
                scene_id=kv.get("id", f"s{i:02d}"),
                characters_in_scene=chars_list,
                location=kv.get("location") or kv.get("локация"),
                action=action,
                description=description,  # MK-REAL2R-2
                dialogue=kv.get("dialogue") or kv.get("диалог"),
                duration_hint_sec=dur,
                keyframe_hints=kf_list,
                time=kv.get("time") or kv.get("время"),
                mood=kv.get("mood") or kv.get("настроение"),
                continuity_out=kv.get("continuity_out"),
                subtitles=kv.get("subtitles"),
            ))
        if not scenes:
            raise BriefParseError(
                "No scenes parsed. Expect blocks with 'action:' key.",
                "scenes",
            )
        return scenes

    # ── helpers ──────────────────────────────────────────────────

    @staticmethod
    def _kv(block: str) -> dict[str, str]:
        """key: value parser — works with markdown lists and plain text."""
        result: dict[str, str] = {}
        for line in block.splitlines():
            line = line.lstrip("- #*").strip()
            if ":" in line:
                k, _, v = line.partition(":")
                result[k.strip().lower()] = v.strip()
        return result
