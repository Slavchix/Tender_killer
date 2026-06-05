import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const scriptPath = fileURLToPath(import.meta.url);
const scriptsDir = path.dirname(scriptPath);
const root = path.dirname(scriptsDir);
const worker = path.join(scriptsDir, "restart-dev-worker.ps1");

const options = parseArgs(process.argv.slice(2));
const apiPort = options.apiPort ?? process.env.TENDER_KILLER_API_PORT ?? "8000";
const webPort = options.webPort ?? process.env.TENDER_KILLER_WEB_PORT ?? "5175";
const timeoutSeconds = options.timeoutSeconds ?? "12";
const extraWebPorts = options.extraWebPorts.length > 0 ? options.extraWebPorts : ["5173", "5174"];
const powershell = path.join(
  process.env.SystemRoot ?? "C:\\Windows",
  "System32",
  "WindowsPowerShell",
  "v1.0",
  "powershell.exe",
);

const workerArgs = [
  "-NoProfile",
  "-ExecutionPolicy",
  "Bypass",
  "-File",
  worker,
  "-ApiPort",
  String(apiPort),
  "-WebPort",
  String(webPort),
  "-TimeoutSeconds",
  String(timeoutSeconds),
];

if (extraWebPorts.length > 0) {
  workerArgs.push("-ExtraWebPorts", ...extraWebPorts.map(String));
}

const child = spawn(powershell, workerArgs, {
  cwd: root,
  detached: true,
  stdio: "ignore",
  windowsHide: true,
});
child.unref();

console.log(`scheduled=true`);
console.log(`worker_pid=${child.pid}`);
console.log(`api=http://127.0.0.1:${apiPort}`);
console.log(`frontend=http://127.0.0.1:${webPort}`);

function parseArgs(argv) {
  const parsed = {
    apiPort: null,
    webPort: null,
    timeoutSeconds: null,
    extraWebPorts: [],
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--api-port" && argv[index + 1]) {
      parsed.apiPort = argv[++index];
    } else if (arg === "--web-port" && argv[index + 1]) {
      parsed.webPort = argv[++index];
    } else if (arg === "--timeout-seconds" && argv[index + 1]) {
      parsed.timeoutSeconds = argv[++index];
    } else if (arg === "--extra-web-ports" && argv[index + 1]) {
      parsed.extraWebPorts = argv[++index].split(",").filter(Boolean);
    }
  }
  return parsed;
}
