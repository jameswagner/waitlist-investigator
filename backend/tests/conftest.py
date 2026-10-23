import pytest

from app.db import SCHEMA, connect


def offer(i, practice, appt, seq, sent, outcome, resp=None, opt=None):
    return (f"o{i}", practice, appt, seq, sent, outcome, resp, opt)


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Hand-written fixture; expected values below are counted by hand."""
    path = tmp_path / "t.db"
    monkeypatch.setenv("WAITLIST_DB", str(path))
    conn = connect(path)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO practices VALUES (?,?,?)",
                     [("a", "Practice A", "x"), ("b", "Practice B", "y")])
    rows = [
        # A: appt1 declines then accepts; appt2 opts out at #1; appt3 no response at #1
        offer(1, "a", "a1", 1, "2025-03-01T10:00:00Z", "declined", "2025-03-01T12:00:00Z"),
        offer(2, "a", "a1", 2, "2025-03-04T10:00:00Z", "accepted", "2025-03-05T09:00:00Z"),
        offer(3, "a", "a2", 1, "2025-03-02T10:00:00Z", "opted_out", None, "2025-03-02T11:00:00Z"),
        offer(4, "a", "a3", 1, "2025-03-31T23:59:59Z", "no_response"),
        # B must never leak into A
        offer(5, "b", "b1", 1, "2025-03-01T10:00:00Z", "accepted", "2025-03-01T10:30:00Z"),
        # A, outside of March
        offer(6, "a", "a4", 1, "2025-04-01T00:00:00Z", "accepted", "2025-04-01T01:00:00Z"),
    ]
    conn.executemany("INSERT INTO offers VALUES (?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    yield conn
    conn.close()
