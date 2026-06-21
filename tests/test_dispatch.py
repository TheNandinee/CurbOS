"""
Dispatch correctness & robustness tests for CurbOS.

Replaces the old curb-bay "double-booking" test (a fossil of the abandoned
marketplace design) with the invariants the dispatch spine actually depends on:

  * determinism            - same seed -> identical numbers (no hidden RNG)
  * optimized >= ad-hoc    - worst-first routing really clears more
  * physical sanity        - you can never clear more obstruction than exists
  * class accounting        - per-class minutes sum to the total
  * Event-Surge effect     - pre-positioning avoids > 0 obstruction-minutes

Run:  pytest tests/ -v
"""
import math
import pytest

from app.seed import seed
from app.feed import generate_events, obstruction_minutes
from app.dispatch import compare, simulate
from app.events import event_surge

SEED = 7


@pytest.fixture(scope="module", autouse=True)
def _seeded_db():
    """Every test runs against the seeded corridor + crews."""
    seed()
    yield


# ----------------------------------------------------------------- determinism
def test_compare_is_deterministic():
    a = compare(seed=SEED)
    b = compare(seed=SEED)
    assert a["efficiency_gain_pct"] == b["efficiency_gain_pct"]
    assert a["residual_reduction_pct"] == b["residual_reduction_pct"]


def test_obstruction_is_deterministic():
    a = obstruction_minutes(generate_events(seed=SEED))
    b = obstruction_minutes(generate_events(seed=SEED))
    assert a["total_obstruction_minutes"] == b["total_obstruction_minutes"]


# ------------------------------------------------------- optimized beats ad-hoc
def test_optimized_clears_more_than_adhoc():
    """The core claim: worst-first routing clears more per crew-hour."""
    result = compare(seed=SEED)
    assert result["efficiency_gain_pct"] > 0, (
        "optimized dispatch should clear more vehicle-minutes per crew-hour "
        "than ad-hoc patrol"
    )


def test_optimized_leaves_less_residual():
    result = compare(seed=SEED)
    assert result["residual_reduction_pct"] > 0, (
        "optimized dispatch should leave less residual obstruction than ad-hoc"
    )


# -------------------------------------------------------------- physical sanity
def test_cannot_clear_more_than_exists():
    """
    You can never clear more obstruction-minutes than the evening generated.
    Guards against double-counting bugs in the simulator.
    """
    total = obstruction_minutes(generate_events(seed=SEED))["total_obstruction_minutes"]
    for mode in ("adhoc", "optimized"):
        run = simulate(mode, seed=SEED)
        cleared = _cleared_minutes(run)
        assert cleared <= total + 1e-6, (
            f"{mode}: cleared {cleared} > generated {total} obstruction-minutes"
        )


def test_residual_is_nonnegative():
    for mode in ("adhoc", "optimized"):
        run = simulate(mode, seed=SEED)
        assert _residual_minutes(run) >= -1e-6, f"{mode}: negative residual obstruction"


# -------------------------------------------------------------- class breakdown
def test_per_class_sums_to_total():
    agg = obstruction_minutes(generate_events(seed=SEED))
    per_class_sum = sum(agg["per_class"].values())
    assert math.isclose(per_class_sum, agg["total_obstruction_minutes"], rel_tol=1e-6), (
        "per-class obstruction-minutes must sum to the total"
    )


def test_delivery_share_is_a_fraction():
    agg = obstruction_minutes(generate_events(seed=SEED))
    assert 0 <= agg["delivery_share_pct"] <= 100


# ----------------------------------------------------------------- event surge
def test_event_surge_avoids_obstruction():
    """Pre-positioning around a predictable event must avoid > 0 obstruction-min."""
    result = event_surge(
        seed=SEED,
        venue_lat=12.9788,
        venue_lon=77.6430,
        event_name="RCB vs CSK @ Chinnaswamy",
    )
    assert result["residual_obstruction_avoided"] > 0


# ----------------------------------------------------------------------- helpers
# simulate() returns {'totals': {...}, 'legs': [...], 'series': [...]}.
# We don't hard-code the exact 'totals' key name because the README doesn't
# document it; we try the plausible names and fail loudly with the real keys
# if none match, so the fix is a one-line edit here.
def _cleared_minutes(run) -> float:
    totals = run.get("totals", run)
    for key in (
        "cleared_minutes", "vehicle_minutes_cleared",
        "cleared", "cleared_obstruction_minutes", "veh_min_cleared",
    ):
        if key in totals:
            return float(totals[key])
    raise KeyError(
        f"cleared-minutes not found in totals keys {list(totals)}; "
        "set the right key in _cleared_minutes()."
    )


def _residual_minutes(run) -> float:
    totals = run.get("totals", run)
    for key in ("residual_minutes", "residual_obstruction_minutes", "residual"):
        if key in totals:
            return float(totals[key])
    raise KeyError(
        f"residual-minutes not found in totals keys {list(totals)}; "
        "set the right key in _residual_minutes()."
    )
