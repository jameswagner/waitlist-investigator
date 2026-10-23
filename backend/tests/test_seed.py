from datetime import date

from app import seed
from app.db import connect
from app.invariants import check_invariants
from app.tools import get_offer_engagement


def test_seed_is_deterministic_and_valid(tmp_path, monkeypatch):
    dumps = []
    for n in range(2):
        monkeypatch.setenv("WAITLIST_DB", str(tmp_path / f"{n}.db"))
        conn = connect(tmp_path / f"{n}.db")
        seed.generate(conn)
        assert check_invariants(conn, seed.DATA_END) == []
        dumps.append(conn.execute("SELECT * FROM offers ORDER BY offer_id").fetchall())
        dumps[-1] = [tuple(r) for r in dumps[-1]]
    assert dumps[0] == dumps[1]
    assert {r[1] for r in dumps[0]} == {"cedar-derm", "harbor-eye"}
    assert len({r[2] for r in dumps[0]}) >= 300
    assert max(r[3] for r in dumps[0]) <= 8


def test_tool_runs_on_seed(tmp_path, monkeypatch):
    monkeypatch.setenv("WAITLIST_DB", str(tmp_path / "s.db"))
    seed.generate(connect(tmp_path / "s.db"))
    r = get_offer_engagement("cedar-derm", date(2025, 1, 1), date(2025, 12, 31), "id")
    assert r.rows[0].sequence_number == 1 and not r.empty
