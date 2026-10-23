from datetime import date

from app.tools import get_offer_engagement, list_practices


def run(practice, start, end):
    return get_offer_engagement(practice, start, end, "rid")


def test_rates_and_counts_by_sequence(db):
    r = run("a", date(2025, 3, 1), date(2025, 3, 31))
    by = {x.sequence_number: x for x in r.rows}
    # Seq 1: a1 declined, a2 opted out, a3 no response -> 3 sent, 0 accepted, 1 opt-out
    assert (by[1].sent, by[1].accepted, by[1].opted_out) == (3, 0, 1)
    assert by[1].acceptance_rate == 0 and by[1].opt_out_rate == round(1 / 3, 4)
    # Seq 2: a1 accepted
    assert (by[2].sent, by[2].accepted, by[2].opted_out) == (1, 1, 0)
    assert by[2].acceptance_rate == 1.0


def test_practice_filter_excludes_other_practice(db):
    r = run("b", date(2025, 3, 1), date(2025, 3, 31))
    assert [(x.sequence_number, x.sent, x.accepted) for x in r.rows] == [(1, 1, 1)]


def test_end_date_inclusive_start_inclusive(db):
    # a3 was sent 2025-03-31T23:59:59Z; a4 at 2025-04-01T00:00:00Z
    assert run("a", date(2025, 3, 31), date(2025, 3, 31)).rows[0].sent == 1
    assert run("a", date(2025, 4, 1), date(2025, 4, 1)).rows[0].sent == 1
    assert run("a", date(2025, 3, 1), date(2025, 3, 30)).rows[0].sent == 2


def test_empty_result(db):
    r = run("a", date(2024, 1, 1), date(2024, 1, 31))
    assert r.empty and r.rows == [] and r.status == "ok"


def test_errors_are_structured(db):
    assert run("nope", date(2025, 3, 1), date(2025, 3, 2)).status == "error"
    assert run("a", date(2025, 3, 5), date(2025, 3, 1)).status == "error"


def test_result_metadata(db):
    r = run("a", date(2025, 3, 1), date(2025, 3, 31))
    assert r.result_id == "rid" and r.tool == "get_offer_engagement"
    assert r.arguments.practice_id == "a" and r.scope.practice_name == "Practice A"
    assert "Offers sent" in r.scope.denominator


def test_list_practices(db):
    ps = {p.practice_id: p for p in list_practices().practices}
    assert ps["a"].offer_count == 5 and ps["b"].offer_count == 1
