"""
main.py — ClearLane API + web.

ENDPOINTS
  GET  /                      overview / pitch page
  GET  /console              live obstruction + dispatch console
  GET  /api/segments         corridor choke segments + crews
  GET  /api/obstruction      obstruction-minutes (total / per-segment / per-class)
  GET  /api/dispatch         ad-hoc vs optimized playback + deltas
  POST /api/event-surge      Event-Surge playback + obstruction avoided
  GET  /api/fleet/advisories advisory zones a fleet would poll (from optimized run)
  GET  /api/health
"""
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.seed import seed
from app.feed import generate_events, obstruction_minutes
from app.dispatch import compare, simulate
from app.events import event_surge

app = FastAPI(title="ClearLane", version="2.0")
WEB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")


@app.on_event("startup")
def startup():
    init_db(); seed()
    print("[startup] ClearLane seeded.")


@app.get("/api/health")
def health(): return {"status": "ok"}


@app.get("/api/segments")
def segments():
    from app.db import get_conn
    c = get_conn()
    try:
        segs = [dict(r) for r in c.execute("SELECT * FROM segment").fetchall()]
        crews = [dict(r) for r in c.execute("SELECT * FROM crew").fetchall()]
        return {"segments": segs, "crews": crews}
    finally:
        c.close()


@app.get("/api/obstruction")
def obstruction(seed: int = 7):
    return obstruction_minutes(generate_events(seed=seed))


@app.get("/api/dispatch")
def dispatch(seed: int = 7, focal: str = "seg_mall_1"):
    return compare(seed=seed)


@app.post("/api/event-surge")
def surge(seed: int = 7):
    return event_surge(seed=seed)


@app.get("/api/fleet/advisories")
def fleet_advisories(seed: int = 7):
    """The real, pollable output a fleet (Flipkart/Blinkit) would consume."""
    from app.fleet import advisories
    return advisories(seed=seed)


@app.get("/")
def index(): return FileResponse(os.path.join(WEB, "index.html"))


@app.get("/console")
def console(): return FileResponse(os.path.join(WEB, "console.html"))


app.mount("/web", StaticFiles(directory=WEB), name="web")
