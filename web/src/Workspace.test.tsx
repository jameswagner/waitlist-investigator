import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { extractEvidence, type Msg } from "./evidence";
import { Workspace } from "./Workspace";

const result = (id: string, name: string, accepted: number) => ({
  status: "ok", result_id: id, tool: "get_offer_engagement",
  arguments: { practice_id: "p", start_date: "2025-01-01", end_date: "2025-06-30" },
  scope: {
    practice_id: "p", practice_name: name, start_date: "2025-01-01", end_date: "2025-06-30",
    date_basis: "dates basis", denominator: "Offers sent at that offer number.",
    outcome_window: "24h window", data_note: "Synthetic.",
  },
  rows: [{ sequence_number: 1, sent: 10, accepted, opted_out: 1, acceptance_rate: accepted / 10, opt_out_rate: 0.1 }],
  empty: false,
});

const call = (id: string, args = {}): Msg => ({
  id: `a-${id}`, role: "assistant",
  toolCalls: [{ id, function: { name: "get_offer_engagement", arguments: JSON.stringify(args) } }],
});
const toolMsg = (id: string, body: unknown): Msg => ({
  id: `t-${id}`, role: "tool", toolCallId: id, content: JSON.stringify(body),
});

describe("extractEvidence", () => {
  it("ignores other tools and marks unanswered calls pending while running", () => {
    const other: Msg = { id: "x", role: "assistant", toolCalls: [{ id: "o", function: { name: "list_practices", arguments: "{}" } }] };
    expect(extractEvidence([other], true)).toEqual([]);
    expect(extractEvidence([call("c1")], true)[0].kind).toBe("pending");
    expect(extractEvidence([call("c1")], false)[0].kind).toBe("error");
  });

  it("surfaces tool errors", () => {
    const [e] = extractEvidence([call("c1"), toolMsg("c1", { status: "error", error: "Unknown practice_id 'z'" })], false);
    expect(e).toMatchObject({ kind: "error", message: "Unknown practice_id 'z'" });
  });
});

describe("Workspace", () => {
  it("renders loading, then result on completion, then restores history without new calls", async () => {
    const user = userEvent.setup();
    const m1 = [call("c1")];
    const { rerender } = render(<Workspace messages={m1} running />);
    expect(screen.getByRole("status")).toHaveTextContent("Running query");

    const m2 = [...m1, toolMsg("c1", result("r1", "Cedar Dermatology", 3))];
    rerender(<Workspace messages={m2} running />);
    expect(await screen.findByRole("heading", { name: "Cedar Dermatology" })).toBeInTheDocument();
    expect(within(screen.getByRole("table")).getByText("30.0%")).toBeInTheDocument();
    expect(screen.getByText(/Offers sent at that offer number/)).toBeInTheDocument();

    const m3 = [...m2, call("c2"), toolMsg("c2", result("r2", "Harbor Eye Care", 5))];
    rerender(<Workspace messages={m3} running={false} />);
    expect(await screen.findByRole("heading", { name: "Harbor Eye Care" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Cedar Dermatology/ }));
    expect(screen.getByRole("heading", { name: "Cedar Dermatology" })).toBeInTheDocument();
    expect(within(screen.getByRole("table")).getByText("30.0%")).toBeInTheDocument();
    // History is local state; restoring needs no new messages / tool calls.
  });

  it("shows empty and error states", async () => {
    const empty = { ...result("r1", "Cedar Dermatology", 0), rows: [], empty: true };
    const { rerender } = render(<Workspace messages={[call("c1"), toolMsg("c1", empty)]} running={false} />);
    expect(await screen.findByRole("status")).toHaveTextContent("No offers matched");
    rerender(<Workspace messages={[]} running={false} agentError="boom" />);
    expect(screen.getByRole("alert")).toHaveTextContent("boom");
  });
});
