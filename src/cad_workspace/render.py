from __future__ import annotations

from pathlib import Path
from typing import Protocol

from PIL import Image, ImageDraw, ImageFont


class RenderArtifact(Protocol):
    slug: str


class RenderProject(Protocol):
    project_id: str
    path: Path
    artifacts: tuple[RenderArtifact, ...]


def render_project(project: RenderProject) -> Path | None:
    images: list[tuple[str, Image.Image]] = []

    for artifact in project.artifacts:
        image_path = project.path / "artifacts" / artifact.slug / f"{artifact.slug}.png"
        if image_path.exists():
            images.append((title_from_slug(artifact.slug), Image.open(image_path).convert("RGB")))

    if not images:
        return None

    output_path = project.path / "renders" / f"{project.project_id}_final.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    canvas = compose_labeled_grid(images)
    canvas.save(output_path, "PNG", optimize=True)
    return output_path


def compose_labeled_grid(images: list[tuple[str, Image.Image]]) -> Image.Image:
    tile_width = 860
    tile_height = 560
    padding = 48
    label_height = 54
    columns = min(2, len(images))
    rows = (len(images) + columns - 1) // columns

    canvas_width = columns * tile_width + (columns + 1) * padding
    canvas_height = rows * (tile_height + label_height) + (rows + 1) * padding
    canvas = Image.new("RGB", (canvas_width, canvas_height), (246, 247, 248))
    draw = ImageDraw.Draw(canvas)
    label_font = load_label_font()

    for index, (label, image) in enumerate(images):
        row = index // columns
        column = index % columns
        x = padding + column * (tile_width + padding)
        y = padding + row * (tile_height + label_height + padding)

        draw_centered_label(draw, label, label_font, x, y, tile_width)
        panel = Image.new("RGB", (tile_width, tile_height), (255, 255, 255))
        preview = image.copy()
        preview.thumbnail((tile_width, tile_height), Image.Resampling.LANCZOS)
        panel.paste(preview, ((tile_width - preview.width) // 2, (tile_height - preview.height) // 2))
        canvas.paste(panel, (x, y + label_height))

    return canvas


def draw_centered_label(
    draw: ImageDraw.ImageDraw,
    label: str,
    font: ImageFont.ImageFont,
    x: int,
    y: int,
    width: int,
) -> None:
    bbox = draw.textbbox((0, 0), label, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text((x + (width - text_width) // 2, y), label, fill=(35, 39, 47), font=font)


def load_label_font() -> ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, 30)
        except OSError:
            pass

    return ImageFont.load_default()


def title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()
