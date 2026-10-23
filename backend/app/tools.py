from datetime import UTC, date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, model_validator

from .db import connect

WINDOW_NOTE = "Outcomes are counted within 24 hours after the offer was sent."


class Practice(BaseModel):
    practice_id: str
    name: str
    specialty: str
    offer_count: int
    first_sent: str | None
    last_sent: str | None


class PracticeList(BaseModel):
    status: Literal["ok"] = "ok"
    tool: Literal["list_practices"] = "list_practices"
    data_note: str = "Synthetic, illustrative data; not from any real organization."
    practices: list[Practice]


class EngagementArgs(BaseModel):
    practice_id: str
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def _ordered(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class EngagementRow(BaseModel):
    sequence_number: int
    sent: int
    accepted: int
    opted_out: int
    acceptance_rate: float
    opt_out_rate: float


class EngagementScope(BaseModel):
    practice_id: str
    practice_name: str
    start_date: date
    end_date: date
    date_basis: str = (
        "Offers with sent_at (UTC) from start_date 00:00 through end_date 23:59:59, "
        "both dates inclusive."
    )
    denominator: str = "Offers sent at that offer number within the date range."
    outcome_window: str = WINDOW_NOTE
    data_note: str = "Synthetic, illustrative data; not from any real organization."


class EngagementResult(BaseModel):
    status: Literal["ok"] = "ok"
    result_id: str
    tool: Literal["get_offer_engagement"] = "get_offer_engagement"
    arguments: EngagementArgs
    scope: EngagementScope
    rows: list[EngagementRow]
    empty: bool


class ToolError(BaseModel):
    status: Literal["error"] = "error"
    tool: str
    error: str


def list_practices() -> PracticeList:
    with connect() as conn:
        rows = conn.execute(
            """SELECT p.practice_id, p.name, p.specialty, COUNT(o.offer_id) AS n,
                      MIN(o.sent_at) AS first_sent, MAX(o.sent_at) AS last_sent
               FROM practices p LEFT JOIN offers o USING (practice_id)
               GROUP BY p.practice_id ORDER BY p.name"""
        ).fetchall()
    return PracticeList(practices=[
        Practice(practice_id=r["practice_id"], name=r["name"], specialty=r["specialty"],
                 offer_count=r["n"], first_sent=r["first_sent"], last_sent=r["last_sent"])
        for r in rows])


def _bound(d: date) -> str:
    return datetime(d.year, d.month, d.day, tzinfo=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_offer_engagement(practice_id: str, start_date: date, end_date: date,
                         result_id: str) -> EngagementResult | ToolError:
    try:
        args = EngagementArgs(practice_id=practice_id, start_date=start_date, end_date=end_date)
    except ValueError as e:
        return ToolError(tool="get_offer_engagement", error=str(e))
    with connect() as conn:
        p = conn.execute("SELECT name FROM practices WHERE practice_id = ?", (practice_id,)).fetchone()
        if p is None:
            known = [r[0] for r in conn.execute("SELECT practice_id FROM practices")]
            return ToolError(tool="get_offer_engagement",
                             error=f"Unknown practice_id '{practice_id}'. Known: {known}")
        # Window outcomes are 24h-complete by construction of the fixture.
        rows = conn.execute(
            """SELECT sequence_number,
                      COUNT(*) AS sent,
                      SUM(outcome = 'accepted'
                          AND responded_at <= strftime('%Y-%m-%dT%H:%M:%SZ', sent_at, '+24 hours')) AS accepted,
                      SUM(outcome = 'opted_out'
                          AND opted_out_at <= strftime('%Y-%m-%dT%H:%M:%SZ', sent_at, '+24 hours')) AS opted_out
               FROM offers
               WHERE practice_id = ? AND sent_at >= ? AND sent_at < ?
               GROUP BY sequence_number ORDER BY sequence_number""",
            (practice_id, _bound(start_date), _bound(end_date + timedelta(days=1))),
        ).fetchall()
    out = [EngagementRow(sequence_number=r["sequence_number"], sent=r["sent"],
                         accepted=r["accepted"], opted_out=r["opted_out"],
                         acceptance_rate=round(r["accepted"] / r["sent"], 4),
                         opt_out_rate=round(r["opted_out"] / r["sent"], 4)) for r in rows]
    return EngagementResult(
        result_id=result_id, arguments=args, rows=out, empty=not out,
        scope=EngagementScope(practice_id=practice_id, practice_name=p["name"],
                              start_date=start_date, end_date=end_date))
