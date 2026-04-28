"""MK-P6 — Episode assembler.

Takes a BriefModel and a list of BuiltScene objects and assembles them
into a complete Episode with aggregated statistics.
"""
from __future__ import annotations

from app.brief.models import BriefModel
from app.scenes.models import BuiltScene

from .models import Episode


class EpisodeAssembler:
    def __init__(self) -> None:
        pass

    def assemble(
        self,
        brief: BriefModel,
        scenes: list[BuiltScene],
    ) -> Episode:
        total_duration_sec = sum(s.duration_sec for s in scenes)
        total_frames = sum(s.total_frames for s in scenes)

        return Episode(
            title=brief.meta.title,
            total_duration_sec=total_duration_sec,
            total_frames=total_frames,
            fps=brief.meta.fps,
            aspect_ratio=brief.meta.aspect_ratio,
            scenes=scenes,
        )
