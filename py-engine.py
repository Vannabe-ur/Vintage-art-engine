#!/usr/bin/env python3
"""
py-engine.py
Convert any photo into a two-tone "woven mesh halftone" artwork:
solid cobalt blue + peach, with highlights rendered as a square screen/grid
that thickens into solid colour, and shadows dissolving into flat blue.

Usage:
    python py-engine.py image.png output.png
    python py-engine.py image.png output.png --cell 7 --contrast 1.6 --mode mesh
    python py-engine.py image.png output.png --mode dots --bg "#0A3EA8" --fg "#F4C49A"

Modes:
    mesh    square-hole screen (default, matches the reference look)
    dots    round halftone dots
    dither  blocky error-diffusion (pixel-art feel)

Requires: pip install pillow numpy
"""
import argparse
import numpy as np
from PIL import Image, ImageOps, ImageFilter


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def prepare_tone(img, width, contrast, gamma, blur, local, invert):
    """Grayscale tone map in [0,1] with strong, punchy contrast."""
    img = ImageOps.exif_transpose(img).convert("L")
    w, h = img.size
    img = img.resize((width, max(1, round(h * width / w))), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=1)
    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(blur))

    t = np.asarray(img, dtype=np.float32) / 255.0

    # Local contrast (poor-man's CLAHE): subtract a heavily blurred copy so
    # details survive in both sky and ground.
    if local > 0:
        big = np.asarray(
            img.filter(ImageFilter.GaussianBlur(max(width / 12, 4))),
            dtype=np.float32) / 255.0
        t = t + local * (t - big)

    t = np.clip(t, 0, 1) ** gamma
    t = np.clip((t - 0.5) * contrast + 0.5, 0, 1)
    if invert:
        t = 1 - t
    return t


def bayer(n):
    m = np.array([[0, 2], [3, 1]], dtype=np.float32)
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / (m.size)


def render_mesh(t, cell, grain, rng, floor, ceil):
    """Peach = outside a square hole whose size shrinks as tone rises."""
    H, W = t.shape
    yy, xx = np.mgrid[0:H, 0:W]
    u = ((xx % cell) + 0.5) / cell * 2 - 1
    v = ((yy % cell) + 0.5) / cell * 2 - 1
    d = np.maximum(np.abs(u), np.abs(v))          # 0 centre .. 1 edge

    tone = np.clip((t - floor) / max(ceil - floor, 1e-3), 0, 1)
    solid = tone > 0.98                            # pure highlights stay clean
    if grain > 0:
        tone = np.clip(tone + rng.normal(0, grain, t.shape), 0, 1)
    hole = np.sqrt(1 - tone)                       # hole half-size
    # thin grid lines appear at tone ~0.15 (hole≈0.92), solid at tone 1
    return ((d >= hole) & (tone > 0.12)) | solid


def render_dots(t, cell, grain, rng, floor, ceil):
    H, W = t.shape
    yy, xx = np.mgrid[0:H, 0:W]
    u = ((xx % cell) + 0.5) / cell * 2 - 1
    v = ((yy % cell) + 0.5) / cell * 2 - 1
    r = np.sqrt(u * u + v * v) / np.sqrt(2)
    tone = np.clip((t - floor) / max(ceil - floor, 1e-3), 0, 1)
    if grain > 0:
        tone = np.clip(tone + rng.normal(0, grain, t.shape), 0, 1)
    return r < np.sqrt(tone) * 0.95


def render_dither(t, cell, grain, rng, floor, ceil):
    """Blocky ordered dither: work at low-res, then scale up by `cell`."""
    H, W = t.shape
    h2, w2 = max(1, H // cell), max(1, W // cell)
    small = np.asarray(
        Image.fromarray((t * 255).astype(np.uint8)).resize((w2, h2), Image.BOX),
        dtype=np.float32) / 255.0
    tone = np.clip((small - floor) / max(ceil - floor, 1e-3), 0, 1)
    if grain > 0:
        tone = np.clip(tone + rng.normal(0, grain, tone.shape), 0, 1)
    thr = np.tile(bayer(4), (h2 // 4 + 1, w2 // 4 + 1))[:h2, :w2]
    out = tone > thr
    out = np.kron(out, np.ones((cell, cell), dtype=bool))
    full = np.zeros((H, W), dtype=bool)
    full[:out.shape[0], :out.shape[1]] = out[:H, :W]
    return full


def convert(path, out, width=1400, cell=6, contrast=1.5, gamma=1.0, blur=0.8,
            local=0.8, grain=0.07, floor=0.25, ceil=0.95, mode="mesh",
            bg="#0A3EA8", fg="#F4C49A", invert=False, scale=1, seed=7):
    rng = np.random.default_rng(seed)
    img = Image.open(path)
    t = prepare_tone(img, width, contrast, gamma, blur, local, invert)

    fn = {"mesh": render_mesh, "dots": render_dots, "dither": render_dither}[mode]
    mask = fn(t, cell, grain, rng, floor, ceil)

    canvas = np.empty(mask.shape + (3,), dtype=np.uint8)
    canvas[:] = hex_to_rgb(bg)
    canvas[mask] = hex_to_rgb(fg)

    result = Image.fromarray(canvas, "RGB")
    if scale != 1:
        result = result.resize((result.width * scale, result.height * scale),
                               Image.NEAREST)
    result.save(out)
    return result


def main():
    p = argparse.ArgumentParser(description="Image -> two-tone mesh halftone art")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--mode", choices=["mesh", "dots", "dither"], default="mesh")
    p.add_argument("--width", type=int, default=1400, help="working width (px)")
    p.add_argument("--cell", type=int, default=6, help="screen cell size (px)")
    p.add_argument("--contrast", type=float, default=1.5)
    p.add_argument("--gamma", type=float, default=1.0, help="<1 brighter, >1 darker")
    p.add_argument("--blur", type=float, default=0.8)
    p.add_argument("--local", type=float, default=0.8, help="local contrast boost")
    p.add_argument("--grain", type=float, default=0.07, help="noise for broken edges")
    p.add_argument("--floor", type=float, default=0.25, help="tones below -> solid bg")
    p.add_argument("--ceil", type=float, default=0.95, help="tones above -> solid fg")
    p.add_argument("--bg", default="#0A3EA8")
    p.add_argument("--fg", default="#F4C49A")
    p.add_argument("--invert", action="store_true")
    p.add_argument("--scale", type=int, default=1, help="nearest-neighbour upscale")
    p.add_argument("--seed", type=int, default=7)
    a = p.parse_args()
    convert(a.input, a.output, a.width, a.cell, a.contrast, a.gamma, a.blur,
            a.local, a.grain, a.floor, a.ceil, a.mode, a.bg, a.fg, a.invert,
            a.scale, a.seed)
    print(f"Saved {a.output}")


if __name__ == "__main__":
    main()