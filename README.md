# ClearLane — Obstruction Intelligence & Dispatch for Bengaluru Traffic Police

**Theme:** Poor Visibility on Parking-Induced Congestion · Flipkart Gridlock Hackathon 2.0

Bengaluru already watches its roads with ~7,500 Safe City cameras and an AI command
centre (ASTraM), and adaptive signals (BATCS) on 165+ junctions. But all of it measures
congestion as **flow and length** — never the **stopped-vehicle cause**, and none of it
tells a scarce crew *where to go next*. ClearLane adds the missing layer.

### The loop
```
 CCTV ─▶ Obstruction-minute engine ─▶ Dispatch optimizer ─▶ Fleet Compliance API
 (measure how long each segment    (send crews to clear the   (delivery vehicles reroute
  is blocked, by vehicle class)     most vehicle-min/trip)      off enforced segments)
```

- **Measure** — `vision/detect_obstruction.py` turns any road video into *obstruction-minutes*
  per segment (real OpenCV; runs on a phone clip of a real choke point).
- **Rank** — segments by *live* blocking, not chronic reputation. A new layer for ASTraM.
- **Dispatch** — `app/dispatch.py` sends BTP's existing tow/officer crews to the segment that
  clears the most **vehicle-minutes per crew-hour** — the workflow BTP already runs (they tow
  near malls today), made optimal.
- **Comply** — `app/fleet.py` exposes advisory zones a fleet (Flipkart/Blinkit/Swiggy) polls,
  so the one *controllable* obstruction class stops blocking at the source — and converts each
  reroute into rupees + rider-minutes saved.

The `/console` is a **two-pane operations view**: left is the **BTP Control Room** (a schematic
junction with live dwell timers + a "clear here next" dispatch board); right is **Flipkart Fleet
Ops** (live rider reroutes + rupee tallies). A corridor strip at the bottom shows all 8 segments
and the A/B KPIs. It renders fully offline.

### Proof (from the live sim, same 4 crews, same evening)
| | Today (ad-hoc patrol) | ClearLane (optimized) |
|---|---|---|
| Residual obstruction-minutes | 491 | **239 (−51%)** |
| Vehicle-min cleared / crew-hour | 12.6 | **27.1 (+115%)** |
| Crew dispatches | 269 | **96** |
| Delivery obstruction avoided at source | — | **31.5 min** |

"Working harder, achieving less" — ad-hoc makes nearly 3× the trips and clears half as much.

## Run it
```bash
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --port 8000
# http://localhost:8000  →  overview ;  /console  →  live console
```
or `./run.sh`, or `docker compose up`.

> The console needs CARTO map tiles + Google Fonts (internet). Run it on your own machine
> to see the live map, crew animation and dual-line chart.

### Run the real detector on a real clip (the credibility moment)
```bash
python vision/make_sample_clip.py                                   # bundled smoke-test clip
python vision/detect_obstruction.py --video vision/sample_clip.mp4 --segment seg_mall_1
# -> sample_clip_events.json  (+ sample_clip_annotated.mp4 with live dwell timers)
```
For the demo, point `--video` at a phone clip of an actual Bengaluru choke point.

## Endpoints
`GET /` · `GET /console` · `GET /api/segments` · `GET /api/obstruction` ·
`GET /api/dispatch` (ad-hoc vs optimized) · `POST /api/event-surge` ·
`GET /api/fleet/advisories` · `GET /api/health`

## What's MVP vs production (stated honestly)
| Layer | This MVP | Production |
|---|---|---|
| Obstruction detection | OpenCV MOG2 + tracking (size-based class) | YOLOv8 + ByteTrack (precise class) |
| Data store | SQLite | PostgreSQL/PostGIS, fed by Safe City + ASTraM |
| Obstruction stream | parameter-driven model | live CCTV/ANPR analytics |
| Service | one FastAPI process | microservices behind ASTraM |

The metric (obstruction-minutes), the optimizer, and the event shape are identical across
both columns — the MVP swaps components, not logic. `app/feed.events_from_cctv()` already
ingests detector output with no special-casing.

## Layout
```
app/      db, seed, feed(+obstruction engine), dispatch(optimizer), fleet, events, main
vision/   detect_obstruction.py (real CV), make_sample_clip.py
web/      index.html (overview), console.html (live console)
tests/    test_dispatch.py
docs/     v1_vision_dossier.md (earlier full vision write-up)
```

`docs/v1_vision_dossier.md` is the earlier, broader product vision (curb-as-a-service). It is
kept for reference; ClearLane is the focused, deployable core that survived a hard teardown.
