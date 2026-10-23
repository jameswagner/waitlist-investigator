import os
import uuid
from datetime import date

from pydantic_ai import Agent

from . import tools

INSTRUCTIONS = """\
You help investigate repeat appointment-offer engagement in a synthetic, illustrative \
dataset (fictional practices; not real data). Always call tools for facts; never invent \
numbers. Start with list_practices if you need practice ids or date coverage. The \
dashboard renders each get_offer_engagement result automatically, so summarize briefly \
and cite the specific rates and counts you rely on.
Rates are descriptive. Later offers go to different, self-selected subsets of people, so \
do not claim causation, and do not recommend an optimal offer cutoff. You may say what \
the data does or does not support, and note small denominators.
Calls for a single practice only; compare practices by calling once per practice with \
the same dates."""

agent = Agent(
    os.environ.get("MODEL", "anthropic:claude-sonnet-5-5"),
    instructions=INSTRUCTIONS,
    defer_model_check=True,
)


@agent.tool_plain
def list_practices() -> tools.PracticeList:
    """List practices with their offer counts and the first/last offer sent dates."""
    return tools.list_practices()


@agent.tool_plain
def get_offer_engagement(
    practice_id: str, start_date: date, end_date: date
) -> tools.EngagementResult | tools.ToolError:
    """Acceptance and 24-hour opt-out counts and rates by offer sequence number for one
    practice. Dates are inclusive, by offer sent date (UTC), ISO format YYYY-MM-DD."""
    return tools.get_offer_engagement(practice_id, start_date, end_date, str(uuid.uuid4()))
