import { useEffect, useMemo, useState } from "react";
import { EvidenceChart } from "./EvidenceChart";
import { extractEvidence, type Evidence, type Msg } from "./evidence";

type Done = Exclude<Evidence, { kind: "pending" }>;

function label(e: Done) {
  if (e.kind === "result") {
    const { scope } = e.result;
    return `${scope.practice_name} · ${scope.start_date} → ${scope.end_date}`;
  }
  return "Failed query";
}

/** Evidence panel + compact query history. History is kept locally so selecting an entry never reruns a query. */
export function Workspace({
  messages,
  running,
  agentError,
}: {
  messages: Msg[];
  running: boolean;
  agentError?: string;
}) {
  const [history, setHistory] = useState<Done[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const derived = useMemo(() => extractEvidence(messages, running), [messages, running]);
  const pending = derived.some((e) => e.kind === "pending");

  useEffect(() => {
    const done = derived.filter((e): e is Done => e.kind !== "pending");
    const known = new Set(history.map((h) => h.id));
    const fresh = done.filter((d) => !known.has(d.id));
    if (fresh.length === 0) return;
    setHistory((h) => [...h, ...fresh]);
    setSelected(fresh[fresh.length - 1].id);
  }, [derived, history]);

  const current = history.find((h) => h.id === selected);

  return (
    <div className="workspace">
      <div className="evidence" aria-live="polite">
        {pending && <p role="status">Running query…</p>}
        {agentError && <p role="alert" className="error">Agent error: {agentError}</p>}
        {current?.kind === "error" && <p role="alert" className="error">Query failed: {current.message}</p>}
        {current?.kind === "result" && current.result.empty && (
          <p role="status">No offers matched {current.result.scope.practice_name} for those dates.</p>
        )}
        {current?.kind === "result" && !current.result.empty && <EvidenceChart result={current.result} />}
        {!current && !pending && !agentError && (
          <p className="muted">Ask a question; query results appear here.</p>
        )}
      </div>
      <nav aria-label="Query history" className="history">
        <h3>History</h3>
        {history.length === 0 && <p className="muted">No completed queries.</p>}
        <ul>
          {history.map((h) => (
            <li key={h.id}>
              <button aria-pressed={h.id === selected} onClick={() => setSelected(h.id)}>
                {label(h)}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
