from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from tender_killer import dev_control


def _workspace_tmp_path(name: str) -> Path:
    path = Path("logs") / "pytest-dev-control" / f"{name}-{time.time_ns()}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def test_restart_worker_command_uses_python_module_not_shell_wrappers():
    tmp_path = _workspace_tmp_path("restart-command")
    config = dev_control.DevControlConfig(
        root=tmp_path,
        api_port=8000,
        web_port=5175,
        timeout_seconds=12,
        generation="abc123",
    )

    command = dev_control.restart_worker_command(config)

    assert command[:4] == [sys.executable, "-m", "tender_killer.dev_control", "worker"]
    assert "--api-port" in command
    assert "8000" in command
    assert "--web-port" in command
    assert "5175" in command
    assert "--timeout-seconds" in command
    assert "12" in command
    assert "--generation" in command
    assert "abc123" in command
    assert "--monitor" in command
    assert "restart-dev.ps1" not in " ".join(command)
    assert "restart-dev.mjs" not in " ".join(command)


def test_detached_spawn_kwargs_do_not_keep_codex_exec_streams_open():
    kwargs = dev_control.detached_spawn_kwargs(Path.cwd())

    assert kwargs["stdin"] is subprocess.DEVNULL
    assert kwargs["stdout"] is subprocess.DEVNULL
    assert kwargs["stderr"] is subprocess.DEVNULL
    assert kwargs["cwd"] == str(Path.cwd())
    assert kwargs["close_fds"] is True


def test_print_json_falls_back_to_ascii_when_console_encoding_rejects(monkeypatch):
    class RejectingStdout:
        def __init__(self):
            self.parts = []

        def write(self, text):
            if "✓" in text:
                raise UnicodeEncodeError("cp1251", text, text.index("✓"), text.index("✓") + 1, "reject")
            self.parts.append(text)

        def flush(self):
            return None

    stdout = RejectingStdout()
    monkeypatch.setattr(dev_control.sys, "stdout", stdout)

    dev_control._print_json({"status": "✓"})

    assert "\\u2713" in "".join(stdout.parts)


def test_detached_spawn_kwargs_breaks_away_from_parent_job_on_windows(monkeypatch):
    monkeypatch.setattr(dev_control.os, "name", "nt")
    monkeypatch.setattr(dev_control.subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200, raising=False)
    monkeypatch.setattr(dev_control.subprocess, "DETACHED_PROCESS", 0x00000008, raising=False)
    monkeypatch.setattr(dev_control.subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000, raising=False)

    kwargs = dev_control.detached_spawn_kwargs(Path.cwd())

    assert int(kwargs["creationflags"]) & 0x01000000


def test_spawn_service_breaks_away_from_parent_job_on_windows(monkeypatch):
    tmp_path = _workspace_tmp_path("spawn-service")
    monkeypatch.setattr(dev_control.os, "name", "nt")
    monkeypatch.setattr(dev_control.subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200, raising=False)
    monkeypatch.setattr(dev_control.subprocess, "DETACHED_PROCESS", 0x00000008, raising=False)
    monkeypatch.setattr(dev_control.subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000, raising=False)
    captured = {}

    class FakeProcess:
        pid = 123

    def fake_popen(command, **kwargs):
        captured.update(kwargs)
        return FakeProcess()

    monkeypatch.setattr(dev_control.subprocess, "Popen", fake_popen)

    process = dev_control._spawn_service(
        [sys.executable, "-V"],
        cwd=tmp_path,
        env={},
        stdout_path=tmp_path / "out.log",
        stderr_path=tmp_path / "err.log",
    )

    assert process.pid == 123
    assert int(captured["creationflags"]) & 0x01000000


def test_dev_manifest_round_trip():
    tmp_path = _workspace_tmp_path("manifest")
    manifest_path = tmp_path / "logs" / "dev-processes.json"
    manifest = dev_control.DevProcessManifest(
        api_pid=123,
        web_pid=456,
        api="http://127.0.0.1:8000",
        frontend="http://127.0.0.1:5175",
        api_log=str(tmp_path / "api.err.log"),
        web_log=str(tmp_path / "web.err.log"),
        api_ready=True,
        web_ready=False,
    )

    dev_control.write_manifest(manifest_path, manifest)

    assert json.loads(manifest_path.read_text(encoding="utf-8"))["api_pid"] == 123
    assert dev_control.read_manifest(manifest_path) == manifest


def test_generation_guard_rejects_stale_worker():
    tmp_path = _workspace_tmp_path("generation")
    config = dev_control.DevControlConfig(root=tmp_path, generation="old")
    dev_control.write_generation(config.root, "new")

    assert dev_control.generation_is_current(config) is False


def test_static_web_command_uses_python_proxy():
    tmp_path = _workspace_tmp_path("static-web")
    config = dev_control.DevControlConfig(root=tmp_path, web_port=5175)

    command = dev_control.static_web_command(config)

    assert command[:3] == [sys.executable, "-m", "tender_killer.dev_static_proxy"]
    assert "--port" in command
    assert "5175" in command
    assert "--api-base-url" in command
    assert "http://127.0.0.1:8000" in command
    assert "vite" not in " ".join(command).lower()


def test_dev_environment_enables_browser_fetch_for_vseinstrumenti():
    tmp_path = _workspace_tmp_path("dev-env-browser")
    config = dev_control.DevControlConfig(root=tmp_path)
    original_tcp_port_open = dev_control._tcp_port_open
    dev_control._tcp_port_open = lambda host, port: False

    try:
        env = dev_control._dev_environment(config, "node.exe")
    finally:
        dev_control._tcp_port_open = original_tcp_port_open

    assert env["TENDER_KILLER_SUPPLIER_BROWSER_FETCH"] == "1"
    assert env["TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS"] == "officemag,vseinstrumenti"
    assert env["TENDER_KILLER_BROWSER_NODE_PATH"] == "node.exe"


def test_dev_environment_auto_attaches_open_browser_cdp(monkeypatch):
    tmp_path = _workspace_tmp_path("dev-env-cdp")
    config = dev_control.DevControlConfig(root=tmp_path)
    monkeypatch.delenv("TENDER_KILLER_BROWSER_CDP_URL", raising=False)
    monkeypatch.delenv("TENDER_KILLER_BROWSER_CDP_PORT", raising=False)
    monkeypatch.setattr(dev_control, "_tcp_port_open", lambda host, port: host == "127.0.0.1" and port == 9222)

    env = dev_control._dev_environment(config, "node.exe")

    assert env["TENDER_KILLER_BROWSER_CDP_URL"] == "http://127.0.0.1:9222"


def test_spawn_web_service_reuses_existing_healthy_frontend_port(monkeypatch):
    tmp_path = _workspace_tmp_path("reuse-web")
    config = dev_control.DevControlConfig(root=tmp_path, web_port=5175)
    monkeypatch.setattr(dev_control, "_port_owner_pids", lambda port: [321] if port == 5175 else [])
    monkeypatch.setattr(dev_control, "_http_ok", lambda url: url == config.frontend_url)
    monkeypatch.setattr(dev_control, "_pid_alive", lambda pid: pid == 321)
    monkeypatch.setattr(
        dev_control.subprocess,
        "Popen",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should reuse existing web port")),
    )

    process, log_path, web_mode = dev_control._spawn_web_service(config, {}, "node.exe", "run")

    assert process.pid == 321
    assert process.poll() is None
    assert log_path.name == "web-existing-5175-run.err.log"
    assert web_mode == "vite"


def test_windows_termination_uses_taskkill(monkeypatch):
    calls = []
    monkeypatch.setattr(dev_control, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(dev_control.os, "name", "nt")
    monkeypatch.setattr(dev_control, "_wait_for_pid_exit", lambda pid: True)
    monkeypatch.setattr(
        dev_control.subprocess,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs)) or subprocess.CompletedProcess(command, 0),
    )

    assert dev_control._terminate_pid(12345) is True

    assert calls[0][0] == ["taskkill", "/PID", "12345", "/T", "/F"]
    assert calls[0][1]["timeout"] == 4


def test_windows_termination_falls_back_to_os_kill_when_taskkill_fails(monkeypatch):
    killed = []
    monkeypatch.setattr(dev_control.os, "name", "nt")
    monkeypatch.setattr(dev_control, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(
        dev_control.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 1),
    )
    monkeypatch.setattr(dev_control.os, "kill", lambda pid, sig: killed.append((pid, sig)))
    monkeypatch.setattr(dev_control, "_wait_for_pid_exit", lambda pid: bool(killed))

    assert dev_control._terminate_pid(12345) is True

    assert killed == [(12345, dev_control.signal.SIGTERM)]


def test_windows_pid_alive_rejects_exited_process_handles(monkeypatch):
    class FakeKernel32:
        def OpenProcess(self, access, inherit, pid):  # noqa: N802 - mirrors Windows API.
            return 123

        def GetExitCodeProcess(self, handle, code_pointer):  # noqa: N802 - mirrors Windows API.
            code_pointer._obj.value = 1
            return 1

        def CloseHandle(self, handle):  # noqa: N802 - mirrors Windows API.
            return 1

    monkeypatch.setattr(dev_control.ctypes, "WinDLL", lambda name, use_last_error=True: FakeKernel32())
    monkeypatch.setattr(dev_control.ctypes, "get_last_error", lambda: 0)

    assert dev_control._windows_pid_alive(12345) is False


def test_stop_managed_processes_includes_spawn_and_worker_pids(monkeypatch):
    tmp_path = _workspace_tmp_path("stop-managed")
    config = dev_control.DevControlConfig(root=tmp_path)
    dev_control.write_manifest(
        config.manifest_path,
        dev_control.DevProcessManifest(
            api_pid=111,
            web_pid=222,
            api=config.api_url,
            frontend=config.frontend_url,
            api_log=str(tmp_path / "api.err.log"),
            web_log=str(tmp_path / "web.err.log"),
            api_ready=True,
            web_ready=True,
            worker_pid=333,
            api_spawn_pid=444,
            web_spawn_pid=555,
        ),
    )
    stopped_pids = []
    monkeypatch.setattr(dev_control, "_stop_pids", lambda pids: stopped_pids.extend(pids) or pids)

    assert dev_control._stop_managed_processes(config) == [111, 222, 444, 555, 333]
    assert stopped_pids == [111, 222, 444, 555, 333]


def test_service_needs_restart_when_process_port_or_http_is_unhealthy(monkeypatch):
    class FakeProcess:
        pid = 123

        def __init__(self, poll_result):
            self._poll_result = poll_result

        def poll(self):
            return self._poll_result

    monkeypatch.setattr(dev_control, "_tcp_port_open", lambda host, port: True)
    monkeypatch.setattr(dev_control, "_http_ok", lambda url: True)

    assert dev_control._service_needs_restart(FakeProcess(1), "127.0.0.1", 8000, "http://127.0.0.1:8000/api/health") is False

    monkeypatch.setattr(dev_control, "_tcp_port_open", lambda host, port: False)
    assert dev_control._service_needs_restart(FakeProcess(None), "127.0.0.1", 8000, "http://127.0.0.1:8000/api/health") is True

    monkeypatch.setattr(dev_control, "_tcp_port_open", lambda host, port: True)
    monkeypatch.setattr(dev_control, "_http_ok", lambda url: False)
    assert dev_control._service_needs_restart(FakeProcess(None), "127.0.0.1", 8000, "http://127.0.0.1:8000/api/health") is True

    monkeypatch.setattr(dev_control, "_http_ok", lambda url: True)
    assert dev_control._service_needs_restart(FakeProcess(None), "127.0.0.1", 8000, "http://127.0.0.1:8000/api/health") is False


def test_doctor_reports_ports_logs_and_recommendations(capsys, monkeypatch):
    tmp_path = _workspace_tmp_path("doctor")
    api_log = tmp_path / "logs" / "api.err.log"
    web_log = tmp_path / "logs" / "web.err.log"
    api_log.parent.mkdir()
    api_log.write_text("api booted\n", encoding="utf-8")
    web_log.write_text("first line\nError: spawn EPERM\n", encoding="utf-8")
    config = dev_control.DevControlConfig(root=tmp_path, api_port=8000, web_port=5175)
    dev_control.write_manifest(
        config.manifest_path,
        dev_control.DevProcessManifest(
            api_pid=111,
            web_pid=222,
            api=config.api_url,
            frontend=config.frontend_url,
            api_log=str(api_log),
            web_log=str(web_log),
            api_ready=True,
            web_ready=False,
            web_mode="static",
        ),
    )
    monkeypatch.setattr(dev_control, "_http_ok", lambda url: url.endswith("/api/health"))
    monkeypatch.setattr(dev_control, "_pid_alive", lambda pid: pid in {111, 222, 333})
    monkeypatch.setattr(
        dev_control,
        "_port_owner_pids",
        lambda port: {8000: [111], 5175: [222, 333]}.get(port, []),
    )

    exit_code = dev_control.doctor_dev(config)

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["services"]["web"]["mode"] == "static"
    assert payload["ports"]["web"]["owners"] == [222, 333]
    assert "spawn EPERM" in payload["logs"]["web"]["tail"]
    assert any("dev_control stop" in item for item in payload["recommendations"])
    assert any("static fallback" in item for item in payload["recommendations"])


def test_package_restart_script_uses_python_dev_control():
    package = json.loads(Path("package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["dev"] == ".\\.venv\\Scripts\\python.exe -m tender_killer.dev_control restart"
    assert package["scripts"]["dev:restart"] == ".\\.venv\\Scripts\\python.exe -m tender_killer.dev_control restart"
    assert package["scripts"]["dev:status"] == ".\\.venv\\Scripts\\python.exe -m tender_killer.dev_control status"
    assert package["scripts"]["dev:stop"] == ".\\.venv\\Scripts\\python.exe -m tender_killer.dev_control stop"
    assert package["scripts"]["dev:doctor"] == ".\\.venv\\Scripts\\python.exe -m tender_killer.dev_control doctor"


def test_package_smoke_script_uses_fast_api_health_check():
    package = json.loads(Path("package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["dev:smoke"] == ".\\.venv\\Scripts\\python.exe -m tender_killer.dev_health --timeout 1.5"
