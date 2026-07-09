"""Agentic AI Summit 2026 - Side Events display mock.

Serves an index plus three full-page previews of the Summit events page, each
with a different Side Events layout inserted directly above Our Community
Partners. Repurposed from the earlier speaker-page mock; Railway deploy config
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


@app.get("/option-a", response_class=HTMLResponse)
def option_a():
    return _page("option_a.html")


@app.get("/option-b", response_class=HTMLResponse)
def option_b():
    return _page("option_b.html")


@app.get("/option-c", response_class=HTMLResponse)
def option_c():
    return _page("option_c.html")


@app.get("/healthz")
def healthz():
    return JSONResponse({"ok": True})
