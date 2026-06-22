from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import traceback
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen

from tender_killer import supplier_browser_fetcher


DEFAULT_API_PORT = 8000
DEFAULT_WEB_PORT = 5175
DEFAULT_EXTRA_WEB_PORTS = (5173, 5174)
DEFAULT_TIMEOUT_SECONDS = 12
DEFAULT_SUPERVISOR_POLL_SECONDS = 2.0


@dataclass(frozen=True)
class DevControlConfig:
    root: Path
    api_port: int = DEFAULT_API_PORT
    web_port: int = DEFAULT_WEB_PORT
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    extra_web_ports: tuple[int, ...] = DEFAULT_EXTRA_WEB_PORTS
    host: str = "127.0.0.1"
    generation: str = ""
    monitor: bool = False
    supervisor_poll_seconds: float = DEFAULT_SUPERVISOR_POLL_SECONDS

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @property
    def manifest_path(self) -> Path:
        return self.logs_dir / "dev-processes.json"

    @property
    def generation_path(self) -> Path:
        return self.logs_dir / "dev-control-generation.txt"

    @property
    def supervisor_log_path(self) -> Path:
        return self.logs_dir / "dev-supervisor.err.log"

    @property
    def api_url(self) -> str:
        return f"http://{self.host}:{self.api_port}"

    @property
    def frontend_url(self) -> str:
        return f"http://{self.host}:{self.web_port}"

    @property
    def vite_script(self) -> Path:
        return self.root / "web" / "node_modules" / "vite" / "bin" / "vite.js"


@dataclass(frozen=True)
class DevProcessManifest:
    api_pid: int
    web_pid: int
    api: str
    frontend: str
    api_log: str
    web_log: str
    api_ready: bool
    web_ready: bool
    web_mode: str = "vite"
    started_at: str = ""
    worker_pid: int | None = None
    api_spawn_pid: int | None = None
    web_spawn_pid: int | None = None


@dataclass(frozen=True)
class PortBackedProcess:
    pid: int

    def poll(self) -> int | None:
        return None if _pid_alive(self.pid) else 1


def restart_worker_command(config: DevControlConfig) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "tender_killer.dev_control",
        "worker",
        "--root",
        str(config.root),
        "--api-port",
        str(config.api_port),
        "--web-port",
        str(config.web_port),
        "--timeout-seconds",
        str(config.timeout_seconds),
    ]
    if config.extra_web_ports:
        command.extend(["--extra-web-ports", ",".join(str(port) for port in config.extra_web_ports)])
    if config.generation:
        command.extend(["--generation", config.generation])
    command.append("--monitor")
    return command


def static_web_command(config: DevControlConfig) -> list[str]:
    return [
        sys.executable,
        "-m",
        "tender_killer.dev_static_proxy",
        "--root",
        str(config.root / "web" / "dist"),
        "--host",
        config.host,
        "--port",
        str(config.web_port),
        "--api-base-url",
        config.api_url,
    ]


def detached_spawn_kwargs(cwd: Path) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "cwd": str(cwd),
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
        "creationflags": _detached_creationflags(),
    }
    startupinfo = _hidden_windows_startupinfo()
    if startupinfo is not None:
        kwargs["startupinfo"] = startupinfo
    return kwargs


def supervisor_spawn_kwargs(config: DevControlConfig) -> dict[str, object]:
    kwargs = detached_spawn_kwargs(config.root)
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    stderr = config.supervisor_log_path.open("ab", buffering=0)
    kwargs["stderr"] = stderr
    kwargs["stdout"] = stderr
    return kwargs


def start_restart_worker(config: DevControlConfig) -> dict[str, object]:
    generation = f"{time.time_ns()}-{os.getpid()}"
    write_generation(config.root, generation)
    config = replace(config, generation=generation)
    spawn_kwargs = supervisor_spawn_kwargs(config)
    stdout = spawn_kwargs.get("stdout")
    stderr = spawn_kwargs.get("stderr")
    try:
        process = subprocess.Popen(restart_worker_command(config), **spawn_kwargs)
    finally:
        if hasattr(stdout, "close"):
            stdout.close()
        if stderr is not stdout and hasattr(stderr, "close"):
            stderr.close()
    return {
        "scheduled": True,
        "worker_pid": process.pid,
        "api": config.api_url,
        "frontend": config.frontend_url,
        "manifest": str(config.manifest_path),
        "generation": generation,
    }


def write_manifest(path: Path, manifest: DevProcessManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(manifest), ensure_ascii=False, indent=2), encoding="utf-8")


def write_generation(root: Path, generation: str) -> None:
    path = DevControlConfig(root=root).generation_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generation, encoding="utf-8")


def generation_is_current(config: DevControlConfig) -> bool:
    if not config.generation:
        return True
    try:
        return config.generation_path.read_text(encoding="utf-8").strip() == config.generation
    except OSError:
        return False


def read_manifest(path: Path) -> DevProcessManifest | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return DevProcessManifest(
        api_pid=int(payload.get("api_pid") or 0),
        web_pid=int(payload.get("web_pid") or 0),
        api=str(payload.get("api") or ""),
        frontend=str(payload.get("frontend") or ""),
        api_log=str(payload.get("api_log") or ""),
        web_log=str(payload.get("web_log") or ""),
        api_ready=bool(payload.get("api_ready")),
        web_ready=bool(payload.get("web_ready")),
        web_mode=str(payload.get("web_mode") or "vite"),
        started_at=str(payload.get("started_at") or ""),
        worker_pid=int(payload["worker_pid"]) if payload.get("worker_pid") else None,
        api_spawn_pid=int(payload["api_spawn_pid"]) if payload.get("api_spawn_pid") else None,
        web_spawn_pid=int(payload["web_spawn_pid"]) if payload.get("web_spawn_pid") else None,
    )


def run_worker(config: DevControlConfig) -> int:
    if not generation_is_current(config):
        return 0
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    _stop_managed_processes(config)
    _stop_configured_port_owners(config)
    time.sleep(0.5)
    if not generation_is_current(config):
        return 0

    node = _find_node(config.root)
    if not node:
        raise RuntimeError("node.exe not found")
    if not config.vite_script.exists():
        raise RuntimeError(f"Vite script not found: {config.vite_script}")

    env = _dev_environment(config, node)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    api_process, api_log = _spawn_api_service(config, env, run_id)
    web_process, web_log, web_mode = _spawn_web_service(config, env, node, run_id)
    if not generation_is_current(config):
        _stop_pids([api_process.pid, web_process.pid])
        return 0

    api_ready, web_ready = _wait_for_ready(config)
    manifest = _write_running_manifest(
        config,
        api_process,
        web_process,
        api_log,
        web_log,
        web_mode,
        api_ready,
        web_ready,
    )
    _print_json(asdict(manifest))
    if config.monitor:
        return _supervise_services(config, env, node, run_id, api_process, web_process, api_log, web_log, web_mode)
    return 0 if api_ready and web_ready else 1


def stop_dev(config: DevControlConfig) -> int:
    write_generation(config.root, f"stopped-{time.time_ns()}-{os.getpid()}")
    stopped = _stop_managed_processes(config)
    stopped.extend(_stop_configured_port_owners(config))
    _print_json({"stopped_pids": sorted(set(stopped))})
    return 0


def status_dev(config: DevControlConfig) -> int:
    manifest = read_manifest(config.manifest_path)
    payload = {
        "manifest": str(config.manifest_path),
        "api": config.api_url,
        "frontend": config.frontend_url,
        "api_http_ok": _http_ok(f"{config.api_url}/api/health"),
        "web_http_ok": _http_ok(config.frontend_url),
        "processes": None,
    }
    if manifest:
        payload["processes"] = {
            "api_pid": manifest.api_pid,
            "api_alive": _pid_alive(manifest.api_pid),
            "web_pid": manifest.web_pid,
            "web_alive": _pid_alive(manifest.web_pid),
            "web_mode": manifest.web_mode,
            "worker_pid": manifest.worker_pid,
            "worker_alive": _pid_alive(manifest.worker_pid or 0),
            "api_spawn_pid": manifest.api_spawn_pid,
            "web_spawn_pid": manifest.web_spawn_pid,
            "api_port_pids": _port_owner_pids(config.api_port),
            "web_port_pids": _port_owner_pids(config.web_port),
            "api_log": manifest.api_log,
            "web_log": manifest.web_log,
            "started_at": manifest.started_at,
        }
    _print_json(payload)
    return 0 if payload["api_http_ok"] and payload["web_http_ok"] else 1


def doctor_dev(config: DevControlConfig) -> int:
    manifest = read_manifest(config.manifest_path)
    api_http_ok = _http_ok(f"{config.api_url}/api/health")
    web_http_ok = _http_ok(config.frontend_url)
    api_port_pids = _unique_ints(_port_owner_pids(config.api_port))
    web_port_pids = _unique_ints(_port_owner_pids(config.web_port))
    browser_fetch = _browser_fetch_runtime_check(config)
    services = {
        "api": {
            "pid": manifest.api_pid if manifest else None,
            "alive": _pid_alive(manifest.api_pid) if manifest else False,
            "http_ok": api_http_ok,
            "url": f"{config.api_url}/api/health",
        },
        "web": {
            "pid": manifest.web_pid if manifest else None,
            "alive": _pid_alive(manifest.web_pid) if manifest else False,
            "http_ok": web_http_ok,
            "url": config.frontend_url,
            "mode": manifest.web_mode if manifest else "unknown",
        },
        "supervisor": {
            "pid": manifest.worker_pid if manifest else None,
            "alive": _pid_alive(manifest.worker_pid or 0) if manifest else False,
        },
    }
    payload = {
        "ok": (
            api_http_ok
            and web_http_ok
            and bool(browser_fetch.get("ok"))
            and len(api_port_pids) <= 1
            and len(web_port_pids) <= 1
        ),
        "manifest": str(config.manifest_path),
        "api": config.api_url,
        "frontend": config.frontend_url,
        "services": services,
        "runtime": {
            "browser_fetch": browser_fetch,
        },
        "ports": {
            "api": {"port": config.api_port, "owners": api_port_pids},
            "web": {"port": config.web_port, "owners": web_port_pids},
        },
        "logs": {
            "api": _log_diagnostic(manifest.api_log if manifest else ""),
            "web": _log_diagnostic(manifest.web_log if manifest else ""),
        },
        "commands": {
            "restart": _python_module_command("restart"),
            "status": _python_module_command("status"),
            "stop": _python_module_command("stop"),
        },
    }
    payload["recommendations"] = _doctor_recommendations(payload)
    _print_json(payload)
    return 0 if payload["ok"] else 1


def _browser_fetch_runtime_check(config: DevControlConfig) -> dict[str, object]:
    node = _find_node(config.root)
    script_path = supplier_browser_fetcher.resolve_script_path()
    enabled = os.environ.get("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", "1").strip().casefold() in {"1", "true", "yes", "on"}
    result: dict[str, object] = {
        "ok": False,
        "enabled": enabled,
        "node_path": node or "",
        "script_path": str(script_path),
        "error": "",
    }
    if not enabled:
        result["error"] = "browser fetch disabled"
        return result
    if not node:
        result["error"] = "node.exe not found"
        return result
    if not script_path.exists():
        result["error"] = f"browser fetch helper not found: {script_path}"
        return result

    env = _dev_environment(config, node)
    env["TENDER_KILLER_BROWSER_TIMEOUT_SECONDS"] = "1"
    env["TENDER_KILLER_BROWSER_PROVIDER"] = "runtime"
    html = "<!doctype html><title>runtime</title><main>" + ("ok " * 260) + "</main>"
    command = [node, str(script_path), "data:text/html;charset=utf-8," + quote(html)]
    try:
        process = subprocess.run(
            command,
            cwd=str(config.root),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        result["error"] = str(exc)
        return result
    if process.returncode != 0:
        result["error"] = (process.stderr or process.stdout or f"exit code {process.returncode}").strip()
        return result
    if "runtime" not in (process.stdout or ""):
        result["error"] = "browser fetch returned unexpected output"
        return result
    result["ok"] = True
    return result


def _spawn_service(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
) -> subprocess.Popen[bytes]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout = stdout_path.open("ab", buffering=0)
    stderr = stderr_path.open("ab", buffering=0)
    kwargs: dict[str, object] = {
        "cwd": str(cwd),
        "env": env,
        "stdin": subprocess.DEVNULL,
        "stdout": stdout,
        "stderr": stderr,
        "close_fds": True,
        "creationflags": _detached_creationflags(),
    }
    startupinfo = _hidden_windows_startupinfo()
    if startupinfo is not None:
        kwargs["startupinfo"] = startupinfo
    try:
        return subprocess.Popen(command, **kwargs)
    finally:
        stdout.close()
        stderr.close()


def _spawn_api_service(
    config: DevControlConfig,
    env: dict[str, str],
    run_id: str,
) -> tuple[subprocess.Popen[bytes], Path]:
    api_log = config.logs_dir / f"api-dev-{config.api_port}-{run_id}.err.log"
    process = _spawn_service(
        [
            sys.executable,
            "-m",
            "tender_killer.web_api",
            "--host",
            config.host,
            "--port",
            str(config.api_port),
        ],
        cwd=config.root,
        env=env,
        stdout_path=config.logs_dir / f"api-dev-{config.api_port}-{run_id}.out.log",
        stderr_path=api_log,
    )
    return process, api_log


def _spawn_web_service(
    config: DevControlConfig,
    env: dict[str, str],
    node: str,
    run_id: str,
) -> tuple[subprocess.Popen[bytes], Path, str]:
    existing_web_pids = _port_owner_pids(config.web_port)
    if existing_web_pids and _http_ok(config.frontend_url):
        web_log = config.logs_dir / f"web-existing-{config.web_port}-{run_id}.err.log"
        web_log.parent.mkdir(parents=True, exist_ok=True)
        web_log.touch(exist_ok=True)
        return PortBackedProcess(existing_web_pids[-1]), web_log, "vite"  # type: ignore[return-value]

    web_mode = "vite"
    web_log = config.logs_dir / f"web-vite-{config.web_port}-{run_id}.err.log"
    process = _spawn_service(
        [node, str(config.vite_script), "--host", config.host, "--port", str(config.web_port)],
        cwd=config.root / "web",
        env=env,
        stdout_path=config.logs_dir / f"web-vite-{config.web_port}-{run_id}.out.log",
        stderr_path=web_log,
    )
    time.sleep(1)
    if process.poll() is None:
        return process, web_log, web_mode

    static_root = config.root / "web" / "dist" / "index.html"
    if not static_root.exists():
        return process, web_log, web_mode

    web_mode = "static"
    web_log = config.logs_dir / f"web-static-{config.web_port}-{run_id}.err.log"
    process = _spawn_service(
        static_web_command(config),
        cwd=config.root,
        env=env,
        stdout_path=config.logs_dir / f"web-static-{config.web_port}-{run_id}.out.log",
        stderr_path=web_log,
    )
    return process, web_log, web_mode


def _write_running_manifest(
    config: DevControlConfig,
    api_process: subprocess.Popen[bytes],
    web_process: subprocess.Popen[bytes],
    api_log: Path,
    web_log: Path,
    web_mode: str,
    api_ready: bool,
    web_ready: bool,
) -> DevProcessManifest:
    manifest = DevProcessManifest(
        api_pid=_select_service_pid(api_process.pid, _port_owner_pids(config.api_port)),
        web_pid=_select_service_pid(web_process.pid, _port_owner_pids(config.web_port)),
        api=config.api_url,
        frontend=config.frontend_url,
        api_log=str(api_log),
        web_log=str(web_log),
        api_ready=api_ready,
        web_ready=web_ready,
        web_mode=web_mode,
        started_at=datetime.now().isoformat(timespec="seconds"),
        worker_pid=os.getpid(),
        api_spawn_pid=api_process.pid,
        web_spawn_pid=web_process.pid,
    )
    write_manifest(config.manifest_path, manifest)
    return manifest


def _supervise_services(
    config: DevControlConfig,
    env: dict[str, str],
    node: str,
    run_id: str,
    api_process: subprocess.Popen[bytes],
    web_process: subprocess.Popen[bytes],
    api_log: Path,
    web_log: Path,
    web_mode: str,
) -> int:
    poll_seconds = max(0.5, float(config.supervisor_poll_seconds))
    _supervisor_log(config, "Supervisor loop started.")
    while generation_is_current(config):
        time.sleep(poll_seconds)
        try:
            restarted = False
            if _service_needs_restart(
                api_process,
                config.host,
                config.api_port,
                f"{config.api_url}/api/health",
            ):
                _supervisor_log(config, "API service is unhealthy; restarting.")
                _stop_pids([api_process.pid, *_port_owner_pids(config.api_port)])
                api_process, api_log = _spawn_api_service(config, env, run_id)
                restarted = True
            if _service_needs_restart(web_process, config.host, config.web_port, config.frontend_url):
                _supervisor_log(config, "Web service is unhealthy; restarting.")
                _stop_pids([web_process.pid, *_port_owner_pids(config.web_port)])
                web_process, web_log, web_mode = _spawn_web_service(config, env, node, run_id)
                restarted = True
            if restarted and generation_is_current(config):
                api_ready, web_ready = _wait_for_ready(config)
                _write_running_manifest(
                    config,
                    api_process,
                    web_process,
                    api_log,
                    web_log,
                    web_mode,
                    api_ready,
                    web_ready,
                )
        except Exception:  # noqa: BLE001 - supervisor must keep dev services recoverable.
            _supervisor_log(config, "Supervisor loop failed:\n" + traceback.format_exc())
    _supervisor_log(config, "Supervisor loop exiting because generation changed.")
    return 0


def _detached_creationflags() -> int:
    if os.name != "nt":
        return 0
    creationflags = 0
    creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    creationflags |= getattr(subprocess, "DETACHED_PROCESS", 0)
    creationflags |= getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000)
    creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return creationflags


def _hidden_windows_startupinfo() -> object | None:
    if os.name != "nt":
        return None
    startupinfo_cls = getattr(subprocess, "STARTUPINFO", None)
    if startupinfo_cls is None:
        return None
    startupinfo = startupinfo_cls()
    startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 0x00000001)
    startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
    return startupinfo


def _print_json(payload: object) -> None:
    try:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        print(json.dumps(payload, ensure_ascii=True, indent=2))


def _service_needs_restart(
    process: subprocess.Popen[bytes],
    host: str,
    port: int,
    health_url: str,
) -> bool:
    port_open = _tcp_port_open(host, port)
    http_ok = _http_ok(health_url) if port_open else False
    if port_open and http_ok:
        return False
    if process.poll() is not None:
        return True
    return True


def _supervisor_log(config: DevControlConfig, message: str) -> None:
    try:
        config.logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat(timespec="seconds")
        with config.supervisor_log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] {message.rstrip()}\n")
    except OSError:
        pass


def _dev_environment(config: DevControlConfig, node: str) -> dict[str, str]:
    env = os.environ.copy()
    ocr_wrapper = config.root / "scripts" / "ocr-pdf.ps1"
    if ocr_wrapper.exists():
        env.setdefault(
            "TENDER_KILLER_PDF_OCR_COMMAND",
            f'powershell -NoProfile -ExecutionPolicy Bypass -File "{ocr_wrapper}" {{path}}',
        )
    env.setdefault("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", "1")
    env.setdefault("TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS", "officemag,komus,petrovich,vseinstrumenti,lemanapro")
    if "TENDER_KILLER_BROWSER_CDP_URL" not in env:
        if cdp_url := _default_browser_cdp_url(config):
            env["TENDER_KILLER_BROWSER_CDP_URL"] = cdp_url
    env.setdefault("TENDER_KILLER_BROWSER_NODE_PATH", node)
    env.setdefault("TENDER_KILLER_VITE_NODE_PATH", node)
    return env


def _default_browser_cdp_url(config: DevControlConfig) -> str | None:
    try:
        port = int(os.environ.get("TENDER_KILLER_BROWSER_CDP_PORT") or 9222)
    except ValueError:
        port = 9222
    if port <= 0:
        return None
    return f"http://127.0.0.1:{port}" if _tcp_port_open(config.host, port) else None


def _find_node(root: Path) -> str | None:
    env_node = os.environ.get("TENDER_KILLER_VITE_NODE_PATH") or os.environ.get("TENDER_KILLER_BROWSER_NODE_PATH")
    if env_node and Path(env_node).exists():
        return env_node
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        codex_bin = Path(local_appdata) / "OpenAI" / "Codex" / "bin"
        if codex_bin.exists():
            nodes = sorted(codex_bin.rglob("node.exe"), key=lambda path: path.stat().st_mtime, reverse=True)
            if nodes:
                return str(nodes[0])
    npm_node = shutil.which("node.exe") or shutil.which("node")
    if npm_node and "WindowsApps" not in npm_node:
        return npm_node
    root_node = root / "node.exe"
    return str(root_node) if root_node.exists() else None


def _python_module_command(command: str) -> str:
    return f"{sys.executable} -m tender_killer.dev_control {command}"


def _unique_ints(values: list[int]) -> list[int]:
    return list(dict.fromkeys(value for value in values if value))


def _log_diagnostic(path: str) -> dict[str, object]:
    if not path:
        return {"path": "", "exists": False, "tail": ""}
    log_path = Path(path)
    if not log_path.exists():
        return {"path": str(log_path), "exists": False, "tail": ""}
    return {"path": str(log_path), "exists": True, "tail": _read_log_tail(log_path)}


def _read_log_tail(path: Path, *, max_lines: int = 24, max_chars: int = 4000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    lines = text[-max_chars:].splitlines()
    return "\n".join(lines[-max_lines:])


def _doctor_recommendations(payload: dict[str, object]) -> list[str]:
    recommendations: list[str] = []
    commands = payload["commands"]
    assert isinstance(commands, dict)
    stop_command = str(commands["stop"])
    restart_command = str(commands["restart"])
    ports = payload["ports"]
    assert isinstance(ports, dict)
    api_port = ports["api"]
    web_port = ports["web"]
    assert isinstance(api_port, dict)
    assert isinstance(web_port, dict)
    if len(api_port["owners"]) > 1 or len(web_port["owners"]) > 1:
        recommendations.append(f"Stop stale process owners with {stop_command}, then restart.")
    services = payload["services"]
    assert isinstance(services, dict)
    api = services["api"]
    web = services["web"]
    supervisor = services.get("supervisor", {})
    assert isinstance(api, dict)
    assert isinstance(web, dict)
    assert isinstance(supervisor, dict)
    if not api["http_ok"] or not web["http_ok"]:
        recommendations.append(f"Run {restart_command} if a service is not answering HTTP.")
    if not supervisor.get("alive"):
        recommendations.append(f"Run {restart_command} because the dev supervisor is not running.")
    if web.get("mode") == "static":
        recommendations.append("Frontend is running through static fallback; check the web log before expecting Vite hot reload.")
    runtime = payload.get("runtime", {})
    browser_fetch = runtime.get("browser_fetch", {}) if isinstance(runtime, dict) else {}
    if isinstance(browser_fetch, dict) and not browser_fetch.get("ok"):
        error = str(browser_fetch.get("error") or "unknown runtime error")
        recommendations.append(f"Check the browser-fetch helper runtime: {error}.")
    logs = payload["logs"]
    assert isinstance(logs, dict)
    web_log = logs["web"]
    assert isinstance(web_log, dict)
    if "spawn EPERM" in str(web_log.get("tail") or ""):
        recommendations.append("Vite/esbuild spawn EPERM detected; static fallback keeps the UI reachable while this is investigated.")
    if not recommendations and payload["ok"]:
        recommendations.append("Dev stack looks healthy.")
    return recommendations


def _wait_for_ready(config: DevControlConfig) -> tuple[bool, bool]:
    api_ready = False
    web_ready = False
    deadline = time.monotonic() + max(1, config.timeout_seconds)
    while time.monotonic() < deadline and not (api_ready and web_ready):
        if not api_ready:
            api_ready = _tcp_port_open(config.host, config.api_port) and _http_ok(f"{config.api_url}/api/health")
        if not web_ready:
            web_ready = _tcp_port_open(config.host, config.web_port) and _http_ok(config.frontend_url)
        if not (api_ready and web_ready):
            time.sleep(0.5)
    return api_ready, web_ready


def _tcp_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except OSError:
        return False


def _http_ok(url: str) -> bool:
    try:
        request = Request(url, headers={"Accept": "application/json,text/html"})
        with urlopen(request, timeout=2) as response:  # noqa: S310 - local dev health URL.
            return 200 <= int(response.status) < 300
    except (OSError, URLError):
        return False


def _stop_managed_processes(config: DevControlConfig) -> list[int]:
    manifest = read_manifest(config.manifest_path)
    if not manifest:
        return []
    return _stop_pids(
        [
            manifest.api_pid,
            manifest.web_pid,
            manifest.api_spawn_pid or 0,
            manifest.web_spawn_pid or 0,
            manifest.worker_pid or 0,
        ]
    )


def _stop_configured_port_owners(config: DevControlConfig) -> list[int]:
    ports = (config.api_port, config.web_port, *config.extra_web_ports)
    pids: list[int] = []
    for port in dict.fromkeys(ports):
        pids.extend(_port_owner_pids(port))
    return _stop_pids(pids)


def _stop_pids(pids: list[int]) -> list[int]:
    stopped: list[int] = []
    for pid in dict.fromkeys(pid for pid in pids if pid and pid != os.getpid()):
        if _terminate_pid(pid):
            stopped.append(pid)
    return stopped


def _select_service_pid(spawn_pid: int, port_owner_pids: list[int]) -> int:
    if not port_owner_pids:
        return spawn_pid
    if spawn_pid in port_owner_pids:
        return spawn_pid
    return port_owner_pids[-1]


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        return _windows_pid_alive(pid)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _terminate_pid(pid: int) -> bool:
    if not _pid_alive(pid):
        return False
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=4,
                check=False,
            )
            if result.returncode == 0 and _wait_for_pid_exit(pid):
                return True
        except (OSError, subprocess.SubprocessError):
            pass
        try:
            os.kill(pid, signal.SIGTERM)
            return _wait_for_pid_exit(pid)
        except OSError:
            return False
    try:
        os.kill(pid, signal.SIGTERM)
        return _wait_for_pid_exit(pid)
    except OSError:
        return False


def _wait_for_pid_exit(pid: int, timeout_seconds: float = 2.0) -> bool:
    deadline = time.monotonic() + max(0.1, timeout_seconds)
    while time.monotonic() < deadline:
        if not _pid_alive(pid):
            return True
        time.sleep(0.1)
    return not _pid_alive(pid)


def _port_owner_pids(port: int) -> list[int]:
    try:
        result = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=4,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    pids: list[int] = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5 or parts[0].upper() != "TCP" or parts[-2].upper() != "LISTENING":
            continue
        local_address = parts[1]
        if local_address.endswith(f":{port}"):
            try:
                pids.append(int(parts[-1]))
            except ValueError:
                continue
    return pids


def _windows_pid_alive(pid: int) -> bool:
    still_active = 259
    process_query_limited_information = 0x1000
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(process_query_limited_information, False, int(pid))
    if not handle:
        return ctypes.get_last_error() == 5
    try:
        exit_code = ctypes.c_ulong()
        if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return int(exit_code.value) == still_active
        return True
    finally:
        kernel32.CloseHandle(handle)


def _config_from_args(args: argparse.Namespace) -> DevControlConfig:
    extra_ports = tuple(
        int(port.strip())
        for port in str(args.extra_web_ports or "").split(",")
        if port.strip()
    )
    return DevControlConfig(
        root=Path(args.root).resolve(),
        api_port=args.api_port,
        web_port=args.web_port,
        timeout_seconds=args.timeout_seconds,
        extra_web_ports=extra_ports,
        generation=str(args.generation or ""),
        monitor=bool(args.monitor),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tender-killer-dev-control")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("restart", "worker", "status", "stop", "doctor"):
        command = subparsers.add_parser(name)
        command.add_argument("--root", type=Path, default=Path.cwd())
        command.add_argument("--api-port", type=int, default=int(os.environ.get("TENDER_KILLER_API_PORT", DEFAULT_API_PORT)))
        command.add_argument("--web-port", type=int, default=int(os.environ.get("TENDER_KILLER_WEB_PORT", DEFAULT_WEB_PORT)))
        command.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
        command.add_argument(
            "--extra-web-ports",
            default=",".join(str(port) for port in DEFAULT_EXTRA_WEB_PORTS),
            help="Comma-separated stale web ports to stop as fallback.",
        )
        command.add_argument("--generation", default="")
        command.add_argument("--monitor", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = _config_from_args(args)
    if args.command == "restart":
        _print_json(start_restart_worker(config))
        return 0
    if args.command == "worker":
        return run_worker(config)
    if args.command == "status":
        return status_dev(config)
    if args.command == "stop":
        return stop_dev(config)
    if args.command == "doctor":
        return doctor_dev(config)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
