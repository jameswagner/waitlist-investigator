import itertools
import sqlite3
from datetime import datetime, timedelta

MIN_GAP = timedelta(hours=48)
WINDOW = timedelta(hours=24)


def _ts(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


def check_invariants(conn: sqlite3.Connection, data_end: datetime | None = None) -> list[str]:
    """Return human-readable violations; empty means the fixture is consistent."""
    problems: list[str] = []
    by_appt: dict[str, list[sqlite3.Row]] = {}
    for r in conn.execute("SELECT * FROM offers ORDER BY waitlisted_appointment_id, sequence_number"):
        by_appt.setdefault(r["waitlisted_appointment_id"], []).append(r)

    for appt, offers in by_appt.items():
        if [o["sequence_number"] for o in offers] != list(range(1, len(offers) + 1)):
            problems.append(f"{appt}: sequence not consecutive from 1")
        if len({o["practice_id"] for o in offers}) > 1:
            problems.append(f"{appt}: offers span practices")
        for prev, cur in itertools.pairwise(offers):
            if prev["outcome"] in ("accepted", "opted_out"):
                problems.append(f"{appt}: offer after {prev['outcome']}")
            if _ts(cur["sent_at"]) - _ts(prev["sent_at"]) < MIN_GAP:
                problems.append(f"{appt}: offers #{prev['sequence_number']}/#{cur['sequence_number']} <48h apart")
        for o in offers:
            sent = _ts(o["sent_at"])
            resp, opt = _ts(o["responded_at"]), _ts(o["opted_out_at"])
            if resp and resp <= sent:
                problems.append(f"{o['offer_id']}: response not after send")
            if opt and opt <= sent:
                problems.append(f"{o['offer_id']}: opt-out not after send")
            if opt and opt - sent > WINDOW:
                problems.append(f"{o['offer_id']}: opt-out outside 24h window")
            if o["outcome"] in ("accepted", "declined") and not (resp and not opt):
                problems.append(f"{o['offer_id']}: {o['outcome']} needs response only")
            if o["outcome"] == "opted_out" and not (opt and not resp):
                problems.append(f"{o['offer_id']}: opted_out needs opt-out time only")
            if o["outcome"] == "no_response" and (resp or opt):
                problems.append(f"{o['offer_id']}: no_response has timestamps")
            if data_end and sent + WINDOW > data_end:
                problems.append(f"{o['offer_id']}: 24h window incomplete")
    return problems
