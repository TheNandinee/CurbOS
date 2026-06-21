# CurbOS - Obstruction Intelligence & Dispatch Optimization Platform

<div align="center">

![CurbOS Banner](https://img.shields.io/badge/CurbOS-Traffic%20Intelligence-blue?style=for-the-badge)

**The Cause Behind the Congestion, Finally Measured**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/TheNandinee/CurbOS/issues)

*An obstruction-minute intelligence and dispatch-optimization layer that plugs into the cameras and
enforcement crews Bengaluru Traffic Police already operate — measuring, ranking, and clearing
parking-induced congestion at its source.*

[Features](#-features) • [Installation](#-installation) • [Usage](#-quick-start) • [Architecture](#-architecture) • [API](#-api-documentation) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-features)
- [System Architecture](#-architecture)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Modules](#-modules)
  - [Obstruction-Minute Engine](#obstruction-minute-engine)
  - [Dispatch Optimizer](#dispatch-optimizer)
  - [Fleet Compliance API](#fleet-compliance-api)
  - [Event-Surge](#event-surge)
  - [CCTV Obstruction Detector](#cctv-obstruction-detector)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Verified Results](#-verified-results)
- [Contributing](#-contributing)
- [Roadmap](#-roadmap)
- [License](#-license)
- [Meet the Team](#-meet-the-team)

---

## 🌟 Overview

**CurbOS** quantifies the one thing Bengaluru's existing traffic-tech stack doesn't measure: *why*
a road is jammed, not just that it is. BTP's ASTraM already tracks congestion length and vehicle
counts every 15 minutes; nobody tracks which stopped vehicle is holding which lane, for how long,
or what class it is. So scarce tow crews and officers get dispatched by gut feel to chronically bad
spots instead of to the worst live blockage right now.

CurbOS sits in that gap. It turns a stream of obstruction events — from real CCTV or a
model-generated evening — into a ranked dispatch board, optimizes the same enforcement crews BTP
already runs, and gives the one *controllable* obstruction source (delivery fleets) a reason to
self-comply instead of getting fined after the fact.

### 🎯 Mission

Make parking-induced congestion measurable and actionable on infrastructure cities already own —
no new cameras, no new authority, no new platform to adopt. Just a smarter version of the
obstruction-clearing operation BTP runs every evening.

### ✨ What Makes CurbOS Different

- **🎥 Plugs into existing infrastructure**: reads the same Safe-City-shaped camera feeds BTP
  already has; optimizes the same towing/officer dispatch BTP already performs.
- **🧮 Deterministic, auditable dispatch**: *which* crew goes *where* is a transparent
  marginal-value calculation (vehicle-minutes clearable per crew-minute) — not a black box.
- **📏 The missing primitive**: obstruction-minutes per segment, per class — the unit ASTraM's
  congestion-length metric doesn't capture.
- **🤝 Two buyers, one substrate**: BTP gets a smarter control room; delivery fleets get fewer
  challans/tows and faster drops — neither has to adopt something net-new.
- **🎬 Real computer vision, not vaporware**: a working OpenCV obstruction detector ships in this
  repo and produces the *same* event shape the model does — the CCTV path is a drop-in, not a slide.

---

## 🚀 Features

### 🧠 Obstruction Intelligence
- **Obstruction-minute aggregation**: total / per-segment / per-class dwell-time of stopped vehicles
- **Clustered, realistic demand**: chronic-segment weighting, dinner-peak modeling, class mix that
  shifts with how commercial a segment is
- **CCTV-compatible event shape**: model output and real-detector output are interchangeable

### 🚓 Dispatch Optimization
- **Two dispatch policies, same event stream**: `adhoc` (today's gut-based, chronic-spot patrol)
  vs `optimized` (max vehicle-minutes clearable per crew-minute)
- **Live playback**: crew legs, per-segment occupancy over time, dispatch log — fully animatable
- **Headline KPIs**: residual obstruction-minutes, cleared vehicle-minutes per crew-hour

### 🚚 Fleet Compliance
- **Pollable advisory zones**: segments currently under enforcement, with start/end windows
- **Transparent economics**: every rupee figure traces back to a stated, overridable assumption
  (challan probability/cost, tow probability/cost, rider-minute value)

### 🏟️ Event-Surge
- **Predictable-event pre-staging**: amplifies obstruction near a venue (e.g. an RCB match at
  Chinnaswamy) and compares reactive vs pre-staged dispatch
- **Reports avoided residual obstruction**, not just raw demand

### 🎥 Real Computer Vision
- **MOG2 background subtraction + centroid tracking** with a stationarity test tolerant of
  transient merges from passing traffic
- **Bundled sample clip generator** so the detector runs out of the box

---

## 🏗️ Architecture

```
CurbOS/
│
├── app/                          # FastAPI backend — the deployed unit
│   ├── main.py                   # Route definitions, app startup/seed
│   ├── db.py                     # SQLite schema (segment, crew, obstruction_event)
│   ├── seed.py                   # Real Indiranagar/CMH Rd corridor + 4 BTP crews
│   ├── feed.py                   # Obstruction-event generator + obstruction-minute engine
│   ├── dispatch.py                # The optimizer — adhoc vs optimized simulation
│   ├── events.py                  # Event-Surge — pre-staged dispatch around venues
│   ├── fleet.py                   # Fleet Compliance API + ₹ economics
│   └── geo.py                     # Haversine distance for crew routing
│
├── vision/                       # Real CCTV obstruction detection
│   ├── detect_obstruction.py     # OpenCV detector → obstruction events
│   └── make_sample_clip.py       # Generates a synthetic test clip
│
├── web/                           # Frontend — required for the app to boot
│   ├── index.html                 # Landing / pitch page
│   └── console.html                # Live map + BTP Control Room + Flipkart Fleet Ops
│
├── tests/
│   └── test_dispatch.py          # Concurrency + correctness tests
│
├── docs/
│   ├── GUIDE.md                  # Build & demo walkthrough
│   └── v1_vision_dossier.md      # Production-scale SRS (curb-marketplace v1)
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.sh
└── README.md
```

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Database** | SQLite (WAL mode) |
| **Optimization** | Deterministic marginal-value dispatch (no ML in the decision layer) |
| **Computer Vision** | OpenCV (MOG2 background subtraction, centroid tracking) |
| **Frontend** | Vanilla JS + Canvas (no build step, no framework) |
| **Testing** | Pytest |
| **Deployment** | Docker, Docker Compose |

This MVP is deliberately zero-infrastructure for a corridor-scale pilot. The production-scale
design (PostgreSQL/PostGIS, Kafka, an ST-GNN demand forecaster, Kubernetes) is documented in
[`docs/v1_vision_dossier.md`](docs/v1_vision_dossier.md) — this repo is the buildable subset of it.

---

## 💻 Installation

### Prerequisites
- Python 3.11+
- pip
- Docker (optional, for containerized deployment)

### Local Installation

```bash
# Clone the repository
git clone https://github.com/TheNandinee/CurbOS.git
cd CurbOS

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed the database (real corridor + crews)
python -m app.seed

# Start the app
uvicorn app.main:app --port 8000
```

### Docker Installation

```bash
# Build and run with Docker Compose
docker compose up --build

# Or build and run manually
docker build -t curbos .
docker run -p 8000:8000 curbos
```

Either way, the database is (re)seeded automatically at startup — `app/main.py` calls `seed()`
in its `@app.on_event("startup")` hook, so there's no separate migration step.

---

## 🎯 Quick Start

### Using the modules directly (Python)

```python
from app.seed import seed
from app.feed import generate_events, obstruction_minutes
from app.dispatch import compare
from app.fleet import advisories

seed()  # loads the 8-segment corridor + 4 enforcement crews

# Measure obstruction
events = generate_events(seed=7)
agg = obstruction_minutes(events)
print(f"Total obstruction-minutes: {agg['total_obstruction_minutes']}")
print(f"Delivery share: {agg['delivery_share_pct']}%")

# Compare ad-hoc vs optimized dispatch
result = compare(seed=7)
print(f"Efficiency gain: {result['efficiency_gain_pct']}%")
print(f"Residual reduction: {result['residual_reduction_pct']}%")

# Pull fleet advisory zones + economics
adv = advisories(seed=7)
print(f"₹ saved this evening: {adv['economics']['rupees_saved_evening']}")
```

### Using the API

```bash
# Start the server
uvicorn app.main:app --port 8000

# Compare dispatch policies
curl http://localhost:8000/api/dispatch

# Pre-stage crews around a predictable event
curl -X POST http://localhost:8000/api/event-surge

# Pull fleet advisory zones
curl http://localhost:8000/api/fleet/advisories
```

### Browser
- **http://localhost:8000** — overview / pitch page
- **http://localhost:8000/console** — live operations console

---

## 📦 Modules

### Obstruction-Minute Engine

The primitive ASTraM lacks: `obstruction_minutes(segment) = Σ dwell(stopped vehicles)`.

```python
from app.feed import generate_events, obstruction_minutes

events = generate_events(seed=7, day_start=18, window_h=4)  # one evening, 8 segments
agg = obstruction_minutes(events)
# {'total_obstruction_minutes': ..., 'per_segment': {...},
#  'per_class': {'delivery': ..., 'car': ..., 'auto': ..., 'other': ...},
#  'delivery_share_pct': ...}
```

Delivery is honestly a **minority** of obstruction-minutes (~17% on the seeded corridor) — that's
the point: the dispatch optimizer clears everything, the Fleet Compliance API targets only the
slice that's actually controllable by software.

### Dispatch Optimizer

The star of the repo. Runs the *same* obstruction stream two ways:

```python
from app.dispatch import simulate, compare

adhoc = simulate("adhoc", seed=7)        # chases chronically-bad spots, ignores live state
optimized = simulate("optimized", seed=7) # max vehicle-minutes clearable per crew-minute
result = compare(seed=7)
```

`optimized` mode also pushes a fleet advisory for any segment under active enforcement — delivery
vehicles in `by_step` that arrive during that window have a `P_COMPLY = 0.7` chance of rerouting,
which is where the Fleet Compliance economics come from.

### Fleet Compliance API

```python
from app.fleet import advisories, economics

result = advisories(seed=7)
# {'zones': [...], 'active_zone_count': ..., 'economics': {
#   'redirects', 'challans_avoided', 'tows_avoided',
#   'rider_minutes_saved', 'rupees_saved_evening', 'assumptions': {...} } }
```

Every assumption (`CHALLAN_PROB`, `CHALLAN_COST`, `TOW_PROB`, `TOW_COST`, `RIDER_MIN_VALUE`) is a
named constant at the top of `app/fleet.py` — swap in real fleet numbers and the whole panel
updates.

### Event-Surge

```python
from app.events import event_surge

result = event_surge(seed=7, venue_lat=12.9788, venue_lon=77.6430,
                      event_name="RCB vs CSK @ Chinnaswamy")
print(result["residual_obstruction_avoided"], "minutes avoided")
```

Amplifies obstruction near a venue using a distance-decayed weight, then compares reactive
ad-hoc dispatch against optimized dispatch on the *same* surged stream.

### CCTV Obstruction Detector

```bash
python vision/make_sample_clip.py
python vision/detect_obstruction.py --video vision/sample_clip.mp4 --segment seg_mall_1
```

Outputs JSON in the same event shape `app/feed.py` produces, so `events_from_cctv()` in
`app/feed.py` can feed real detector output straight into the obstruction engine and dispatch
optimizer — no schema translation layer.

---

## ⚙️ Configuration

CurbOS is intentionally config-free for the MVP — no `.env`, no external services, no API keys.
Every tunable value is a named constant at the top of its file, so it's visible and version-controlled
rather than hidden in environment variables:

| File | Constants | Purpose |
|---|---|---|
| `app/dispatch.py` | `DT`, `CREW_SPEED_MPS`, `SERVICE_S`, `ENFORCE_WINDOW`, `P_COMPLY` | Simulation step size, crew response speed, service time, advisory window, compliance rate |
| `app/feed.py` | `CLASS_DWELL` | Dwell-time ranges per vehicle class |
| `app/fleet.py` | `CHALLAN_PROB`, `CHALLAN_COST`, `TOW_PROB`, `TOW_COST`, `RIDER_MIN_VALUE` | Fleet economics assumptions |
| `app/seed.py` | `SEGMENTS`, `CREWS` | The corridor geometry and enforcement resources |

The only environment-style setting is the Docker port mapping (`-p 8000:8000`).

---

## 📚 API Documentation

### Segments & Crews
```http
GET /api/segments

Response: 200 OK
{
  "segments": [{"segment_id": "seg_mall_1", "name": "Mall frontage (drop-off)",
                "lat": 12.9693, "lon": 77.6436, "chronic": 2.6}, ...],
  "crews": [{"crew_id": "tow_1", "kind": "tow", "home_lat": ..., "home_lon": ...}, ...]
}
```

### Obstruction-Minutes
```http
GET /api/obstruction?seed=7

Response: 200 OK
{
  "total_obstruction_minutes": 644.0,
  "per_segment": {"seg_mall_1": 112.3, ...},
  "per_class": {"delivery": 108.9, "car": 219.4, "auto": 142.1, "other": 173.6},
  "delivery_share_pct": 17.0
}
```

### Dispatch Comparison
```http
GET /api/dispatch?seed=7&focal=seg_mall_1

Response: 200 OK
{
  "adhoc": { "totals": {...}, "legs": [...], "series": [...] },
  "optimized": { "totals": {...}, "legs": [...], "series": [...] },
  "residual_saved_minutes": ..., "residual_reduction_pct": ...,
  "efficiency_gain_pct": ..., "delivery_minutes_avoided": ...
}
```

### Event-Surge
```http
POST /api/event-surge?seed=7

Response: 200 OK
{
  "event": "RCB vs CSK @ Chinnaswamy",
  "impact_segments": ["seg_mall_1", ...],
  "residual_obstruction_avoided": 391.5,
  "delivery_minutes_avoided": ...
}
```

### Fleet Advisories
```http
GET /api/fleet/advisories?seed=7

Response: 200 OK
{
  "zones": [{"segment_id": "seg_mall_1", "name": "...", "start": ..., "end": ...}],
  "active_zone_count": 6,
  "economics": {"redirects": 14, "challans_avoided": 3.5, "tows_avoided": 0.7,
                "rider_minutes_saved": 53, "rupees_saved_evening": 3073,
                "assumptions": {...}}
}
```

### Health
```http
GET /api/health → {"status": "ok"}
```

Interactive Swagger docs are auto-generated by FastAPI at **`/docs`** and ReDoc at **`/redoc`**.

---

## 🧪 Testing

```bash
# Run the full suite
pytest tests/

# Run with verbose output
pytest tests/ -v
```

`tests/test_dispatch.py` fires concurrent reservation requests at the same bay/segment and asserts
**zero double-booking** — the correctness property the whole dispatch spine depends on.

---

## 🚀 Deployment

### Docker
```bash
docker build -t curbos .
docker run -d -p 8000:8000 --name curbos curbos
docker logs -f curbos
```

### Docker Compose
```bash
docker compose up -d --build
```

### Verifying a deployment
```bash
curl http://<host>:8000/api/health
# {"status":"ok"}
```

A from-scratch container build runs `python -m app.seed` during the image build (see
`Dockerfile`), and `app/main.py` reseeds again on every startup — so a fresh container is always
in a known, demo-ready state with no manual migration step.

---

## 📊 Verified Results

Measured directly from `app/dispatch.py` on the seeded Indiranagar/CMH Road corridor, 4 crews,
one evening — reproduce with `python -m app.dispatch`:

| Metric | Ad-hoc (today) | CurbOS (optimized) |
|---|---|---|
| Vehicle-minutes cleared / crew-hour | baseline | **+115%** |
| Residual obstruction-minutes | baseline | **−51%** |
| Crews used | 4 | 4 (same resource, better allocation) |

From `app/fleet.py` on the same run: **14 delivery riders redirected away from enforced segments,
≈₹3,073 saved in one corridor in one evening** under the stated economic assumptions (see
[Configuration](#-configuration)).

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Commit your changes (`git commit -m "Add your feature"`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Open a Pull Request

### Areas for Contribution
- 🎥 Production-grade vehicle classification in `vision/detect_obstruction.py` (currently size-based)
- 📡 A real CCTV ingestion adapter for `events_from_cctv()` in `app/feed.py`
- 🗺️ Multi-corridor support (currently one seeded corridor)
- 🧪 Expanded test coverage beyond the concurrency test

---

## 🗺️ Roadmap

### Current (MVP)
- ✅ Obstruction-minute engine
- ✅ Ad-hoc vs optimized dispatch comparison
- ✅ Fleet Compliance API with transparent economics
- ✅ Event-Surge pre-staging
- ✅ Real OpenCV obstruction detector
- ✅ Live two-pane operations console

### Pilot (4 weeks, 1 corridor)
- 🔄 Real CCTV feed in, obstruction-minutes measured before/after
- 🔄 One fleet's real challan/tow data replacing the stated assumptions

### Scale
- 📅 Corridor → ASTraM module, citywide
- 📅 Fleet-wide Compliance API across Blinkit/Swiggy/Amazon alongside Flipkart/Ekart
- 📅 Production architecture per `docs/v1_vision_dossier.md` (Postgres/PostGIS, Kafka, ST-GNN, Kubernetes)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 Nandinee

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 👥 Meet the Team

| **[Nandinee](https://github.com/TheNandinee)** |
| :---: |
| **Project Lead & Core Developer** |
| Built the obstruction engine, dispatch optimizer, fleet economics, and operations console. |

### Libraries & Tools

CurbOS is built on the shoulders of:
- [FastAPI](https://github.com/tiangolo/fastapi) — backend framework
- [Uvicorn](https://github.com/encode/uvicorn) — ASGI server
- [OpenCV](https://github.com/opencv/opencv) — obstruction detection
- [Pytest](https://github.com/pytest-dev/pytest) — testing framework

---

## ⭐ Star

If you find CurbOS interesting, consider giving it a star.

<a href="https://star-history.com/#TheNandinee/CurbOS&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=TheNandinee/CurbOS&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=TheNandinee/CurbOS&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=TheNandinee/CurbOS&type=Date" />
  </picture>
</a>

---

<div align="center">

**Built for the Flipkart Gridlock Hackathon 2.0**

[⬆ Back to Top](#-curbos---obstruction-intelligence--dispatch-optimization-platform)

</div>
