import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "speakers.json"
FRONTIER_PATH = BASE_DIR / "data" / "frontier.json"
AGENDA_PATH = BASE_DIR / "data" / "agenda.json"
FRONTIER_AGENDA_PATH = BASE_DIR / "data" / "frontier_agenda.json"

app = FastAPI(title="Agentic AI Summit - Speaker Page Mockup")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


def load_speakers():
    with open(DATA_PATH) as f:
        return json.load(f)


def load_frontier():
    with open(FRONTIER_PATH) as f:
        return json.load(f)


def load_agenda():
    with open(AGENDA_PATH) as f:
        return json.load(f)


def load_frontier_agenda():
    with open(FRONTIER_AGENDA_PATH) as f:
        return json.load(f)


@app.get("/frontier-agenda-flat", response_class=HTMLResponse)
def frontier_agenda_flat(request: Request):
    return templates.TemplateResponse(
        request, "frontier_agenda_flat.html",
        {"fa": load_frontier_agenda()})


@app.get("/frontier-agenda-toggle", response_class=HTMLResponse)
def frontier_agenda_toggle(request: Request):
    return templates.TemplateResponse(
        request, "frontier_agenda_toggle.html",
        {"fa": load_frontier_agenda()})


def frontier_sessions(frontier_data):
    """Group Frontier speakers by session, ordered by session_order then slot."""
    sessions = {}
    for s in frontier_data["speakers"]:
        sessions.setdefault(s["session"], []).append(s)
    ordered = sorted(sessions.items(), key=lambda kv: kv[1][0]["session_order"])
    for _, members in ordered:
        members.sort(key=lambda s: s["slot"])
    return ordered


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/option-a", response_class=HTMLResponse)
def option_a(request: Request):
    data = load_speakers()
    return templates.TemplateResponse(request, "option_a.html",
                                      {"data": data, "agenda": load_agenda()})


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
    data = load_frontier()
    ordered = frontier_sessions(data)
    return templates.TemplateResponse(
        request, "frontier.html", {"data": data, "sessions": ordered}
    )


@app.get("/option-a-frontier", response_class=HTMLResponse)
def option_a_frontier(request: Request):
    """Option A circle-grid: Main Stage grid + Frontier grouped by session."""
    main = load_speakers()
    frontier_data = load_frontier()
    return templates.TemplateResponse(
        request,
        "option_a_frontier.html",
        {
            "data": main,
            "main_speakers": main["speakers"],
            "sessions": frontier_sessions(frontier_data),
        },
    )


@app.get("/option-a-toggle", response_class=HTMLResponse)
def option_a_toggle(request: Request):
    """Option A with a Main / Frontier toggle."""
    main = load_speakers()
    frontier_data = load_frontier()
    return templates.TemplateResponse(
        request,
        "option_a_toggle.html",
        {
            "data": main,
            "main_speakers": main["speakers"],
            "sessions": frontier_sessions(frontier_data),
        },
    )


@app.get("/option-a-flat", response_class=HTMLResponse)
def option_a_flat(request: Request):
    """Option A flat list, no categories: Main + Frontier combined."""
    main = load_speakers()
    frontier_data = load_frontier()
    all_speakers = main["speakers"] + frontier_data["speakers"]
    return templates.TemplateResponse(
        request,
        "option_a_flat.html",
        {"data": main, "all_speakers": all_speakers},
    )


@app.get("/option-a-paged", response_class=HTMLResponse)
def option_a_paged(request: Request):
    """Option A circle-grid, combined list split into 3 pages (bottom pager).

    Drops the duplicate Main-stage Aditya Grover entry (he also appears as a
    Frontier speaker), and balances the 3-page split so no page ends with a
    lone single card in the 4-column grid.
    """
    main = load_speakers()
    frontier_data = load_frontier()
    all_speakers = main["speakers"] + frontier_data["speakers"]

    # Remove the Main-stage Aditya Grover (keep the Frontier instance, which
    # sits later in the list). Only the first matching Main entry is dropped.
    for i, s in enumerate(all_speakers):
        if s.get("name") == "Aditya Grover" and s.get("stage") == "Main":
            del all_speakers[i]
            break

    cols = 4
    num_pages = 3
    total = len(all_speakers)
    base = total // num_pages
    counts = [base] * num_pages
    for i in range(total - base * num_pages):
        counts[i] += 1
    # Nudge counts so no page ends with a single card on the last row.
    for i in range(num_pages - 1):
        if counts[i] % cols == 1:
            counts[i] += 1
            counts[i + 1] -= 1
    if counts[-1] % cols == 1 and counts[-1] > 1:
        counts[-2] += 1
        counts[-1] -= 1

    pages, start = [], 0
    for c in counts:
        pages.append(all_speakers[start:start + c])
        start += c

    return templates.TemplateResponse(
        request,
        "option_a_paged.html",
        {"data": main, "pages": pages, "num_pages": num_pages},
    )


@app.get("/healthz")
def healthz():
    return {"ok": True}
