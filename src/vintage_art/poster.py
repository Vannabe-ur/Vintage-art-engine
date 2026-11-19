#!/usr/bin/env python3
"""Build a printable editorial poster card from a Vintage Art Engine image.

Example:
    python poster-card.py raw.png unforgettable-moments.png
"""
import argparse
import os
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from . import engine


CARD_SIZE = (2400, 1600)  # 8 x 5.33 in at 300 DPI
PAPER = "#F5F1E8"
INK = "#111111"
MUTED = "#8C8C86"
ACCENT = "#EAB84D"
ACCENT_WIDTH = 120
ACCENT_HEIGHT = 70


def font(size, bold=False):
    candidates = (
        [
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\Arial_Bold.ttf",
        ]
        if bold
        else [r"C:\Windows\Fonts\arial.ttf"]
    )
    candidates += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def fit_cover(image, size):
    return ImageOps.fit(image.convert("RGB"), size, method=Image.Resampling.LANCZOS)


def wrap_to_width(draw, text, text_font, max_width):
    """Wrap text using rendered pixel width instead of character count."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if line and draw.textbbox((0, 0), candidate, font=text_font)[2] > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
    return "\n".join(lines)


def load_engine():
    return engine


def make_card(source, output, title, number, date, subtitle, story, author, location, accent):
    card_w, card_h = CARD_SIZE
    panel_w = int(card_w * 0.39)
    art_w = card_w - panel_w
    art = fit_cover(Image.open(source), (art_w, card_h))

    card = Image.new("RGB", CARD_SIZE, PAPER)
    card.paste(art, (panel_w, 0))
    draw = ImageDraw.Draw(card)

    margin_x = 120
    draw.text((margin_x, 120), "M", fill=INK, font=font(62, bold=True))
    draw.line((margin_x + 12, 220, margin_x + 105, 140), fill=INK, width=8)

    draw.text((margin_x, 330), f"{number:02d}", fill=INK, font=font(150, bold=True))
    draw.text((margin_x, 505), date.upper(), fill=MUTED, font=font(27), spacing=6)

    swatch = (
        panel_w - margin_x - ACCENT_WIDTH,
        card_h - 205,
        panel_w - margin_x,
        card_h - 205 + ACCENT_HEIGHT,
    )
    story_width = swatch[2] - margin_x

    text_top = 615
    title_font = font(74, bold=True)
    title_lines = wrap_to_width(draw, title.upper(), title_font, story_width)
    draw.multiline_text((margin_x, text_top), title_lines, fill=INK, font=title_font, spacing=4)
    title_box = draw.multiline_textbbox((margin_x, text_top), title_lines, font=title_font, spacing=4)

    subtitle_font = font(38, bold=True)
    subtitle_lines = wrap_to_width(draw, subtitle, subtitle_font, story_width)
    subtitle_top = title_box[3] + 28
    draw.multiline_text((margin_x, subtitle_top), subtitle_lines, fill=INK,
                        font=subtitle_font, spacing=8)
    subtitle_box = draw.multiline_textbbox((margin_x, subtitle_top), subtitle_lines,
                                           font=subtitle_font, spacing=8)

    story_font = font(30)
    wrapped = wrap_to_width(draw, story, story_font, story_width)
    story_top = subtitle_box[3] + 70
    draw.multiline_text((margin_x, story_top), wrapped, fill=INK, font=story_font,
                        spacing=16, align="left")

    byline = f"{author.upper()} | {location.upper()}"
    draw.text((margin_x, swatch[1] + 20), byline, fill=MUTED, font=font(25, bold=True))

    draw.rectangle(swatch, fill=accent)

    # Small registration line visually ties the generated artwork to the card layout.
    draw.line((panel_w - 24, 0, panel_w - 24, card_h), fill=INK, width=3)
    card.save(output, "PNG", dpi=(300, 300))


def generate_card(input_path, output_path, title="Unforgettable Moments", number=1,
                  date="19 November 2026", subtitle="A small archive of scenes worth keeping.",
                  story="Some moments arrive quietly and stay forever. Keep the light, the place, and the feeling.",
                  author="Shin", location="Phnom Penh, Cambodia", accent=ACCENT,
                  skip_engine=False, mode="mesh", width=1400, cell=6, contrast=1.5,
                  bg="#0A3EA8", fg="#F4C49A", seed=7):
    """Generate one final poster card, keeping the transformed image temporary."""
    processed_input = input_path
    temporary_path = None
    try:
        if not skip_engine:
            engine = load_engine()
            temporary_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            temporary_path = temporary_file.name
            temporary_file.close()
            engine.convert(input_path, temporary_path, width=width, cell=cell,
                           contrast=contrast, mode=mode, bg=bg, fg=fg, seed=seed)
            processed_input = temporary_path

        make_card(processed_input, output_path, title, number, date, subtitle,
                  story, author, location, accent)
    finally:
        if temporary_path:
            os.unlink(temporary_path)


def main():
    parser = argparse.ArgumentParser(description="Create a printable poster card from generated artwork.")
    parser.add_argument("input", help="Raw source image to transform")
    parser.add_argument("output", help="Output poster-card PNG")
    parser.add_argument("--title", default="Unforgettable Moments")
    parser.add_argument("--number", type=int, default=1)
    parser.add_argument("--date", default="19 November 2026")
    parser.add_argument("--subtitle", default="A small archive of scenes worth keeping.")
    parser.add_argument(
        "--story",
        default="Some moments arrive quietly and stay forever. Keep the light, the place, and the feeling.",
    )
    parser.add_argument("--author", default="Shin")
    parser.add_argument("--location", default="Phnom Penh, Cambodia")
    parser.add_argument("--accent", default=ACCENT, help="Accent swatch color, e.g. #EAB84D")
    parser.add_argument("--skip-engine", action="store_true",
                        help="Treat input as already-processed artwork")
    parser.add_argument("--mode", choices=["mesh", "dots", "dither"], default="mesh")
    parser.add_argument("--width", type=int, default=1400)
    parser.add_argument("--cell", type=int, default=6)
    parser.add_argument("--contrast", type=float, default=1.5)
    parser.add_argument("--bg", default="#0A3EA8")
    parser.add_argument("--fg", default="#F4C49A")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    generate_card(args.input, args.output, title=args.title, number=args.number,
                  date=args.date, subtitle=args.subtitle, story=args.story,
                  author=args.author, location=args.location, accent=args.accent,
                  skip_engine=args.skip_engine, mode=args.mode, width=args.width,
                  cell=args.cell, contrast=args.contrast, bg=args.bg, fg=args.fg,
                  seed=args.seed)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()

