"""MK-OBS1.5 — Contact Sheet generator for frame thumbnails.

Creates a contact sheet (grid of thumbnails) from generated frame paths
with labels showing beat_id, filename, and QA verdict.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise ImportError(
        "PIL (Pillow) is required for contact sheet generation. "
        "Install it with: pip install Pillow"
    )


class ContactSheetGenerator:
    """Generates contact sheets from frame paths."""

    def __init__(
        self,
        frame_data: list[dict[str, Any]],
        output_path: str | Path,
        thumbnail_size: tuple[int, int] = (256, 256),
        columns: int = 4,
        padding: int = 10,
    ) -> None:
        """
        Initialize contact sheet generator.

        Args:
            frame_data: List of frame data with path, beat_id, qa_verdict
            output_path: Path to output contact sheet image
            thumbnail_size: Size of each thumbnail (width, height)
            columns: Number of columns in the grid
            padding: Padding between thumbnails
        """
        self.frame_data = frame_data
        self.output_path = Path(output_path)
        self.thumbnail_size = thumbnail_size
        self.columns = columns
        self.padding = padding

    def generate(self) -> Path:
        """
        Generate contact sheet image.

        Returns:
            Path to generated contact sheet
        """
        if not self.frame_data:
            raise ValueError("No frame data provided")

        # Load and resize all frames
        thumbnails = []
        for frame in self.frame_data:
            frame_path = frame.get("frame_path")
            if not frame_path or not Path(frame_path).exists():
                # Create placeholder for missing frames
                thumb = self._create_placeholder(frame.get("beat_id", "N/A"), "missing")
            else:
                thumb = self._load_and_resize(frame_path)
            thumbnails.append((thumb, frame))

        # Calculate grid dimensions
        rows = (len(thumbnails) + self.columns - 1) // self.columns
        thumb_width, thumb_height = self.thumbnail_size
        label_height = 40  # Space for labels

        # Calculate canvas size
        canvas_width = self.columns * (thumb_width + self.padding) + self.padding
        canvas_height = rows * (thumb_height + label_height + self.padding) + self.padding

        # Create canvas
        canvas = Image.new("RGB", (canvas_width, canvas_height), color="#ffffff")
        draw = ImageDraw.Draw(canvas)

        # Place thumbnails
        for idx, (thumb, frame) in enumerate(thumbnails):
            row = idx // self.columns
            col = idx % self.columns

            x = self.padding + col * (thumb_width + self.padding)
            y = self.padding + row * (thumb_height + label_height + self.padding)

            # Paste thumbnail
            canvas.paste(thumb, (x, y))

            # Draw label
            label_y = y + thumb_height + 5
            beat_id = frame.get("beat_id", "N/A")
            filename = Path(frame.get("frame_path", "")).name
            qa_verdict = frame.get("qa_verdict", "pending")

            label_text = f"{beat_id} | {filename[:30]} | QA: {qa_verdict}"
            draw.text((x, label_y), label_text, fill="#000000")

        # Save contact sheet
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(self.output_path, "JPEG", quality=90)

        return self.output_path

    def _load_and_resize(self, frame_path: str) -> Image.Image:
        """Load and resize a frame to thumbnail size."""
        img = Image.open(frame_path)
        img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

        # Create a new image with exact thumbnail size (center crop)
        thumb = Image.new("RGB", self.thumbnail_size, color="#000000")
        img_width, img_height = img.size
        thumb_width, thumb_height = self.thumbnail_size

        # Calculate paste position (center)
        paste_x = (thumb_width - img_width) // 2
        paste_y = (thumb_height - img_height) // 2

        thumb.paste(img, (paste_x, paste_y))
        return thumb

    def _create_placeholder(self, beat_id: str, status: str) -> Image.Image:
        """Create a placeholder image for missing frames."""
        thumb = Image.new("RGB", self.thumbnail_size, color="#cccccc")
        draw = ImageDraw.Draw(thumb)

        # Draw placeholder text
        text = f"{beat_id}\n({status})"
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except (IOError, OSError):
            font = ImageFont.load_default()

        # Center text
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x = (self.thumbnail_size[0] - text_width) // 2
        y = (self.thumbnail_size[1] - text_height) // 2

        draw.text((x, y), text, fill="#666666", font=font)
        return thumb


def generate_contact_sheet(
    frame_data: list[dict[str, Any]],
    output_path: str | Path,
    thumbnail_size: tuple[int, int] = (256, 256),
    columns: int = 4,
) -> Path:
    """
    Convenience function to generate contact sheet.

    Args:
        frame_data: List of frame data with path, beat_id, qa_verdict
        output_path: Path to output contact sheet image
        thumbnail_size: Size of each thumbnail (width, height)
        columns: Number of columns in the grid

    Returns:
        Path to generated contact sheet
    """
    generator = ContactSheetGenerator(
        frame_data=frame_data,
        output_path=output_path,
        thumbnail_size=thumbnail_size,
        columns=columns,
    )
    return generator.generate()


if __name__ == "__main__":
    # CLI for testing
    import sys
    import json

    if len(sys.argv) < 3:
        print("Usage: python -m app.control.contact_sheet <frame_data.json> <output.jpg>")
        sys.exit(1)

    frame_data_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(frame_data_path, "r", encoding="utf-8") as f:
        frame_data = json.load(f)

    result = generate_contact_sheet(frame_data, output_path)
    print(f"Contact sheet generated: {result}")
