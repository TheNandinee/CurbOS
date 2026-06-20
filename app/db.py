"""
db.py — SQLite store for ClearLane.

Tables model the real BTP operation:
  segment           — a stretch of carriageway prone to obstruction (a choke point)
  crew              — an enforcement resource (tow truck / officer) BTP already has
  obstruction_event — a stopped vehicle blocking a live lane (from CCTV or the model)

SQLite keeps the demo zero-install. Production reads obstruction_event straight
from the Safe City CCTV / ANPR analytics pipeline and segment/crew from ASTraM.
"""
import os, sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "clearlane.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS segment (
    segment_id TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    lat        REAL NOT NULL,
    lon        REAL NOT NULL,
    chronic    REAL NOT NULL DEFAULT 1.0   -- relative obstruction propensity
);
CREATE TABLE IF NOT EXISTS crew (
    crew_id  TEXT PRIMARY KEY,
    kind     TEXT NOT NULL,                -- 'tow' | 'officer'
    home_lat REAL NOT NULL,
    home_lon REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS obstruction_event (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id TEXT NOT NULL,
    ts         REAL NOT NULL,
    vehicle_class TEXT NOT NULL,           -- 'delivery' | 'car' | 'auto' | 'other'
    dwell_s    REAL NOT NULL,
    source     TEXT NOT NULL DEFAULT 'model' -- 'model' | 'cctv'
);
CREATE INDEX IF NOT EXISTS idx_obs_seg ON obstruction_event(segment_id, ts);
"""


def init_db():
    c = get_conn()
    try:
        c.executescript(SCHEMA); c.commit()
    finally:
        c.close()


if __name__ == "__main__":
    init_db(); print("OK schema at", DB_PATH)
