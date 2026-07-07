from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from tender_killer.filters import FilterProfile


@dataclass(frozen=True)
class NamedFilterProfile:
    id: str
    name: str
    profile: FilterProfile


@dataclass(frozen=True)
class FilterProfileCollection:
    profiles: tuple[NamedFilterProfile, ...]
    active_profile_ids: tuple[str, ...]

    def active_profiles(self) -> tuple[NamedFilterProfile, ...]:
        active = set(self.active_profile_ids)
        return tuple(profile for profile in self.profiles if profile.id in active)


class FilterProfileStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> FilterProfile:
        collection = self.load_collection()
        active_profiles = collection.active_profiles()
        if active_profiles:
            return active_profiles[0].profile
        if collection.profiles:
            return collection.profiles[0].profile
        return FilterProfile.default()

    def load_collection(self) -> FilterProfileCollection:
        if not self.path.exists():
            collection = FilterProfileCollection(
                profiles=(
                    NamedFilterProfile(
                        id="default",
                        name="Default",
                        profile=FilterProfile.default(),
                    ),
                ),
                active_profile_ids=("default",),
            )
            self.save_collection(collection)
            return collection

        data = json.loads(self.path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("Filter profile must be a JSON object.")
        if "profiles" not in data:
            profile = FilterProfile.from_mapping(data)
            collection = FilterProfileCollection(
                profiles=(NamedFilterProfile(id="default", name="Default", profile=profile),),
                active_profile_ids=("default",),
            )
            self.save_collection(collection)
            return collection
        return _collection_from_json(data)

    def save(self, profile: FilterProfile) -> None:
        collection = FilterProfileCollection(
            profiles=(NamedFilterProfile(id="default", name="Default", profile=profile),),
            active_profile_ids=("default",),
        )
        self.save_collection(collection)

    def save_collection(self, collection: FilterProfileCollection) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = _collection_to_json(collection)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def update(self, **changes: Any) -> FilterProfile:
        collection = self.load_collection()
        target = collection.active_profiles()[0] if collection.active_profiles() else collection.profiles[0]
        profile = replace(target.profile, **changes)
        self.update_profile(target.id, profile=profile)
        return profile

    def add_profile(self, name: str, **profile_changes: Any) -> NamedFilterProfile:
        collection = self.load_collection()
        profile_id = _unique_profile_id(name, collection.profiles)
        profile = replace(FilterProfile.default(), **profile_changes)
        named = NamedFilterProfile(id=profile_id, name=name.strip() or "Profile", profile=profile)
        updated = FilterProfileCollection(
            profiles=(*collection.profiles, named),
            active_profile_ids=(*collection.active_profile_ids, named.id),
        )
        self.save_collection(updated)
        return named

    def update_profile(
        self,
        profile_id: str,
        *,
        name: str | None = None,
        profile: FilterProfile | None = None,
        **profile_changes: Any,
    ) -> NamedFilterProfile:
        collection = self.load_collection()
        profiles: list[NamedFilterProfile] = []
        updated_profile: NamedFilterProfile | None = None
        for item in collection.profiles:
            if item.id != profile_id:
                profiles.append(item)
                continue
            next_profile = profile or replace(item.profile, **profile_changes)
            updated_profile = NamedFilterProfile(
                id=item.id,
                name=name if name is not None else item.name,
                profile=next_profile,
            )
            profiles.append(updated_profile)
        if updated_profile is None:
            raise ValueError(f"Unknown profile id: {profile_id}")
        self.save_collection(
            FilterProfileCollection(
                profiles=tuple(profiles),
                active_profile_ids=collection.active_profile_ids,
            )
        )
        return updated_profile

    def set_profile_enabled(self, profile_id: str, enabled: bool) -> FilterProfileCollection:
        collection = self.load_collection()
        known_ids = {profile.id for profile in collection.profiles}
        if profile_id not in known_ids:
            raise ValueError(f"Unknown profile id: {profile_id}")
        active = list(collection.active_profile_ids)
        if enabled and profile_id not in active:
            active.append(profile_id)
        if not enabled:
            active = [item for item in active if item != profile_id]
        updated = FilterProfileCollection(
            profiles=collection.profiles,
            active_profile_ids=tuple(active),
        )
        self.save_collection(updated)
        return updated


def _profile_to_json(profile: FilterProfile) -> dict[str, Any]:
    payload = asdict(profile)
    return {
        key: list(value) if isinstance(value, tuple) else value
        for key, value in payload.items()
    }


def _collection_from_json(data: dict[str, Any]) -> FilterProfileCollection:
    raw_profiles = data.get("profiles")
    if not isinstance(raw_profiles, list):
        raise ValueError("Filter profile collection must contain profiles array.")
    profiles = []
    for raw in raw_profiles:
        if not isinstance(raw, dict):
            continue
        profile_data = raw.get("profile", raw)
        if not isinstance(profile_data, dict):
            continue
        profile_id = str(raw.get("id") or _slugify(str(raw.get("name") or "profile")))
        profiles.append(
            NamedFilterProfile(
                id=profile_id,
                name=str(raw.get("name") or profile_id),
                profile=FilterProfile.from_mapping(profile_data),
            )
        )
    active_ids = tuple(str(item) for item in data.get("active_profile_ids", ()))
    return FilterProfileCollection(profiles=tuple(profiles), active_profile_ids=active_ids)


def _collection_to_json(collection: FilterProfileCollection) -> dict[str, Any]:
    return {
        "profiles": [
            {
                "id": profile.id,
                "name": profile.name,
                "profile": _profile_to_json(profile.profile),
            }
            for profile in collection.profiles
        ],
        "active_profile_ids": list(collection.active_profile_ids),
    }


def _unique_profile_id(name: str, profiles: tuple[NamedFilterProfile, ...]) -> str:
    base = _slugify(name) or "profile"
    used = {profile.id for profile in profiles}
    if base not in used:
        return base
    index = 2
    while f"{base}-{index}" in used:
        index += 1
    return f"{base}-{index}"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ]+", "-", value.strip().lower()).strip("-")
    return slug or "profile"
