# Vintage Art Engine

Generate bold two-tone vintage artwork and turn it into printable memory poster cards.

![Example output](examples/output/ag-out.png)

## Project layout

```text
src/vintage_art/
├── engine.py       # Image transformation engine
├── poster.py       # Poster-card composition and CLI
└── api.py          # FastAPI prototype
examples/
├── input/          # Source photographs
└── output/         # Example generated artwork and cards
```

## Installation

Install the package and API dependencies in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\Activate.ps1   # PowerShell
python -m pip install -e ".[api]"
```

## Generate a poster card

The poster command accepts a raw image, runs it through the vintage engine internally, and saves only the final card:

```bash
vintage-art-card examples/input/image.png examples/output/card.png \
  --number 2 \
  --date "19 November 2026" \
  --title "Unforgettable Moments" \
  --subtitle "Happen, Stay with me" \
  --story "For the days we did not know would become memories." \
  --author "Shin" \
  --location "Phnom Penh, Cambodia"
```

The same command can be run without installing the console entry point:

```bash
python -m vintage_art.poster examples/input/image.png examples/output/card.png
```

Already-transformed artwork can be placed directly into the card with `--skip-engine`.

## Engine options

The poster command passes the main visual options through to the engine:

```bash
vintage-art-card examples/input/image.png examples/output/card.png \
  --mode dots \
  --cell 8 \
  --contrast 1.7 \
  --bg "#101820" \
  --fg "#F2AA4C"
```

Available modes are `mesh`, `dots`, and `dither`. Use `--help` to see all card and engine options.

## API prototype

Start the local API:

```bash
uvicorn vintage_art.api:app --reload
```

Generate a card from a raw image and receive only the final PNG:

```bash
curl -X POST http://127.0.0.1:8000/generate-card \
  -F "image=@examples/input/image.png" \
  -F "number=2" \
  -F "date=19 November 2026" \
  -F "title=Unforgettable Moments" \
  -F "subtitle=Happen, Stay with me" \
  -F "story=For the days we did not know would become memories." \
  -F "author=Shin" \
  -F "location=Phnom Penh, Cambodia" \
  -o examples/output/api-card.png
```

The API keeps the transformed image temporary and deletes it after the response.

## Poster-card fields

- `--number` - large card number.
- `--date` - muted date below the number.
- `--title` - changeable uppercase title.
- `--subtitle` - bold supporting line.
- `--story` - memory text or caption.
- `--author` and `--location` - muted metadata shown as `AUTHOR | LOCATION`.
- `--accent` - yellow accent-box color.

## How the engine works

1. Corrects image orientation and converts the source to grayscale.
2. Resizes and adjusts contrast, gamma, blur, and local detail.
3. Renders a mesh, dot, or dither mask.
4. Applies the selected two-color palette.
5. Places the result into the poster-card layout with typography and metadata.

## License

No license is currently specified for this repository.
