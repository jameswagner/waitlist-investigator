import { HttpAgent } from "@ag-ui/client";
import { CopilotRuntime, createCopilotExpressHandler } from "@copilotkit/runtime/v2";
import express from "express";

const agentUrl = process.env.AGENT_URL ?? "http://127.0.0.1:8765/agent";
const port = Number(process.env.RUNTIME_PORT ?? 4765);

const runtime = new CopilotRuntime({
  agents: { default: new HttpAgent({ url: agentUrl }) },
});

const app = express();
app.use(createCopilotExpressHandler({ runtime, basePath: "/api/copilotkit" }));
app.listen(port, "127.0.0.1", () => console.log(`CopilotKit runtime on :${port} -> ${agentUrl}`));
