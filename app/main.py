"""Agentic AI Summit 2026 - Side Events display mock.

Serves an index plus full-page previews of proposed Summit page changes:
the approved compact Side Events layout and the pending sponsor additions. Repurposed from the earlier speaker-page mock; Railway deploy config
(app.main:app, /healthz) is unchanged.
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent
PAGES_DIR = BASE_DIR / "app" / "pages"
STATIC_DIR = BASE_DIR / "app" / "static"

app = FastAPI(title="Agentic AI Summit 2026 - Side Events Mock")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _page(name: str) -> HTMLResponse:
    return HTMLResponse((PAGES_DIR / name).read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)
def index():
    return _page("index.html")


@app.get("/sponsors", response_class=HTMLResponse)
def sponsors():
    return _page("sponsors.html")


@app.get("/option-c", response_class=HTMLResponse)
def option_c():
    return _page("option_c.html")


@app.get("/banner-a", response_class=HTMLResponse)
def banner_a():
    return _page("banner_a.html")


@app.get("/banner-b", response_class=HTMLResponse)
def banner_b():
    return _page("banner_b.html")


@app.get("/banner-c", response_class=HTMLResponse)
def banner_c():
    return _page("banner_c.html")


@app.get("/banner-preview", response_class=HTMLResponse)
def banner_preview():
    return _page("banner_b.html")


@app.get("/healthz")
def healthz():
    return JSONResponse({"ok": True})
