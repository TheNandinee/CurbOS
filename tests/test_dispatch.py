"""
Tests for the two claims ClearLane stakes its pitch on:
  1. The optimizer clears more vehicle-minutes per crew-hour than ad-hoc, with
     the SAME crews on the SAME obstruction — and leaves less residual obstruction.
  2. CCTV detector output is interchangeable with the model feed (same shape),
     so the obstruction-minute engine runs on either.
Run:  python -m pytest -q   (or)   python -m tests.test_dispatch
"""
from app.seed import seed
from app.feed import generate_events, obstruction_minutes, events_from_cctv
from app.dispatch import compare, simulate


def test_optimizer_beats_adhoc():
    seed()
    r = compare(seed=7)
    a, o = r["adhoc"]["totals"], r["optimized"]["totals"]
    # more efficient per scarce crew-hour
    assert o["cleared_per_crew_hour"] > a["cleared_per_crew_hour"]
    # less obstruction left on the road
    assert o["residual_obstruction_minutes"] < a["residual_obstruction_minutes"]
    # same resource count (fair comparison)
    assert o["crews"] == a["crews"]
    # fleet compliance only happens in optimized mode
    assert o["delivery_minutes_avoided"] > 0
    assert a["delivery_minutes_avoided"] == 0


def test_obstruction_minutes_consistent():
    seed()
    ev = generate_events(seed=7)
    agg = obstruction_minutes(ev)
    # sum of per-class equals total (accounting identity)
    assert abs(sum(agg["per_class"].values()) - agg["total_obstruction_minutes"]) < 1.0
    assert 0 <= agg["delivery_share_pct"] <= 100


def test_cctv_events_interchangeable():
    seed()
    sample = [{"start_s": 5.0, "segment_id": "seg_mall_1",
               "vehicle_class": "lcv", "dwell_s": 120.0}]
    import json, tempfile, os
    p = os.path.join(tempfile.gettempdir(), "_cl_cctv.json")
    json.dump({"events": sample}, open(p, "w"))
    ev = events_from_cctv(p)
    assert ev and ev[0]["segment_id"] == "seg_mall_1"
    # the engine accepts CCTV events with no special-casing
    agg = obstruction_minutes(ev)
    assert agg["total_obstruction_minutes"] == 2.0  # 120s = 2 min


if __name__ == "__main__":
    test_optimizer_beats_adhoc()
    test_obstruction_minutes_consistent()
    test_cctv_events_interchangeable()
    print("OK: all tests passed")
