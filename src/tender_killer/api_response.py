from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApiResponse:
    payload: dict[str, Any]
    status: int = 200
    kind: str = "json"
