"""
seed.py — a real Bengaluru corridor and BTP's enforcement resources.

Segments are real-ish choke points around Indiranagar 100ft Road and the
CMH Road / metro / mall cluster — the kind of evening obstruction BTP already
tows near Phoenix Mall of Asia. Crews = 4 enforcement units (BTP's scarce
resource). Numbers are deliberately modest and defensible.
"""
from app.db import get_conn, init_db

# corridor anchor (Indiranagar)
C_LAT, C_LON = 12.97180, 77.64120

SEGMENTS = [
    # id,            name,                                lat,       lon,      chronic
    ("seg_100ft_1", "100ft Rd × CMH Rd junction",        12.97240, 77.64050, 2.4),
    ("seg_100ft_2", "100ft Rd (restaurant row)",         12.97150, 77.64230, 2.0),
    ("seg_cmh_1",   "CMH Rd (metro entrance)",           12.97600, 77.63900, 2.2),
    ("seg_cmh_2",   "CMH Rd (market stretch)",           12.97720, 77.64080, 1.7),
    ("seg_mall_1",  "Mall frontage (drop-off)",          12.96930, 77.64360, 2.6),
    ("seg_12th_1",  "12th Main (cloud-kitchen cluster)", 12.97050, 77.63780, 1.9),
    ("seg_doublerd","Double Rd feeder",                  12.96820, 77.63990, 1.2),
    ("seg_oldmadras","Old Madras Rd slip",               12.97880, 77.64300, 1.4),
]

# one depot crews return toward (BTP sub-division base, approx)
DEPOT_LAT, DEPOT_LON = 12.97400, 77.64500
CREWS = [
    ("tow_1", "tow", DEPOT_LAT, DEPOT_LON),
    ("tow_2", "tow", DEPOT_LAT, DEPOT_LON),
    ("off_1", "officer", DEPOT_LAT, DEPOT_LON),
    ("off_2", "officer", DEPOT_LAT, DEPOT_LON),
]


def seed():
    init_db()
    c = get_conn()
    try:
        c.execute("DELETE FROM obstruction_event")
        c.execute("DELETE FROM segment")
        c.execute("DELETE FROM crew")
        c.executemany(
            "INSERT INTO segment (segment_id,name,lat,lon,chronic) VALUES (?,?,?,?,?)",
            SEGMENTS)
        c.executemany(
            "INSERT INTO crew (crew_id,kind,home_lat,home_lon) VALUES (?,?,?,?)",
            CREWS)
        c.commit()
        print(f"OK: seeded {len(SEGMENTS)} segments, {len(CREWS)} crews.")
    finally:
        c.close()


if __name__ == "__main__":
    seed()
