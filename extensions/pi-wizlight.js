import { fileURLToPath } from "node:url";

const helperPath = fileURLToPath(new URL("../pi_status_light.py", import.meta.url));

export default function (pi) {
  let queue = Promise.resolve();
  const setStatus = (status) => {
    const current = queue.catch(() => {}).then(async () => {
      const result = await pi.exec("python3", [helperPath, status]);
      if (result.code !== 0) throw new Error(result.stderr || `WizLight helper exited with code ${result.code}`);
    });
    queue = current;
    return current;
  };

  pi.on("session_start", () => setStatus("input"));
  pi.on("agent_start", () => setStatus("idle"));
  pi.on("tool_execution_start", () => setStatus("working"));
  pi.on("tool_execution_end", (event) => {
    if (event.toolName === "write" || event.toolName === "edit") return setStatus("flash");
  });
  pi.on("agent_settled", () => setStatus("input"));
  pi.on("session_shutdown", async () => {
    await setStatus("warm");
    await setStatus("off");
  });
}
