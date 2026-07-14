#!/usr/bin/env python3
"""Render full-frame transparent title/caption overlays for v2."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "overlays"
OUT.mkdir(exist_ok=True)

WIDTH, HEIGHT = 1080, 1920
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
TITLE_FONT = ImageFont.truetype(FONT, 70)
CAPTION_FONT = ImageFont.truetype(FONT, 50)

SCENES = [
    ("SKIP THE CLEANUP", "Painting or sanding?\nSkip hours of cleanup."),
    ("TAPE + FILM IN ONE", "Pre-taped masking film combines yellow tape\nand clear PE film in one roll."),
    ("TAPE FIRST", "First, press the yellow tape firmly\nalong the cabinet edge."),
    ("PULL DOWN TO COVER", "Then pull the film down smoothly\nto cover the tile and countertop."),
    ("TEAR BY HAND", "Fix the far edge, pull tight, and tear it by hand.\nNo scissors."),
    ("PAINT STAYS ON FILM", "Paint and dust stay on the film,\nnot on your furniture."),
    ("PEEL CLEAN", "Peel it away. No damage, no sticky residue,\nand no cleanup."),
    ("FASTER MASKING. LESS CLEANUP.", "One roll, faster masking, and far less cleanup.\nTry pre-taped masking film on your next project."),
]


def wrap_pixels(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    wrapped: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            candidate = word if not line else f"{line} {word}"
            box = draw.textbbox((0, 0), candidate, font=font, stroke_width=5)
            if box[2] - box[0] <= max_width:
                line = candidate
            else:
                if line:
                    wrapped.append(line)
                line = word
        if line:
            wrapped.append(line)
    return "\n".join(wrapped)


def centered_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, y: int, fill: str, spacing: int) -> None:
    box = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, stroke_width=5, align="center")
    w = box[2] - box[0]
    h = box[3] - box[1]
    x = (WIDTH - w) // 2
    pad_x, pad_y = 28, 18
    draw.rounded_rectangle(
        (x - pad_x, y - pad_y, x + w + pad_x, y + h + pad_y),
        radius=20,
        fill=(0, 0, 0, 105),
    )
    draw.multiline_text(
        (x, y), text, font=font, fill=fill, spacing=spacing,
        stroke_width=5, stroke_fill=(18, 18, 18, 255), align="center",
    )


for index, (title, caption) in enumerate(SCENES, start=1):
    image = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    title = wrap_pixels(draw, title, TITLE_FONT, 920)
    caption = wrap_pixels(draw, caption, CAPTION_FONT, 900)
    centered_text(draw, title, TITLE_FONT, 115, "#FFD800", 8)
    cap_box = draw.multiline_textbbox((0, 0), caption, font=CAPTION_FONT, spacing=12, stroke_width=5, align="center")
    cap_h = cap_box[3] - cap_box[1]
    centered_text(draw, caption, CAPTION_FONT, HEIGHT - 145 - cap_h, "#FFFFFF", 12)
    image.save(OUT / f"scene-{index:02d}.png")
