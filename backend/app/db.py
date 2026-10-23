import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "waitlist.db"

SCHEMA = """
CREATE TABLE practices (
  practice_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  specialty TEXT NOT NULL
);
CREATE TABLE offers (
  offer_id TEXT PRIMARY KEY,
  practice_id TEXT NOT NULL REFERENCES practices(practice_id),
  waitlisted_appointment_id TEXT NOT NULL,
  sequence_number INTEGER NOT NULL CHECK (sequence_number BETWEEN 1 AND 8),
  sent_at TEXT NOT NULL,          -- UTC ISO-8601
  outcome TEXT NOT NULL CHECK (outcome IN ('accepted','declined','opted_out','no_response')),
  responded_at TEXT,              -- accepted / declined only
  opted_out_at TEXT,              -- opted_out only
  UNIQUE (waitlisted_appointment_id, sequence_number)
);
CREATE INDEX offers_practice_sent ON offers (practice_id, sent_at);
"""


def db_path() -> Path:
    return Path(os.environ.get("WAITLIST_DB", DEFAULT_DB))


def connect(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or db_path())
    conn.row_factory = sqlite3.Row
    return conn
