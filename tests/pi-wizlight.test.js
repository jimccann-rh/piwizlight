import assert from "node:assert/strict";
import { test } from "node:test";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const helperPath = resolve(dirname(fileURLToPath(import.meta.url)), "..", "pi_status_light.py");

async function loadExtension() {
  try {
    return (await import("../extensions/pi-wizlight.js")).default;
  } catch (error) {
    assert.fail(`Pi extension should be importable: ${error.message}`);
  }
}

async function makePi(exec = async () => ({ stdout: "", stderr: "", code: 0, killed: false })) {
  const register = await loadExtension();
  const handlers = new Map();
  const calls = [];
  register({
    on: (event, handler) => handlers.set(event, handler),
    exec: async (command, args) => {
      calls.push([command, args]);
      return exec(command, args);
    },
  });
  return { handlers, calls };
}

test("maps Pi lifecycle events to the existing helper statuses", async () => {
  const { handlers, calls } = await makePi();
  await handlers.get("session_start")();
  await handlers.get("agent_start")();
  await handlers.get("tool_execution_start")({ toolName: "bash" });
  await handlers.get("tool_execution_end")({ toolName: "write" });
  await handlers.get("tool_execution_end")({ toolName: "edit" });
  await handlers.get("tool_execution_end")({ toolName: "bash" });
  await handlers.get("agent_settled")();
  await handlers.get("session_shutdown")();

  assert.deepEqual(calls.map(([command, args]) => [command, args[1]]), [
    ["python3", "input"], ["python3", "idle"], ["python3", "working"],
    ["python3", "flash"], ["python3", "flash"], ["python3", "input"],
    ["python3", "warm"], ["python3", "off"],
  ]);
  assert.ok(calls.every(([, args]) => args[0] === helperPath));
});

test("serializes controller calls", async () => {
  let releaseFirst;
  const firstCall = new Promise((resolve) => { releaseFirst = resolve; });
  const { handlers, calls } = await makePi(async () => {
    if (calls.length === 1) await firstCall;
    return { stdout: "", stderr: "", code: 0, killed: false };
  });
  const first = handlers.get("agent_start")();
  const second = handlers.get("tool_execution_start")({ toolName: "bash" });
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(calls.map(([, args]) => args[1]), ["idle"]);
  releaseFirst();
  await Promise.all([first, second]);
  assert.deepEqual(calls.map(([, args]) => args[1]), ["idle", "working"]);
});

test("reports helper failures and continues the queue", async () => {
  let attempts = 0;
  const { handlers } = await makePi(async () => {
    if (++attempts === 1) throw new Error("controller failed");
    return { stdout: "", stderr: "", code: 0, killed: false };
  });
  await assert.rejects(handlers.get("agent_start")(), /controller failed/);
  await handlers.get("tool_execution_start")({ toolName: "bash" });
  assert.equal(attempts, 2);
});

test("rejects a nonzero helper exit", async () => {
  const { handlers } = await makePi(async () => ({
    stdout: "",
    stderr: "controller exited",
    code: 1,
    killed: false,
  }));
  await assert.rejects(handlers.get("agent_start")(), /controller exited/);
});
