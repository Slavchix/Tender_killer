from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from tender_killer.config import Settings
from tender_killer.search_service import run_search_payload

LOGGER = logging.getLogger(__name__)


SettingsFactory = Callable[[], Settings]
Clock = Callable[[], float]


class WebSearchRunner:
    def __init__(
        self,
        settings_factory: SettingsFactory = Settings.from_env,
        pipeline_runner=None,
    ) -> None:
        self._settings_factory = settings_factory
        self._pipeline_runner = pipeline_runner
        self._lock = threading.Lock()

    def run(self, filters_payload: dict[str, Any] | None = None, trigger: str = "manual") -> dict[str, Any]:
        if not self._lock.acquire(blocking=False):
            return {
                "ok": False,
                "running": True,
                "status": "already_running",
                "message": "Поиск уже идет. Дождитесь завершения обновления.",
            }
        started_at = _utc_now()
        try:
            payload = run_search_payload(
                self._settings_factory(),
                runner=self._pipeline_runner,
                filters_payload=filters_payload,
            )
            payload["running"] = False
            payload["trigger"] = trigger
            payload["started_at"] = started_at
            payload["finished_at"] = _utc_now()
            return payload
        finally:
            self._lock.release()


class WebAutoSearchScheduler:
    def __init__(
        self,
        search_runner: WebSearchRunner,
        interval_seconds: int,
        clock: Clock = time.monotonic,
    ) -> None:
        self.search_runner = search_runner
        self.interval_seconds = max(0, int(interval_seconds))
        self._clock = clock
        self._next_run_at = self._clock() + self.interval_seconds if self.interval_seconds > 0 else float("inf")
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self.interval_seconds <= 0 or self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, name="tender-killer-web-auto-search", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def run_if_due(self) -> dict[str, Any]:
        now = self._clock()
        if now < self._next_run_at:
            return {"ran": False}
        self._next_run_at = now + self.interval_seconds
        payload = self.search_runner.run(trigger="auto")
        return {"ran": True, "payload": payload}

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            wait_seconds = max(0.0, self._next_run_at - self._clock())
            if self._stop_event.wait(wait_seconds):
                return
            try:
                result = self.run_if_due()
            except Exception as exc:  # noqa: BLE001 - background refresh must not kill the API server.
                LOGGER.warning("Web auto search failed: %s", exc)
                continue
            if result.get("ran"):
                payload = result.get("payload")
                LOGGER.info("Web auto search finished: %s", payload.get("stats") if isinstance(payload, dict) else payload)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
