# waitlist-investigator

Synthetic waitlist analytics demo: ask an agent about repeat appointment-offer
engagement, watch it call a Python query tool, see the returned data charted, and
ask a follow-up. An investigation workspace, not a scheduling service.

All data is **synthetic and illustrative**: two fictional practices, generated records,
not fitted to research or supplied by any healthcare organization.

## Stack

- `backend/` — Python, FastAPI, Pydantic AI served over AG-UI, SQLite
- `web/` — React, CopilotKit (chat + tool events), Recharts; a small Node
  CopilotKit runtime (`web/server`) proxies the browser to the agent

## Setup

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), Node 22+.

```sh
cp .env.example .env          # set MODEL and the matching provider key
(cd backend && uv sync && uv run python -m app.seed)
(cd backend && uv run uvicorn app.main:app --port 8765)   # terminal 1
(cd web && npm install && npm run dev)                    # terminal 2
```

Open the URL Vite prints (usually http://localhost:5173) and use the suggested question. Provider keys stay
server-side in `.env` (git-ignored). `npm run dev` disables CopilotKit telemetry.

## Tools (the agent's only data access)

- `list_practices()`
- `get_offer_engagement(practice_id, start_date, end_date)` — per offer number:
  offers sent, accepted, opt-outs within 24h, and rates. Denominator is offers sent at
  that offer number. Dates filter on sent time (UTC), both ends inclusive.

Each result carries a unique `result_id`, arguments, scope, and rows. The dashboard
renders the tool result itself (never assistant prose) and keeps it in the query history,
so selecting history restores a chart without re-running the query.

## Checks

```sh
(cd backend && uv run ruff check . && uv run pytest)
(cd web && npm run typecheck && npm test && npm run build)
```

## Scope

No auth, deployment, messaging, EHR integration, workers, or free-form SQL.
Contribution rules for humans and agents: [AGENTS.md](AGENTS.md).
