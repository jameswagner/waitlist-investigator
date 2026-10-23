"""Deterministic synthetic fixture. Illustrative only: not fitted to research or
supplied by any healthcare organization."""
import argparse
import random
from datetime import UTC, datetime, timedelta

from .db import SCHEMA, connect, db_path
from .invariants import check_invariants

DATA_END = datetime(2026, 1, 1, tzinfo=UTC)
FIRST_OFFER_FROM = datetime(2025, 1, 1, tzinfo=UTC)
FIRST_OFFER_SPAN_DAYS = 270
N_APPOINTMENTS = 400
SEED = 20250101

PRACTICES = [
    ("cedar-derm", "Cedar Dermatology", "dermatology"),
    ("harbor-eye", "Harbor Eye Care", "eye care"),
]

# Per offer number 1..8: (P(accept), P(opt out within 24h)); remainder splits
# between decline and no response.
PARAMS = {
    "cedar-derm": [(.30, .01), (.24, .02), (.18, .04), (.13, .07),
                   (.09, .10), (.06, .13), (.04, .16), (.03, .18)],
    "harbor-eye": [(.28, .01), (.27, .01), (.26, .01), (.25, .01),
                   (.25, .01), (.24, .015), (.24, .015), (.23, .015)],
}


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate(conn) -> None:
    rng = random.Random(SEED)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO practices VALUES (?,?,?)", PRACTICES)
    n_offer = 0
    for pid, _, _ in PRACTICES:
        for i in range(N_APPOINTMENTS):
            appt = f"{pid}-wa-{i + 1:04d}"
            sent = FIRST_OFFER_FROM + timedelta(
                seconds=rng.randrange(FIRST_OFFER_SPAN_DAYS * 86400))
            for seq, (p_acc, p_opt) in enumerate(PARAMS[pid], start=1):
                if sent + timedelta(hours=24) > DATA_END:
                    break
                n_offer += 1
                u = rng.random()
                resp = opt = None
                if u < p_acc:
                    outcome = "accepted"
                    resp = sent + timedelta(seconds=rng.randrange(60, 86400))
                elif u < p_acc + p_opt:
                    outcome = "opted_out"
                    opt = sent + timedelta(seconds=rng.randrange(60, 86400))
                elif u < p_acc + p_opt + 0.25:
                    outcome = "declined"
                    resp = sent + timedelta(seconds=rng.randrange(60, 86400))
                else:
                    outcome = "no_response"
                conn.execute(
                    "INSERT INTO offers VALUES (?,?,?,?,?,?,?,?)",
                    (f"offer-{n_offer:06d}", pid, appt, seq, _iso(sent), outcome,
                     _iso(resp) if resp else None, _iso(opt) if opt else None))
                if outcome in ("accepted", "opted_out"):
                    break
                sent += timedelta(hours=48 + rng.randrange(0, 5 * 24))
    conn.commit()


def main() -> None:
    ap = argparse.ArgumentParser(description="Create the synthetic SQLite database.")
    ap.add_argument("--force", action="store_true", help="replace an existing database")
    args = ap.parse_args()
    path = db_path()
    if path.exists():
        if not args.force:
            raise SystemExit(f"{path} exists; pass --force to replace it")
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(path)
    generate(conn)
    problems = check_invariants(conn, DATA_END)
    if problems:
        raise SystemExit("invariant violations:\n" + "\n".join(problems[:20]))
    n = conn.execute("SELECT COUNT(*) FROM offers").fetchone()[0]
    print(f"Wrote {n} synthetic offers to {path}")


if __name__ == "__main__":
    main()
