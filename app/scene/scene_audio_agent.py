"""
Scene Audio Agent - MK-4

Generates voiceover audio for scene videos and links audio artifacts to scene manifests.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

def check_tts_availability() -> tuple[bool, str]:
    """Check TTS availability at runtime."""
    try:
        import edge_tts
        return True, "edge-tts"
    except ImportError:
        try:
            import pyttsx3
            return True, "pyttsx3"
        except ImportError:
            return False, "none"


@dataclass
class SceneAudioConfig:
    """Configuration for scene audio generation."""
    scene_manifest_path: str
    output_audio_dir: str
    voiceover_text: str | None = None
    tts_tool: str = "pyttsx3"
    audio_format: str = "wav"
    voice_rate: int = 150  # Words per minute


@dataclass
class SceneAudioResult:
    """Result of scene audio generation."""
    scene_id: str
    status: str
    video_path: str
    voiceover_text: str
    tts_tool: str
    audio_path: str
    audio_format: str
    scene_linkage: dict[str, Any]
    manifest_path: str
    error: str | None = None


class SceneAudioAgent:
    """Agent for generating and linking scene audio."""

    def __init__(
        self,
        manifests_dir: str,
        audio_output_dir: str,
    ):
        self.manifests_dir = Path(manifests_dir)
        self.audio_output_dir = Path(audio_output_dir)
        self.audio_output_dir.mkdir(parents=True, exist_ok=True)

    def _load_scene_manifest(self, scene_manifest_path: str) -> dict[str, Any]:
        """Load scene manifest from file."""
        with open(scene_manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _generate_voiceover_text(self, scene_manifest: dict[str, Any]) -> str:
        """Generate voiceover text from scene context."""
        # Extract scene prompt from manifest
        video_prompt = scene_manifest.get("processing", {}).get("prompt", "")
        
        # Generate simple voiceover based on scene content
        if "portrait" in video_prompt.lower():
            base_text = "A cinematic portrait scene with subtle movement."
        elif "dynamic" in video_prompt.lower():
            base_text = "A dynamic scene with energetic motion."
        elif "static" in video_prompt.lower() or "frozen" in video_prompt.lower():
            base_text = "A static scene with minimal movement."
        else:
            base_text = "A scene with visual elements."
        
        # Add context-specific details
        if "cinematic" in video_prompt.lower():
            base_text += " Cinematic lighting and professional quality."
        if "subtle" in video_prompt.lower():
            base_text += " Subtle transitions and smooth details."
        
        return base_text

    def _generate_audio_with_pyttsx3(
        self,
        text: str,
        output_path: str,
        rate: int = 150,
    ) -> str:
        """Generate audio using pyttsx3."""
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        return output_path

    async def _generate_audio_with_edge_tts(
        self,
        text: str,
        output_path: str,
    ) -> str:
        """Generate audio using edge-tts."""
        import edge_tts

        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
        await communicate.save(output_path)
        return output_path

    async def _generate_audio(
        self,
        text: str,
        output_path: str,
        tts_tool: str = "pyttsx3",
        rate: int = 150,
    ) -> str:
        """Generate audio file from text."""
        if tts_tool == "pyttsx3":
            return self._generate_audio_with_pyttsx3(text, output_path, rate)
        elif tts_tool == "edge-tts":
            return await self._generate_audio_with_edge_tts(text, output_path)
        else:
            raise ValueError(f"TTS tool {tts_tool} not available")

    def _create_scene_linkage(
        self,
        scene_manifest: dict[str, Any],
        audio_path: str,
        voiceover_text: str,
        tts_tool: str,
    ) -> dict[str, Any]:
        """Create scene-audio linkage fragment."""
        scene_id = scene_manifest.get("video_id", "unknown")
        video_path = scene_manifest.get("export", {}).get("export_path", "")
        
        linkage = {
            "scene_id": scene_id,
            "video_path": video_path,
            "audio_path": audio_path,
            "voiceover_text": voiceover_text,
            "tts_tool": tts_tool,
            "linked_at": datetime.now().isoformat(),
            "linkage_type": "scene_audio_voiceover",
        }
        
        return linkage

    def _update_manifest_with_audio(
        self,
        scene_manifest: dict[str, Any],
        audio_path: str,
        voiceover_text: str,
        tts_tool: str,
        linkage: dict[str, Any],
    ) -> dict[str, Any]:
        """Update scene manifest with audio information."""
        # Add audio section if not exists
        if "audio" not in scene_manifest:
            scene_manifest["audio"] = {}
        
        scene_manifest["audio"]["audio_path"] = audio_path
        scene_manifest["audio"]["voiceover_text"] = voiceover_text
        scene_manifest["audio"]["tts_tool"] = tts_tool
        scene_manifest["audio"]["generated_at"] = datetime.now().isoformat()
        scene_manifest["audio"]["linkage"] = linkage
        
        return scene_manifest

    def _save_manifest(self, manifest: dict[str, Any], manifest_path: str) -> None:
        """Save updated manifest to file."""
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    async def generate_scene_audio(
        self,
        config: SceneAudioConfig,
    ) -> SceneAudioResult:
        """Generate scene audio and link to scene video.

        Args:
            config: SceneAudioConfig with scene manifest path and settings

        Returns:
            SceneAudioResult with audio path and linkage information
        """
        try:
            # Step 1: Load scene manifest
            scene_manifest = self._load_scene_manifest(config.scene_manifest_path)
            scene_id = scene_manifest.get("video_id", "unknown")
            video_path = scene_manifest.get("export", {}).get("export_path", "")

            # Step 2: Generate voiceover text
            voiceover_text = config.voiceover_text or self._generate_voiceover_text(scene_manifest)

            # Step 3: Generate audio file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"scene_audio_{scene_id}_{timestamp}.{config.audio_format}"
            audio_path = str(self.audio_output_dir / audio_filename)

            await self._generate_audio(
                text=voiceover_text,
                output_path=audio_path,
                tts_tool=config.tts_tool,
                rate=config.voice_rate,
            )

            # Step 4: Create scene-audio linkage
            linkage = self._create_scene_linkage(
                scene_manifest=scene_manifest,
                audio_path=audio_path,
                voiceover_text=voiceover_text,
                tts_tool=config.tts_tool,
            )

            # Step 5: Update manifest with audio information
            updated_manifest = self._update_manifest_with_audio(
                scene_manifest=scene_manifest,
                audio_path=audio_path,
                voiceover_text=voiceover_text,
                tts_tool=config.tts_tool,
                linkage=linkage,
            )

            # Step 6: Save updated manifest
            self._save_manifest(updated_manifest, config.scene_manifest_path)

            return SceneAudioResult(
                scene_id=scene_id,
                status="completed",
                video_path=video_path,
                voiceover_text=voiceover_text,
                tts_tool=config.tts_tool,
                audio_path=audio_path,
                audio_format=config.audio_format,
                scene_linkage=linkage,
                manifest_path=config.scene_manifest_path,
                error=None,
            )

        except Exception as e:
            return SceneAudioResult(
                scene_id="unknown",
                status="failed",
                video_path="",
                voiceover_text="",
                tts_tool=config.tts_tool,
                audio_path="",
                audio_format=config.audio_format,
                scene_linkage={},
                manifest_path=config.scene_manifest_path,
                error=str(e),
            )


async def run_scene_audio(
    scene_manifest_path: str,
    voiceover_text: str | None = None,
    tts_tool: str = "pyttsx3",
    audio_format: str = "wav",
) -> dict[str, Any]:
    """Run scene audio generation.

    Args:
        scene_manifest_path: Path to scene manifest JSON
        voiceover_text: Optional custom voiceover text
        tts_tool: TTS tool to use (default: pyttsx3)
        audio_format: Audio output format (default: wav)

    Returns:
        Dictionary with generation results
    """
    # Set up paths
    manifests_dir = "data/manifests"
    audio_output_dir = "data/audio/scenes"

    # Check TTS availability at runtime
    tts_available, available_tool = check_tts_availability()
    if not tts_available:
        return {
            "status": "failed",
            "error": f"TTS tool {tts_tool} not available. Install with: pip install edge-tts",
            "scene_id": "unknown",
            "audio_path": "",
            "voiceover_text": "",
            "tts_tool": tts_tool,
            "scene_linkage": {},
            "manifest_path": scene_manifest_path,
        }

    # Create config
    config = SceneAudioConfig(
        scene_manifest_path=scene_manifest_path,
        output_audio_dir=audio_output_dir,
        voiceover_text=voiceover_text,
        tts_tool=tts_tool,
        audio_format=audio_format,
    )

    # Create agent and generate audio
    agent = SceneAudioAgent(manifests_dir, audio_output_dir)
    result = await agent.generate_scene_audio(config)

    return {
        "status": result.status,
        "scene_id": result.scene_id,
        "video_path": result.video_path,
        "voiceover_text": result.voiceover_text,
        "tts_tool": result.tts_tool,
        "audio_path": result.audio_path,
        "audio_format": result.audio_format,
        "scene_linkage": result.scene_linkage,
        "manifest_path": result.manifest_path,
        "error": result.error,
    }
