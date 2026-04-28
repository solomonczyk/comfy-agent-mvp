"""MK-CTRL26 — Prompt pack loader for contract-driven generation.

Loads prompt_pack.json which contains beat-level generation specifications
including prompts, seed policy, sampler, scheduler, steps, cfg, and checkpoint.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


def load_prompt_pack(project_root: str, episode_id: str, shot_id: str) -> Optional[dict[str, Any]]:
    """
    Load prompt pack from project root.
    
    Args:
        project_root: Path to project root directory
        episode_id: Episode ID to match
        shot_id: Shot ID to match
    
    Returns:
        Prompt pack dict if found and matches episode/shot, else None
    """
    project_path = Path(project_root)
    prompt_pack_path = project_path / "output" / "control" / "prompt_pack.json"
    
    if not prompt_pack_path.exists():
        return None
    
    try:
        with open(prompt_pack_path, 'r', encoding='utf-8') as f:
            prompt_pack = json.load(f)
        
        # Verify episode and shot match
        if prompt_pack.get("episode_id") == episode_id and prompt_pack.get("shot_id") == shot_id:
            return prompt_pack
        
        return None
    except (json.JSONDecodeError, IOError):
        return None


def calculate_deterministic_seed(character_seed: int, beat_seed_offset: int) -> int:
    """
    Calculate deterministic seed for a beat.
    
    Args:
        character_seed: Base character seed
        beat_seed_offset: Beat-specific offset
    
    Returns:
        Deterministic seed for the beat
    """
    return character_seed + beat_seed_offset


def get_beat_seed(prompt_pack: dict[str, Any], beat_id: str) -> Optional[int]:
    """
    Get deterministic seed for a specific beat from prompt pack.
    
    Args:
        prompt_pack: Prompt pack dictionary
        beat_id: Beat ID to look up
    
    Returns:
        Deterministic seed if found, else None
    """
    seed_policy = prompt_pack.get("beats", [])
    
    for beat in seed_policy:
        if beat.get("beat_id") == beat_id:
            seed_policy_obj = beat.get("seed_policy", {})
            if isinstance(seed_policy_obj, dict):
                character_seed = seed_policy_obj.get("character_seed")
                beat_seed_offset = seed_policy_obj.get("beat_seed_offset", {}).get(beat_id, 0)
                if character_seed is not None:
                    return calculate_deterministic_seed(character_seed, beat_seed_offset)
    
    return None


if __name__ == "__main__":
    # CLI for testing
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python -m app.control.prompt_pack <project_root> <episode_id> <shot_id>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    episode_id = sys.argv[2]
    shot_id = sys.argv[3]
    
    prompt_pack = load_prompt_pack(project_root, episode_id, shot_id)
    if prompt_pack:
        print(json.dumps(prompt_pack, indent=2, ensure_ascii=False))
    else:
        print(f"Prompt pack not found for {episode_id}/{shot_id}")
        sys.exit(1)
