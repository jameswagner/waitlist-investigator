import { CopilotChat, CopilotKitProvider, useAgent, useConfigureSuggestions, useRenderTool } from "@copilotkit/react-core/v2";
import { useEffect, useState } from "react";
import { z } from "zod";
import type { Msg } from "./evidence";
import { Workspace } from "./Workspace";

const SUGGESTION =
  "Compare repeat-offer engagement at Cedar and Harbor. Is there evidence for the same outreach policy at both?";

function Screen() {
  const { agent } = useAgent();
  const [agentError, setAgentError] = useState<string>();
  useEffect(() => {
    const sub = agent.subscribe({
      onRunStartedEvent: () => setAgentError(undefined),
      onRunErrorEvent: ({ event }) => setAgentError(event.message),
    });
    return () => sub.unsubscribe();
  }, [agent]);
  useRenderTool(
    {
      name: "get_offer_engagement",
      parameters: z.object({ practice_id: z.string(), start_date: z.string(), end_date: z.string() }),
      render: ({ status, parameters }) => (
        <p className="toolnote">
          {status === "complete" ? "Queried" : "Querying"} {parameters.practice_id ?? "…"}{" "}
          {status === "complete" ? "— see evidence panel" : "…"}
        </p>
      ),
    },
    [],
  );
  useConfigureSuggestions(
    { suggestions: [{ title: "Compare Cedar and Harbor", message: SUGGESTION }], available: "always" },
    [],
  );
  return (
    <main>
      <header>
        <h1>Synthetic waitlist analytics demo</h1>
        <p className="muted">Fictional practices and generated records; illustrative only.</p>
      </header>
      <div className="layout">
        <Workspace messages={agent.messages as unknown as Msg[]} running={agent.isRunning} agentError={agentError} />
        <aside className="chat" aria-label="Agent chat">
          <CopilotChat />
        </aside>
      </div>
    </main>
  );
}

export default function App() {
  return (
    <CopilotKitProvider runtimeUrl="/api/copilotkit">
      <Screen />
    </CopilotKitProvider>
  );
}
