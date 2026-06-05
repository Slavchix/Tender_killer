from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tender_killer import dev_control


def test_restart_worker_command_uses_python_module_not_shell_wrappers(tmp_path):
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
    assert "restart-dev.ps1" not in " ".join(command)
    assert "restart-dev.mjs" not in " ".join(command)


def test_detached_spawn_kwargs_do_not_keep_codex_exec_streams_open():
    kwargs = dev_control.detached_spawn_kwargs(Path.cwd())

    assert kwargs["stdin"] is subprocess.DEVNULL
    assert kwargs["stdout"] is subprocess.DEVNULL
    assert kwargs["stderr"] is subprocess.DEVNULL
    assert kwargs["cwd"] == str(Path.cwd())
    assert kwargs["close_fds"] is True


def test_dev_manifest_round_trip(tmp_path):
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


def test_generation_guard_rejects_stale_worker(tmp_path):
    config = dev_control.DevControlConfig(root=tmp_path, generation="old")
    dev_control.write_generation(config.root, "new")

    assert dev_control.generation_is_current(config) is False


def test_static_web_command_uses_python_proxy(tmp_path):
    config = dev_control.DevControlConfig(root=tmp_path, web_port=5175)

    command = dev_control.static_web_command(config)

    assert command[:3] == [sys.executable, "-m", "tender_killer.dev_static_proxy"]
    assert "--port" in command
    assert "5175" in command
    assert "--api-base-url" in command
    assert "http://127.0.0.1:8000" in command
    assert "vite" not in " ".join(command).lower()


def test_windows_termination_uses_taskkill(monkeypatch):
    calls = []
    monkeypatch.setattr(dev_control, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(dev_control.os, "name", "nt")
    monkeypatch.setattr(
        dev_control.subprocess,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs)) or subprocess.CompletedProcess(command, 0),
    )

    assert dev_control._terminate_pid(12345) is True

    assert calls[0][0] == ["taskkill", "/PID", "12345", "/T", "/F"]
    assert calls[0][1]["timeout"] == 4


def test_package_restart_script_uses_python_dev_control():
    package = json.loads(Path("package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["dev:restart"] == ".\\.venv\\Scripts\\python.exe -m tender_killer.dev_control restart"
    assert package["scripts"]["dev:status"] == ".\\.venv\\Scripts\\python.exe -m tender_killer.dev_control status"
    assert package["scripts"]["dev:stop"] == ".\\.venv\\Scripts\\python.exe -m tender_killer.dev_control stop"
