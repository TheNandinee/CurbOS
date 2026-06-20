"""
geo.py — distance math.

WHY this file exists:
  Allocation needs "how far is this rider from each bay?" in metres.
  We do NOT use PostGIS in the MVP (it's an install/ops burden for a beginner),
  so we compute great-circle distance in pure Python. For a micro-zone of a few
  hundred metres this is accurate to centimetres — more than enough.

In production this is replaced by a PostGIS ST_Distance / Redis GEOSEARCH call.
"""
from math import radians, sin, cos, asin, sqrt

EARTH_RADIUS_M = 6_371_000  # mean Earth radius in metres


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in METRES between two lat/lon points."""
    rlat1, rlon1, rlat2, rlon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(a))
