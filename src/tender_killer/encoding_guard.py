from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".ps1",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yml",
    ".yaml",
}
IGNORED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
    "pytest-cache-files-full",
}


@dataclass(frozen=True)
class MojibakeFinding:
    path: Path
    line: int
    column: int
    marker: str
    excerpt: str


def default_scan_paths(root: Path) -> list[Path]:
    return [
        root / "README.md",
        root / "memory",
        root / "package.json",
        root / "scripts",
        root / "src",
        root / "web" / "index.html",
        root / "web" / "src",
        root / "web" / "vite.config.js",
    ]


def find_mojibake(text: str, path: Path) -> list[MojibakeFinding]:
    findings: list[MojibakeFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = _line_mojibake_match(line)
        if match is None:
            continue
        column, marker = match
        findings.append(
            MojibakeFinding(
                path=path,
                line=line_number,
                column=column + 1,
                marker=marker,
                excerpt=line.strip()[:160],
            )
        )
    return findings


def scan_paths(paths: list[Path] | tuple[Path, ...]) -> list[MojibakeFinding]:
    findings: list[MojibakeFinding] = []
    for path in paths:
        for text_path in _iter_text_files(path):
            try:
                text = text_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            findings.extend(find_mojibake(text, text_path))
    return findings


def _iter_text_files(path: Path):
    if _is_ignored(path):
        return
    if path.is_file():
        if path.suffix.lower() in TEXT_SUFFIXES or not path.suffix:
            yield path
        return
    if not path.is_dir():
        return
    for child in path.rglob("*"):
        if _is_ignored(child):
            continue
        if child.is_file() and child.suffix.lower() in TEXT_SUFFIXES:
            yield child


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def _line_mojibake_match(line: str) -> tuple[int, str] | None:
    matches: list[tuple[int, str]] = []
    for marker in _mojibake_markers():
        start = line.find(marker)
        while start != -1:
            matches.append((start, marker))
            start = line.find(marker, start + len(marker))
    if len(matches) < 2:
        return None
    matches.sort(key=lambda item: item[0])
    for index, (start, marker) in enumerate(matches):
        nearby = [item for item in matches[index:] if item[0] - start <= 80]
        if len(nearby) >= 2:
            return start, marker
    return None


def _mojibake_markers() -> tuple[str, ...]:
    markers: set[str] = set()
    for codepoint in range(0x0400, 0x0500):
        char = chr(codepoint)
        try:
            marker = char.encode("utf-8").decode("cp1251")
        except UnicodeDecodeError:
            continue
        if marker == char or len(marker) < 2:
            continue
        if marker.strip() != marker:
            continue
        if marker.isascii():
            continue
        markers.add(marker)
    return tuple(sorted(markers, key=lambda value: (-len(value), value)))
