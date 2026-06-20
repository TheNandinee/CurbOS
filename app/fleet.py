"""
fleet.py — the Fleet Compliance API (the Flipkart-facing half) + its economics.

Exposes the advisory zones a delivery fleet (Flipkart/Blinkit/Swiggy) polls, and
converts complied-away obstructions into money and rider-time saved. Every
assumption is explicit and shown on screen so the number is defensible, not magic.
"""
from app.dispatch import simulate

# --- transparent assumptions (override with real fleet data) ---
CHALLAN_PROB = 0.25      # share of would-be obstructors that actually get fined
CHALLAN_COST = 500       # rupees per no-parking / obstruction challan
TOW_PROB = 0.05          # share that would have been towed
TOW_COST = 1500          # rupees fine + tow + rider downtime
RIDER_MIN_VALUE = 6      # rupees value of one rider-minute
EVENINGS_PER_YEAR = 320  # operating evenings for annualisation


def economics(redirect_count, delivery_minutes_avoided):
    challans = redirect_count * CHALLAN_PROB
    tows = redirect_count * TOW_PROB
    rider_min = delivery_minutes_avoided + redirect_count * 1.0   # dwell + handling
    rupees = challans * CHALLAN_COST + tows * TOW_COST + rider_min * RIDER_MIN_VALUE
    return {
        "redirects": redirect_count,
        "challans_avoided": round(challans, 1),
        "tows_avoided": round(tows, 1),
        "rider_minutes_saved": round(rider_min, 0),
        "rupees_saved_evening": round(rupees, 0),
        "assumptions": {"challan_prob": CHALLAN_PROB, "challan_cost": CHALLAN_COST,
                        "tow_prob": TOW_PROB, "tow_cost": TOW_COST,
                        "rider_min_value": RIDER_MIN_VALUE},
    }


def advisories(seed=7):
    opt = simulate("optimized", seed=seed)
    seg_names = {s["segment_id"]: s["name"] for s in opt["segments"]}
    zones = [{"segment_id": a["seg"], "name": seg_names.get(a["seg"], a["seg"]),
              "start": a["start"], "end": a["end"]} for a in opt["advisories"]]
    econ = economics(len(opt["redirects"]), opt["totals"]["delivery_minutes_avoided"])
    return {"zones": zones, "active_zone_count": len(zones),
            "delivery_minutes_avoided": opt["totals"]["delivery_minutes_avoided"],
            "economics": econ}


if __name__ == "__main__":
    from app.seed import seed as do_seed
    do_seed()
    r = advisories()
    e = r["economics"]
    print("advisory zones:", r["active_zone_count"], "| redirects:", e["redirects"])
    print("challans avoided:", e["challans_avoided"], "| rupees saved/evening:", e["rupees_saved_evening"])
