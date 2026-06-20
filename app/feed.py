"""
feed.py — generates a realistic stream of obstruction events, and aggregates them
into the metric ASTraM lacks: OBSTRUCTION-MINUTES per segment, per time, per class.

WHY this is the core primitive: BTP's ASTraM measures congestion *length*; nobody
measures how long stopped vehicles block live lanes, or which vehicle class causes
it. obstruction_minutes(segment) = Σ dwell of stopped vehicles on the carriageway.

The generator is parameter-driven and clustered (chronic segments, dinner peak,
delivery share higher at commercial segments). In production this stream comes
from the CCTV detector in vision/detect_obstruction.py — same event shape.
"""
import random
from datetime import datetime, timedelta

from app.db import get_conn

CLASSES = ["delivery", "car", "auto", "other"]
# class -> (relative share at a commercial segment, typical dwell range seconds)
CLASS_DWELL = {
    "delivery": (90, 200),    # short-dwell drops
    "car":      (180, 900),   # someone parked to shop/eat
    "auto":     (60, 240),    # waiting for a fare
    "other":    (120, 600),
}


def _peak(hour):
    import math
    lunch = math.exp(-((hour - 13) ** 2) / 2.0)
    dinner = math.exp(-((hour - 20) ** 2) / 2.0)
    return 0.2 + lunch + 1.4 * dinner


def generate_events(seed=7, day_start=18, window_h=4):
    """Return obstruction events across all segments for one evening."""
    rng = random.Random(seed)
    c = get_conn()
    try:
        segs = c.execute("SELECT segment_id,chronic FROM segment").fetchall()
    finally:
        c.close()
    base = datetime(2026, 6, 5, day_start, 0, 0)
    events = []
    steps = int(window_h * 3600 / 30)   # 30s steps
    for s in range(steps):
        t = base + timedelta(seconds=30 * s)
        hour = day_start + (30 * s) / 3600
        peak = _peak(hour)
        for seg in segs:
            # expected new stopped vehicles in this 30s window
            lam = 0.018 * seg["chronic"] * peak
            n = _poisson(rng, lam)
            for _ in range(n):
                # delivery share rises with how commercial (chronic) the segment is
                w = {"delivery": 0.30 + 0.10 * (seg["chronic"] - 1),
                     "car": 0.34, "auto": 0.22, "other": 0.14}
                cls = _weighted(rng, w)
                lo, hi = CLASS_DWELL[cls]
                dwell = rng.uniform(lo, hi)
                events.append({"ts": t.timestamp(), "segment_id": seg["segment_id"],
                               "vehicle_class": cls, "dwell_s": dwell, "source": "model"})
    events.sort(key=lambda e: e["ts"])
    return events


def _poisson(rng, lam):
    # Knuth's algorithm (lam is small here)
    import math
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


def _weighted(rng, w):
    total = sum(w.values()); r = rng.random() * total; acc = 0
    for k, v in w.items():
        acc += v
        if r <= acc:
            return k
    return "other"


def events_from_cctv(json_path, base_ts=None):
    """Convert a detector output file (vision/detect_obstruction.py) into the SAME
    event shape the model produces — proving the CCTV pipeline drops straight in.
    The obstruction-minute engine and dispatch optimizer don't care which source
    produced the events."""
    import json
    from datetime import datetime
    raw = json.load(open(json_path))
    base = base_ts if base_ts is not None else datetime(2026, 6, 5, 20, 0, 0).timestamp()
    out = []
    for e in raw["events"]:
        cls = {"two_wheeler": "delivery", "lcv": "delivery",
               "car_auto": "car"}.get(e["vehicle_class"], "other")
        out.append({"ts": base + e["start_s"], "segment_id": e["segment_id"],
                    "vehicle_class": cls, "dwell_s": e["dwell_s"], "source": "cctv"})
    return out


def obstruction_minutes(events):
    """Aggregate total + per-segment + per-class obstruction-minutes."""
    per_seg, per_cls, total = {}, {}, 0.0
    for e in events:
        m = e["dwell_s"] / 60.0
        total += m
        per_seg[e["segment_id"]] = per_seg.get(e["segment_id"], 0.0) + m
        per_cls[e["vehicle_class"]] = per_cls.get(e["vehicle_class"], 0.0) + m
    return {
        "total_obstruction_minutes": round(total, 1),
        "per_segment": {k: round(v, 1) for k, v in per_seg.items()},
        "per_class": {k: round(v, 1) for k, v in per_cls.items()},
        "delivery_share_pct": round(100 * per_cls.get("delivery", 0) / total, 0) if total else 0,
    }


if __name__ == "__main__":
    from app.seed import seed
    seed()
    ev = generate_events()
    agg = obstruction_minutes(ev)
    print(f"OK: {len(ev)} obstruction events")
    print("total obstruction-minutes:", agg["total_obstruction_minutes"])
    print("delivery share:", agg["delivery_share_pct"], "%")
    print("per class:", agg["per_class"])
