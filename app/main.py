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


def _norm_name(n):
    import re
    return re.sub(r'[^a-z]', '', (n or '').lower())


def build_mainstage_pool(data):
    """Mainstage speaker pool with Linda's edits: drop Sanja Fidler (now Frontier),
    pin Ion Stoica first. Card order otherwise follows speakers.json directly."""
    mains = [s for s in data["speakers"] if s.get("stage") == "Main"]
    mains = [s for s in mains if _norm_name(s["name"]) != _norm_name("Sanja Fidler")]
    # pin Ion Stoica first
    mains.sort(key=lambda s: 0 if _norm_name(s["name"]) == _norm_name("Ion Stoica") else 1)
    return mains


def _frontier_meta_index():
    """Map normalized speaker name -> {headshot, link} from frontier.json, which
    has both for all original Frontier speakers. Includes aliases for agenda-vs-
    frontier.json spelling differences so matches don't fail on spelling."""
    idx = {}
    try:
        with open(FRONTIER_PATH) as f:
            for s in json.load(f)["speakers"]:
                idx[_norm_name(s["name"])] = {
                    "headshot": s.get("headshot"), "link": s.get("link"),
                }
    except Exception:
        pass
    # agenda spelling -> frontier.json spelling (same person, different spelling)
    spelling_alias = {
        "shivakasiviswanthan": "shivakasiviswanathan",
        "jonravshene": "jonravshende",
        "professorjohnamcdermid": "johnamcdermid",
        "johnamcdermid": "johnamcdermid",
    }
    for agenda_key, fr_key in spelling_alias.items():
        if fr_key in idx:
            idx.setdefault(agenda_key, idx[fr_key])
    # New agenda-only speakers not in frontier.json: headshot + link sourced
    # separately (per Linda). Headshot files added to static/img/speakers/.
    extra = {
        "joshalbrecht": {"headshot": "josh_albrecht.png", "link": "https://joshalbrecht.com/"},
        "vincentsunnchen": {"headshot": "vincent_sunn_chen.png", "link": "https://snorkel.ai/author/vincent-chen/"},
        "vijayganesh": {"headshot": "vijay_ganesh.png", "link": "https://www.cc.gatech.edu/people/vijay-ganesh"},
        "lilatretikov": {"headshot": "lila_tretikov.png", "link": "https://www.nea.com/team/lila-tretikov"},
        "silasalberti": {"headshot": "silas_alberti.png", "link": "https://sil.as/"},
        "chenguangwang": {"headshot": "chenguang_wang.png", "link": "https://cgraywang.github.io/"},
        "alexobadia": {"headshot": "alex_obadia.png", "link": "https://alexobadia.com/(%E3%83%84)/about"},
        "tudorachim": {"headshot": "tudor_achim.png", "link": "https://cs.stanford.edu/~tachim/"},
        "boli": {"headshot": "bo_li.png", "link": "https://www.linkedin.com/in/drboli"},
        # Atlas Saturday workshop presenters (agenda-only; headshots + links per Linda)
        "lovrepesut": {"headshot": "lovre_pesut.png", "link": "https://lov.re/"},
        "muhammadhashmi": {"headshot": "muhammad_hashmi.png", "link": "https://www.linkedin.com/in/mu-hash/"},
        "devinajain": {"headshot": "devina_jain.png", "link": "https://www.linkedin.com/in/devina-jain-088aba86"},
        "zachmueller": {"headshot": "zach_mueller.png", "link": "https://www.linkedin.com/in/zachary-mueller-135257118/"},
        "chuanli": {"headshot": "chuan_li.png", "link": "https://github.com/chuanli11"},
        "brandonmiddleton": {"headshot": "brandon_middleton.png", "link": "https://dschool.stanford.edu/directory/brandon-middleton"},
    }
    for k, v in extra.items():
        idx[k] = v
    return idx


def _headshot_index():
    """Back-compat: name -> headshot only (delegates to the meta index)."""
    return {k: v["headshot"] for k, v in _frontier_meta_index().items() if v.get("headshot")}


def build_frontier_combined():
    """Option D: all Frontier speakers as one combined list, in frontier.json order."""
    with open(FRONTIER_PATH) as f:
        return json.load(f)["speakers"]


def paginate_speakers(speakers, num_pages=3, cols=4):
    """Split a speaker list into `num_pages` balanced pages, nudging counts so no
    page ends with a lone single card on the last row (mirrors option-a-paged)."""
    total = len(speakers)
    base = total // num_pages
    counts = [base] * num_pages
    for i in range(total - base * num_pages):
        counts[i] += 1
    for i in range(num_pages - 1):
        if counts[i] % cols == 1:
            counts[i] += 1
            counts[i + 1] -= 1
    if counts[-1] % cols == 1 and counts[-1] > 1:
        counts[-2] += 1
        counts[-1] -= 1
    pages, start = [], 0
    for c in counts:
        pages.append(speakers[start:start + c])
        start += c
    return pages


def build_frontier_by_stage():
    """Option E: Frontier speakers grouped per stage, derived from the agenda data
    (reliable per-stage order). Headshots AND profile links matched by name from
    frontier.json (which has both for all original Frontier speakers)."""
    fa = load_frontier_agenda()
    meta = _frontier_meta_index()
    groups = []
    for st in fa["stages"]:
        speakers = []
        seen = set()
        session_idx = 0   # running session order within the stage (across days)
        row_idx = 0       # running row order, for stable final tiebreak
        for day in st["days"]:
            for e in day["entries"]:
                if e["type"] not in ("Session", "Workshop"):
                    continue
                session_idx += 1
                for s in e.get("speakers", []):
                    key = _norm_name(s["name"])
                    if key in seen:
                        continue
                    seen.add(key)
                    m = meta.get(key, {})
                    speakers.append({
                        "name": s["name"], "title": s.get("title"),
                        "org": s.get("org"), "stage": "Frontier",
                        "headshot": m.get("headshot"), "link": m.get("link"),
                        # sort keys (per Linda): length desc (15>10>5), then session
                        # order, then sheet row order. Stripped before returning.
                        "_len": s.get("length") or 0,
                        "_sess": session_idx,
                        "_row": row_idx,
                    })
                    row_idx += 1
        # Significance sort for the speaker cards: longest talks first, ties broken
        # by session order, then original row order. Agenda timeline is unaffected
        # (this only reorders the speaker-card list).
        speakers.sort(key=lambda sp: (-sp["_len"], sp["_sess"], sp["_row"]))
        for sp in speakers:
            del sp["_len"]; del sp["_sess"]; del sp["_row"]
        groups.append({"stage": st["stage"], "speakers": speakers})
    return groups


def load_agenda():
    with open(AGENDA_PATH) as f:
        return json.load(f)


def load_frontier_agenda():
    with open(FRONTIER_AGENDA_PATH) as f:
        return json.load(f)


def _frontier_entry_to_common(e):
    """Normalize a frontier_agenda entry into the same shape option_a's macro uses
    (type/session/start/color/speakers/...)."""
    if e["type"] == "Session":
        return {
            "type": "Focus Talks" if e.get("title") else "Focus Talks",
            "session": e.get("title") or None,
            "start": e.get("start"),
            "color": "blue",
            "speakers": e.get("speakers", []),
        }
    if e["type"] == "Workshop":
        return {
            "type": e.get("title") or e.get("label", "Workshop"),
            "session": None,
            "start": e.get("start"),
            "color": "magenta",
            "speakers": e.get("speakers", []),
        }
    if e["type"] == "Lunch":
        return {
            "type": "Lunch", "session": None,
            "label": e.get("label", "Lunch"),
            "start": e.get("start"), "color": "amber", "speakers": [],
        }
    if e["type"] == "Reception":
        return {
            "type": "Reception", "session": None,
            "label": e.get("label", "Reception"),
            "start": e.get("start"), "color": "amber", "speakers": [],
        }
    return {"type": e["type"], "session": None, "start": e.get("start"),
            "color": "blue", "speakers": e.get("speakers", [])}


def build_flat_tabs(agenda, frontier):
    """Option A (flat): Mainstage Sat | Mainstage Sun | Atlas | Nexus | Horizon.
    Each tab = one panel of timeline entries. Frontier stages that span 2 days
    stack their days inside the panel with a date divider."""
    tabs = []
    for day in agenda["days"]:
        tabs.append({"key": "m-" + day["key"], "label": day["label"],
                     "sections": [{"date": None, "entries": day["entries"]}]})
    for st in frontier["stages"]:
        sections = []
        for d in st["days"]:
            sections.append({
                "date": d["date"] if len(st["days"]) > 1 else None,
                "entries": [_frontier_entry_to_common(e) for e in d["entries"]],
            })
        tabs.append({"key": "f-" + st["stage"].lower(), "label": st["stage"],
                     "sections": sections})
    return tabs


def build_grouped_tabs(agenda, frontier):
    """Option D: stage tabs (Mainstage | Atlas | Nexus | Horizon), each with a
    Saturday/Sunday day sub-toggle."""
    groups = []
    # Mainstage group (its 'days' already split by day). Display name is now
    # "Plenary" (per Linda); internal key stays "mainstage" for JS tab linkage.
    groups.append({
        "key": "mainstage", "label": "Plenary",
        "days": [{"day": d["label"].split(" - ")[-1], "date": d["date"],
                  "entries": d["entries"], "key": d["key"]}
                 for d in agenda["days"]],
    })
    for st in frontier["stages"]:
        groups.append({
            "key": st["stage"].lower(), "label": st["stage"],
            "days": [{"day": d["day"], "date": d["date"],
                      "entries": [_frontier_entry_to_common(e) for e in d["entries"]],
                      "key": d["day"].lower()}
                     for d in st["days"]],
        })
    return groups



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
    agenda = load_agenda()
    frontier = load_frontier_agenda()
    return templates.TemplateResponse(
        request, "option_a.html",
        {"data": data, "agenda": agenda,
         "agenda_tabs": build_flat_tabs(agenda, frontier)})


@app.get("/option-d", response_class=HTMLResponse)
def option_d(request: Request):
    data = load_speakers()
    agenda = load_agenda()
    frontier = load_frontier_agenda()
    return templates.TemplateResponse(
        request, "option_d.html",
        {"data": data,
         "agenda_groups": build_grouped_tabs(agenda, frontier),
         "mainstage_speakers": build_mainstage_pool(data),
         "frontier_pages": paginate_speakers(build_frontier_combined(), num_pages=3)})


@app.get("/option-e", response_class=HTMLResponse)
def option_e(request: Request):
    data = load_speakers()
    agenda = load_agenda()
    frontier = load_frontier_agenda()
    return templates.TemplateResponse(
        request, "option_e.html",
        {"data": data,
         "agenda_groups": build_grouped_tabs(agenda, frontier),
         "mainstage_speakers": build_mainstage_pool(data),
         "frontier_stage_groups": build_frontier_by_stage()})


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
