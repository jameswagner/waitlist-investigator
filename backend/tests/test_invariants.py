from app.invariants import check_invariants
from tests.conftest import offer


def test_fixture_is_consistent(db):
    assert check_invariants(db) == []


def _problems(db, rows):
    db.execute("DELETE FROM offers")
    db.executemany("INSERT INTO offers VALUES (?,?,?,?,?,?,?,?)", rows)
    return check_invariants(db)


def test_offer_after_acceptance(db):
    p = _problems(db, [
        offer(1, "a", "x", 1, "2025-03-01T10:00:00Z", "accepted", "2025-03-01T11:00:00Z"),
        offer(2, "a", "x", 2, "2025-03-05T10:00:00Z", "no_response")])
    assert any("offer after accepted" in s for s in p)


def test_spacing_under_48h(db):
    p = _problems(db, [
        offer(1, "a", "x", 1, "2025-03-01T10:00:00Z", "no_response"),
        offer(2, "a", "x", 2, "2025-03-03T09:59:59Z", "no_response")])
    assert any("<48h" in s for s in p)


def test_response_before_send_and_gap_in_sequence(db):
    p = _problems(db, [
        offer(1, "a", "x", 1, "2025-03-01T10:00:00Z", "declined", "2025-03-01T09:00:00Z"),
        offer(2, "a", "x", 3, "2025-03-09T10:00:00Z", "no_response")])
    assert any("not after send" in s for s in p)
    assert any("consecutive" in s for s in p)


def test_mutual_exclusion_and_window(db):
    p = _problems(db, [
        offer(1, "a", "x", 1, "2025-03-01T10:00:00Z", "accepted",
              "2025-03-01T11:00:00Z", "2025-03-01T12:00:00Z"),
        offer(2, "a", "y", 1, "2025-03-01T10:00:00Z", "opted_out", None, "2025-03-02T10:00:01Z")])
    assert any("needs response only" in s for s in p)
    assert any("outside 24h" in s for s in p)
