from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from tender_killer.filters import FilterProfile


class FilterProfileStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> FilterProfile:
        if not self.path.exists():
            profile = FilterProfile.default()
            self.save(profile)
            return profile
        return FilterProfile.from_json_file(self.path)

    def save(self, profile: FilterProfile) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = _profile_to_json(profile)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def update(self, **changes: Any) -> FilterProfile:
        profile = replace(self.load(), **changes)
        self.save(profile)
        return profile


def _profile_to_json(profile: FilterProfile) -> dict[str, Any]:
    payload = asdict(profile)
    return {
        key: list(value) if isinstance(value, tuple) else value
        for key, value in payload.items()
    }
