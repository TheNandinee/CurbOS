# ClearLane — Build & Demo Guide

A walk-through of how the system is built, how to run it, and how to demo it so it
lands with a panel that includes Bengaluru Traffic Police.

## Phase 0 — The one idea
Parking-induced congestion is **stopped vehicles holding live lanes**. BTP can see the
jam but not *which 150 m is blocked, for how long, by whom* — so scarce crews patrol by
gut. ClearLane measures that, optimizes the crews, and turns the controllable class
(delivery) into a partner.

## Phase 1 — Obstruction-minute engine
`app/feed.py` produces an obstruction-event stream (chronic segments × dinner peak,
vehicle classes) and aggregates **obstruction-minutes** per segment/class. This is the
primitive ASTraM lacks (it measures congestion *length*, not *cause*).
```bash
python -m app.feed   # prints total obstruction-minutes + delivery share
```
Delivery is honestly a *minority* (~17%) of obstruction-minutes — that's the point:
the optimizer clears everything; the fleet API tackles the slice software can control.

## Phase 2 — Dispatch optimizer (the star)
`app/dispatch.py` runs the same evening two ways:
- **ad-hoc** — crews chase chronically-bad spots, ignoring live state (today's gut dispatch).
- **optimized** — crews go to max **vehicle-minutes clearable per crew-minute**; enforced
  segments broadcast a fleet advisory so delivery vehicles stop showing up.
```bash
python -m app.dispatch   # residual −51%, +115% cleared/crew-hour, same 4 crews
```

## Phase 3 — Real computer vision
`vision/detect_obstruction.py` measures obstruction-minutes from actual video
(MOG2 background subtraction + centroid tracking + a stationarity test that tolerates
transient merges from passing traffic). Output JSON matches the engine's event shape.
```bash
python vision/make_sample_clip.py
python vision/detect_obstruction.py --video vision/sample_clip.mp4 --segment seg_mall_1
```
**For the demo, run it on a real phone clip of a Bengaluru choke point.** A bounding box
with a ticking "BLOCKING 6.8s" timer is the single most convincing artifact you have.

## Phase 4 — The two-pane operations console
`app/main.py` serves the overview (`/`) and the console (`/console`). The console is
built for the two people who'd actually use ClearLane, side by side on one event stream:

- **Left — BTP Control Room:** a schematic junction view (the *Mall frontage* choke point)
  where stopped vehicles sit in the kerb lane as labelled chips with live dwell timers, a
  junction obstruction-minute counter, and a **dispatch board** ranking every segment with
  the recommended crew + ETA. Today = vehicles linger, board full of "waiting"; ClearLane =
  worst-first, crews "en route / on scene".
- **Right — Flipkart Fleet Ops:** a live **rider-advisory feed** and running **rupee tallies**
  (challans avoided, tows avoided, rider-minutes, ₹ saved tonight + annualised). All driven by
  the same redirects the optimiser produces.
- **Bottom — corridor strip:** all 8 segments as live bars (the "and it scales" coda) plus the
  headline A/B KPIs (+115% cleared/crew-hr, −51% residual) and the Event-Surge button.

```bash
uvicorn app.main:app --port 8000     # or ./run.sh / docker compose up
```
The junction view is a **labelled schematic** (driven by the model), not real CCTV — say so on
stage. The real OpenCV detector (`vision/`) stays in the repo as the production CCTV-ingestion
path. The console renders fully offline (no map tiles).

## The 90-second demo script
1. **Overview (`/`)** — "the jam has a cause nobody measures." Land on the proof stats.
2. **Launch console** — opens in *ClearLane* mode. Point at the **left**: a car blocking the
   Mall frontage for 8 minutes, the dispatch board sending `tow_2` to it. Then the **right**:
   rupees stacking as riders reroute.
3. **Toggle to *Today*** — same evening, gut patrol: dwell timers climb, the board fills with
   "⚠ waiting", the rupee counter flatlines ("riders stop wherever, get fined later").
   Say the numbers: **+115% cleared per crew-hour, −51% residual, ₹3k saved on one corridor / evening.**
4. **⚡ Pre-stage RCB match** — obstruction spikes near the venue; ClearLane positions crews early.
5. **Close:** "Left screen is what your control room acts on. Right screen is what it saves Flipkart.
   Same cameras you already own — zero new hardware."

## Talking points that survive scrutiny
- *Authority:* we don't price or dedicate curb; we feed ASTraM and aid the tow crews BTP
  already dispatches. No new powers needed.
- *Hardware:* ₹0 new — Safe City cameras already exist.
- *Measurability:* obstruction-minutes on the same camera, before/after. Testable in a 4-week,
  one-corridor pilot.
- *Why now:* Safe City live, ASTraM operational, towing being reinstated, q-commerce surging —
  all converged in 2024–25.

## Deploy a public demo link (optional)
Push to GitHub → Render.com → New Web Service → Build `pip install -r requirements.txt` →
Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Free tier is fine for judging.
