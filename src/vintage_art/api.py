#!/usr/bin/env python3
"""Small HTTP API for generating a final Vintage Art poster card."""
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from . import poster as poster_card

app = FastAPI(title="Vintage Art Poster API", version="0.1.0")


def remove_files(*paths):
    for path in paths:
        Path(path).unlink(missing_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-card")
async def generate_card(
    image: UploadFile = File(...),
    number: int = Form(1),
    date: str = Form("19 November 2026"),
    title: str = Form("Unforgettable Moments"),
    subtitle: str = Form("A small archive of scenes worth keeping."),
    story: str = Form("Some moments arrive quietly and stay forever."),
    author: str = Form("Shin"),
    location: str = Form("Phnom Penh, Cambodia"),
    mode: str = Form("mesh"),
    cell: int = Form(6),
    contrast: float = Form(1.5),
    bg: str = Form("#0A3EA8"),
    fg: str = Form("#F4C49A"),
):
    suffix = Path(image.filename or "image.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as input_file:
        input_path = input_file.name
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as output_file:
        output_path = output_file.name

    try:
        with open(input_path, "wb") as destination:
            shutil.copyfileobj(image.file, destination)

        poster_card.generate_card(
            input_path, output_path, title=title, number=number, date=date,
            subtitle=subtitle, story=story, author=author, location=location,
            mode=mode, cell=cell, contrast=contrast, bg=bg, fg=fg,
        )
    except Exception:
        remove_files(input_path, output_path)
        raise

    return FileResponse(
        output_path,
        media_type="image/png",
        filename="poster-card.png",
        background=BackgroundTask(remove_files, input_path, output_path),
    )

