import { CartesianGrid, Legend, Line, LineChart, Tooltip, XAxis, YAxis } from "recharts";
import type { EngagementResult } from "./evidence";

export const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

export function EvidenceChart({ result }: { result: EngagementResult }) {
  const data = result.rows.map((r) => ({
    offer: r.sequence_number,
    Acceptance: r.acceptance_rate * 100,
    "Opt-out (24h)": r.opt_out_rate * 100,
  }));
  const { scope } = result;
  return (
    <section aria-labelledby="ev-title">
      <h2 id="ev-title">{scope.practice_name}</h2>
      <p className="muted">
        Offers sent {scope.start_date} to {scope.end_date} (UTC, inclusive)
      </p>
      <div role="img" aria-label={`Acceptance and opt-out rates by offer number for ${scope.practice_name}`}>
        <LineChart width={640} height={300} data={data} margin={{ top: 8, right: 16, bottom: 20, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="offer" label={{ value: "Offer number", position: "insideBottom", offset: -12 }} />
          <YAxis unit="%" domain={[0, 100]} />
          <Tooltip formatter={(v) => `${Number(v).toFixed(1)}%`} />
          <Legend verticalAlign="top" />
          <Line dataKey="Acceptance" stroke="#1b6ec2" strokeWidth={2} isAnimationActive={false} />
          <Line dataKey="Opt-out (24h)" stroke="#c2410c" strokeWidth={2} strokeDasharray="6 3" isAnimationActive={false} />
        </LineChart>
      </div>
      <table>
        <caption className="sr-only">Counts and rates by offer number</caption>
        <thead>
          <tr>
            <th scope="col">Offer #</th>
            <th scope="col">Sent</th>
            <th scope="col">Accepted</th>
            <th scope="col">Acceptance</th>
            <th scope="col">Opt-outs ≤24h</th>
            <th scope="col">Opt-out rate</th>
          </tr>
        </thead>
        <tbody>
          {result.rows.map((r) => (
            <tr key={r.sequence_number}>
              <th scope="row">{r.sequence_number}</th>
              <td>{r.sent}</td>
              <td>{r.accepted}</td>
              <td>{pct(r.acceptance_rate)}</td>
              <td>{r.opted_out}</td>
              <td>{pct(r.opt_out_rate)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <details>
        <summary>Definitions</summary>
        <ul>
          <li>Denominator: {scope.denominator}</li>
          <li>{scope.outcome_window}</li>
          <li>Dates: {scope.date_basis}</li>
          <li>{scope.data_note}</li>
        </ul>
      </details>
    </section>
  );
}
