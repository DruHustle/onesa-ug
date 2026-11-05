import { createAppServer } from "./app.ts";
import { loadConfig } from "./config.ts";

const config = loadConfig();
const server = createAppServer(config);

server.listen(config.port, config.host, () => {
  console.info(`Onesa Mobile demo API listening on port ${config.port}. Telecom activation and payments are unavailable.`);
});

server.on("error", (error: NodeJS.ErrnoException) => {
  // No credentials, tokens, raw requests or arbitrary error objects in output.
  console.error(`API startup failed (${error.code ?? "UNKNOWN"}).`);
  process.exitCode = 1;
});

let stopping = false;
function shutdown(): void {
  if (stopping) return;
  stopping = true;
  const deadline = setTimeout(() => {
    server.closeAllConnections();
    process.exitCode = 1;
  }, 5_000);
  deadline.unref();
  server.close(() => { clearTimeout(deadline); });
  server.closeIdleConnections();
}

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
