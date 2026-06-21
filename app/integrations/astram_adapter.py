"""
ASTraM integration adapter.

Turns CurbOS's obstruction-minute output into a payload shaped as a new ASTraM
*layer* - converting the pitch claim ("becomes a new layer inside ASTraM") into
a concrete, inspectable interface contract.

ASTraM's internal API is not public, so the schema below is CurbOS's *proposed*
contract: the exact JSON we would push as the obstruction-minute layer. Field
names are documented in docs/INTEGRATION.md and remap easily to ASTraM's real
schema during a pilot.

See the exact payload:
    python -m app.integrations.astram_adapter
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Optional

from app.seed import seed
from app.feed import generate_events, obstruction_minutes
from app.dispatch import compare

LAYER_NAME = "curbos.obstruction_minutes"
SCHEMA_VERSION = "0.1"


@dataclass
class SegmentRecord:
    segment_id: str
    name: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    obstruction_minutes: float
    dominant_class: Optional[str]
    rank: int                          # 1 = worst live blockage right now
    recommended_action: Optional[str]  # e.g. "dispatch tow_2"


@dataclass
class ASTraMLayerPayload:
    layer: str
    schema_version: str
    generated_at: str
    summary: dict
    segments: list = field(default_factory=list)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(asdict(self), indent=indent)


def _get(obj, key):
    """Read a field from a dict OR an object, returning None if absent."""
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _segment_index() -> dict:
    """
    Map segment_id -> {name, lat, lon}. Reads app.seed.SEGMENTS and normalizes
    dict-vs-object. If SEGMENTS uses different field names, adjust here only.
    """
    try:
        from app.seed import SEGMENTS  # type: ignore
    except Exception:
        return {}
    idx: dict = {}
    for s in SEGMENTS:
        sid = _get(s, "segment_id") or _get(s, "id")
        if sid is None:
            continue
        idx[sid] = {"name": _get(s, "name"), "lat": _get(s, "lat"), "lon": _get(s, "lon")}
    return idx


def _dominant_class_per_segment(events) -> dict:
    """Best-effort: which vehicle class holds the most obstruction-min per segment."""
    tally: dict = {}
    for e in events:
        sid = _get(e, "segment_id")
        cls = _get(e, "vehicle_class") or _get(e, "klass") or _get(e, "cls")
        dwell = _get(e, "dwell_min") or _get(e, "dwell") or 0
        if sid is None or cls is None:
            continue
        tally.setdefault(sid, {}).setdefault(cls, 0.0)
        tally[sid][cls] += float(dwell or 0)
    return {sid: max(by_cls, key=by_cls.get) for sid, by_cls in tally.items() if by_cls}


def _recommended_actions() -> dict:
    """
    segment_id -> recommended crew action, read from optimized dispatch legs.
    Returns {} if the leg shape differs; the layer is still valid without it.
    """
    try:
        legs = compare(seed=7).get("optimized", {}).get("legs", [])
    except Exception:
        return {}
    out: dict = {}
    for leg in legs:
        sid = _get(leg, "segment_id") or _get(leg, "to_segment") or _get(leg, "target")
        crew = _get(leg, "crew_id") or _get(leg, "crew")
        if sid and crew and sid not in out:
            out[sid] = f"dispatch {crew}"
    return out


def build_astram_layer(seed_value: int = 7) -> ASTraMLayerPayload:
    seed()
    events = generate_events(seed=seed_value)
    agg = obstruction_minutes(events)
    per_segment: dict = agg["per_segment"]

    meta = _segment_index()
    dominant = _dominant_class_per_segment(events)
    rec = _recommended_actions()

    # Worst-first ranking is the dispatch priority ASTraM doesn't compute today.
    ranked = sorted(per_segment.items(), key=lambda kv: kv[1], reverse=True)

    records = []
    for rank, (sid, minutes) in enumerate(ranked, start=1):
        m = meta.get(sid, {})
        records.append(
            SegmentRecord(
                segment_id=sid,
                name=m.get("name"),
                lat=m.get("lat"),
                lon=m.get("lon"),
                obstruction_minutes=round(float(minutes), 1),
                dominant_class=dominant.get(sid),
                rank=rank,
                recommended_action=rec.get(sid),
            )
        )

    summary: dict[str, Any] = {
        "total_obstruction_minutes": agg["total_obstruction_minutes"],
        "delivery_share_pct": agg.get("delivery_share_pct"),
        "segment_count": len(records),
        "worst_segment": records[0].segment_id if records else None,
    }

    return ASTraMLayerPayload(
        layer=LAYER_NAME,
        schema_version=SCHEMA_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
        summary=summary,
        segments=records,
    )


if __name__ == "__main__":
    print(build_astram_layer().to_json())
