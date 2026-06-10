import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "speakers.json"
FRONTIER_PATH = BASE_DIR / "data" / "frontier.json"

app = FastAPI(title="Agentic AI Summit - Speaker Page Mockup")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


def load_speakers():
    with open(DATA_PATH) as f:
        return json.load(f)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/option-a", response_class=HTMLResponse)
def option_a(request: Request):
    data = load_speakers()
    return templates.TemplateResponse(request, "option_a.html", {"data": data})


@app.get("/option-b", response_class=HTMLResponse)
def option_b(request: Request):
    data = load_speakers()
    return templates.TemplateResponse(request, "option_b.html", {"data": data})


@app.get("/option-c", response_class=HTMLResponse)
def option_c(request: Request):
    data = load_speakers()
    return templates.TemplateResponse(request, "option_c.html", {"data": data})


@app.get("/frontier", response_class=HTMLResponse)
def frontier(request: Request):
    with open(FRONTIER_PATH) as f:
        data = json.load(f)
    # group speakers by session, preserving session_order then slot
    sessions = {}
    for s in data["speakers"]:
        sessions.setdefault(s["session"], []).append(s)
    ordered = sorted(
        sessions.items(),
        key=lambda kv: kv[1][0]["session_order"],
    )
    for _, members in ordered:
        members.sort(key=lambda s: s["slot"])
    return templates.TemplateResponse(
        request, "frontier.html", {"data": data, "sessions": ordered}
    )


@app.get("/healthz")
def healthz():
    return {"ok": True}
