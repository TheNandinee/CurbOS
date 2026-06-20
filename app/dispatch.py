"""
dispatch.py — the OPTIMIZER. The defensible core of ClearLane.

BTP has a handful of tow/officer crews and picks where to send them by gut. We
run the same evening two ways on the SAME obstruction stream:

  'adhoc'     — crews patrol the chronically-worst spots, ignoring live state
                (a fair model of today's gut-based dispatch).
  'optimized' — crews are sent to the segment with the highest *marginal
                vehicle-minutes clearable per crew-minute*, and ClearLane pushes a
                fleet advisory to the segment under enforcement, so delivery
                vehicles (the controllable class) stop showing up there.

Outputs measurable KPIs BTP cares about:
  - residual obstruction-minutes (lower = clearer roads)
  - vehicle-minutes cleared per crew-hour (enforcement efficiency)
  - delivery obstruction-minutes avoided at source (the fleet-compliance effect)
Plus an animatable playback (crew legs, per-segment obstruction over time).
"""
import random
from app.db import get_conn
from app.geo import haversine_m
from app.feed import generate_events

DT = 30.0                 # sim step seconds
CREW_SPEED_MPS = 6.0      # ~22 km/h response
SERVICE_S = 180.0         # time to clear/tow a segment
ENFORCE_WINDOW = 600.0    # advisory + deterrence after a crew acts (10 min)
P_COMPLY = 0.7            # delivery riders who reroute when a segment is enforced


def _load():
    c = get_conn()
    try:
        segs = {r["segment_id"]: dict(r)
                for r in c.execute("SELECT * FROM segment").fetchall()}
        crews = [dict(r) for r in c.execute("SELECT * FROM crew").fetchall()]
    finally:
        c.close()
    return segs, crews


def simulate(mode, seed=7, events=None, focal="seg_mall_1"):
    segs, crew_rows = _load()
    events = events if events is not None else generate_events(seed=seed)
    rng = random.Random(seed + (5 if mode == "optimized" else 0))

    t0 = events[0]["ts"]
    t1 = max(e["ts"] + e["dwell_s"] for e in events)

    # bucket events by step index
    by_step = {}
    for e in events:
        k = int((e["ts"] - t0) // DT)
        by_step.setdefault(k, []).append(e)

    active = {s: [] for s in segs}            # currently blocking items per segment
    residual_s = {s: 0.0 for s in segs}       # obstruction-seconds experienced
    residual_delivery_s = 0.0
    enforce_until = {s: 0.0 for s in segs}    # advisory/deterrence window end

    crews = []
    for cr in crew_rows:
        crews.append({"id": cr["crew_id"], "kind": cr["kind"],
                      "lat": cr["home_lat"], "lon": cr["home_lon"],
                      "state": "idle", "target": None, "free_ts": t0,
                      "leg": None})

    legs, dispatch_log, series = [], [], []
    advisories = []
    redirects = []          # ts of each delivery vehicle that complied away (optimized)
    focal_occ = []          # per-step occupancy of the focal junction (for the schematic)
    cleared_vmin = 0.0
    delivery_avoided_s = 0.0
    crew_busy_s = 0.0

    nsteps = int((t1 - t0) / DT) + 1
    for k in range(nsteps):
        t = t0 + k * DT

        # 1) arrivals (with fleet compliance in optimized mode)
        for e in by_step.get(k, []):
            sid = e["segment_id"]
            if (mode == "optimized" and e["vehicle_class"] == "delivery"
                    and t < enforce_until[sid] and rng.random() < P_COMPLY):
                delivery_avoided_s += e["dwell_s"]
                redirects.append(t)            # a rider rerouted off an enforced segment
                continue
            active[sid].append({"remove": e["ts"] + e["dwell_s"],
                                "cls": e["vehicle_class"], "arr": e["ts"]})

        # 2) natural departures
        for sid in segs:
            active[sid] = [it for it in active[sid] if it["remove"] > t]

        # 3) accumulate obstruction-minutes
        for sid in segs:
            residual_s[sid] += len(active[sid]) * DT
            residual_delivery_s += sum(1 for it in active[sid] if it["cls"] == "delivery") * DT

        # 4) crews
        targeted = {c["target"] for c in crews if c["state"] == "enroute"}
        for c in crews:
            if c["state"] == "service" and t >= c["free_ts"]:
                c["state"] = "idle"
            if c["state"] == "enroute" and t >= c["leg"]["arrive"]:
                sid = c["target"]
                gain = sum(max(0.0, it["remove"] - t) for it in active[sid]) / 60.0
                cleared_vmin += gain
                n = len(active[sid])
                active[sid] = []
                enforce_until[sid] = t + ENFORCE_WINDOW
                advisories.append({"seg": sid, "start": t, "end": t + ENFORCE_WINDOW})
                c["lat"], c["lon"] = segs[sid]["lat"], segs[sid]["lon"]
                c["state"] = "service"; c["free_ts"] = t + SERVICE_S; c["target"] = None
                dispatch_log.append({"t": t, "crew": c["id"], "seg": sid,
                                     "vehicles": n, "vmin": round(gain, 1)})
            if c["state"] == "idle":
                tgt = _pick(mode, c, segs, active, t, targeted)
                if tgt:
                    targeted.add(tgt)
                    dist = haversine_m(c["lat"], c["lon"], segs[tgt]["lat"], segs[tgt]["lon"])
                    travel = max(DT, dist / CREW_SPEED_MPS)
                    c["state"] = "enroute"; c["target"] = tgt
                    c["leg"] = {"from": {"lat": c["lat"], "lon": c["lon"]},
                                "to": {"lat": segs[tgt]["lat"], "lon": segs[tgt]["lon"]},
                                "depart": t, "arrive": t + travel}
                    legs.append({"crew": c["id"], "kind": c["kind"], "seg": tgt, **c["leg"]})
            if c["state"] in ("enroute", "service"):
                crew_busy_s += DT

        # 5) sample for animation (every 60s) + focal junction occupancy (every 30s)
        if k % 2 == 0:
            series.append({"t": t,
                           "active": {s: len(active[s]) for s in segs},
                           "residual_min": round(sum(residual_s.values()) / 60.0, 1)})
        if focal in active:
            focal_occ.append({"t": t,
                              "vehicles": [{"cls": it["cls"], "arr": it["arr"]}
                                           for it in active[focal]]})

    window_h = (t1 - t0) / 3600.0
    crew_hours = len(crews) * window_h
    totals = {
        "residual_obstruction_minutes": round(sum(residual_s.values()) / 60.0, 1),
        "residual_delivery_minutes": round(residual_delivery_s / 60.0, 1),
        "cleared_vehicle_minutes": round(cleared_vmin, 1),
        "cleared_per_crew_hour": round(cleared_vmin / crew_hours, 1) if crew_hours else 0,
        "delivery_minutes_avoided": round(delivery_avoided_s / 60.0, 1),
        "crews": len(crews), "window_h": round(window_h, 1),
        "dispatches": len(dispatch_log),
    }
    return {"mode": mode, "t_start": t0, "t_end": t1, "focal": focal,
            "segments": [{"segment_id": s, **{k: segs[s][k] for k in ("name", "lat", "lon", "chronic")}} for s in segs],
            "crews": [{"id": c["id"], "kind": c["kind"]} for c in crews],
            "legs": legs, "series": series, "dispatch_log": dispatch_log,
            "advisories": advisories, "redirects": redirects, "focal_occupancy": focal_occ,
            "totals": totals}


def _pick(mode, crew, segs, active, t, targeted):
    """Choose the next segment for an idle crew."""
    best, best_val = None, 0.0
    for sid, s in segs.items():
        if sid in targeted:
            continue
        if mode == "adhoc":
            # gut-based: prioritise chronically-bad spots, nearest first; ignores live state
            dist = haversine_m(crew["lat"], crew["lon"], s["lat"], s["lon"])
            val = s["chronic"] * 1000.0 - dist     # chronic dominates, distance breaks ties
        else:
            n = len(active[sid])
            if n == 0:
                continue
            rem = sum(max(0.0, it["remove"] - t) for it in active[sid]) / 60.0
            dist = haversine_m(crew["lat"], crew["lon"], s["lat"], s["lon"])
            cost_min = (dist / CREW_SPEED_MPS + SERVICE_S) / 60.0
            val = rem / cost_min                   # vehicle-minutes clearable per crew-minute
        if val > best_val:
            best, best_val = sid, val
    return best


def compare(seed=7):
    events = generate_events(seed=seed)
    adhoc = simulate("adhoc", seed=seed, events=events)
    opt = simulate("optimized", seed=seed, events=events)
    a, o = adhoc["totals"], opt["totals"]
    resid_saved = round(a["residual_obstruction_minutes"] - o["residual_obstruction_minutes"], 1)
    resid_pct = round(100 * resid_saved / a["residual_obstruction_minutes"], 0) if a["residual_obstruction_minutes"] else 0
    eff_gain = round(100 * (o["cleared_per_crew_hour"] - a["cleared_per_crew_hour"]) / a["cleared_per_crew_hour"], 0) if a["cleared_per_crew_hour"] else 0
    return {"adhoc": adhoc, "optimized": opt,
            "residual_saved_minutes": resid_saved,
            "residual_reduction_pct": resid_pct,
            "efficiency_gain_pct": eff_gain,
            "delivery_minutes_avoided": o["delivery_minutes_avoided"],
            "t_start": min(adhoc["t_start"], opt["t_start"]),
            "t_end": max(adhoc["t_end"], opt["t_end"])}


if __name__ == "__main__":
    import json
    from app.seed import seed as do_seed
    do_seed()
    r = compare()
    for m in ("adhoc", "optimized"):
        print(m, json.dumps(r[m]["totals"]))
    print("residual reduction:", r["residual_reduction_pct"], "%")
    print("efficiency gain (cleared/crew-hr):", r["efficiency_gain_pct"], "%")
    print("delivery obstruction avoided at source:", r["delivery_minutes_avoided"], "min")
