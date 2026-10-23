import { z } from "zod";

const Row = z.object({
  sequence_number: z.number(),
  sent: z.number(),
  accepted: z.number(),
  opted_out: z.number(),
  acceptance_rate: z.number(),
  opt_out_rate: z.number(),
});

export const EngagementResult = z.object({
  status: z.literal("ok"),
  result_id: z.string(),
  tool: z.literal("get_offer_engagement"),
  arguments: z.object({ practice_id: z.string(), start_date: z.string(), end_date: z.string() }),
  scope: z.object({
    practice_id: z.string(),
    practice_name: z.string(),
    start_date: z.string(),
    end_date: z.string(),
    date_basis: z.string(),
    denominator: z.string(),
    outcome_window: z.string(),
    data_note: z.string(),
  }),
  rows: z.array(Row),
  empty: z.boolean(),
});
export type EngagementResult = z.infer<typeof EngagementResult>;

export const ENGAGEMENT_TOOL = "get_offer_engagement";

export type Evidence =
  | { id: string; kind: "result"; result: EngagementResult }
  | { id: string; kind: "error"; message: string; args?: unknown }
  | { id: string; kind: "pending"; args?: unknown };

interface ToolCall { id: string; function: { name: string; arguments: string } }
export interface Msg {
  id: string;
  role: string;
  content?: unknown;
  toolCalls?: ToolCall[];
  toolCallId?: string;
  error?: string;
}

function parseArgs(raw: string): unknown {
  try { return JSON.parse(raw); } catch { return undefined; }
}

/** Derive engagement evidence from tool calls/results in the AG-UI message stream. */
export function extractEvidence(messages: Msg[], running: boolean): Evidence[] {
  const calls = new Map<string, ToolCall>();
  for (const m of messages) for (const c of m.toolCalls ?? []) {
    if (c.function.name === ENGAGEMENT_TOOL) calls.set(c.id, c);
  }
  const results = new Map<string, Msg>();
  for (const m of messages) if (m.role === "tool" && m.toolCallId && calls.has(m.toolCallId)) {
    results.set(m.toolCallId, m);
  }
  return [...calls.values()].map((call): Evidence => {
    const args = parseArgs(call.function.arguments);
    const res = results.get(call.id);
    if (!res) {
      return running
        ? { id: call.id, kind: "pending", args }
        : { id: call.id, kind: "error", message: "The query did not complete.", args };
    }
    let body: unknown;
    try { body = JSON.parse(String(res.content)); } catch { body = undefined; }
    const ok = EngagementResult.safeParse(body);
    if (ok.success) return { id: ok.data.result_id, kind: "result", result: ok.data };
    const msg = (body as { error?: string } | undefined)?.error ?? res.error ?? "The tool returned an unreadable result.";
    return { id: call.id, kind: "error", message: msg, args };
  });
}
