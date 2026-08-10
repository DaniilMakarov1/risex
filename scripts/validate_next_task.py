"""Validate the NEXT_TASK.md handoff contract."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "Task ID",
    "Objective",
    "Starting baseline",
    "Branch",
    "Allowed scope",
    "Forbidden scope",
    "Implementation requirements",
    "Required files",
    "Required tests",
    "Required report format",
)

HEADING_PATTERN = re.compile(r"^(##)\s+(.+?)\s*$")
TASK_DEFINITION_PATTERN = re.compile(r"^RX-[A-Z0-9][A-Z0-9-]*\s+(?:-|\u2014)\s+\S")


def parse_sections(text: str) -> tuple[dict[str, list[str]], list[str]]:
    sections: dict[str, list[str]] = {}
    duplicates: list[str] = []
    current_section: str | None = None

    for line in text.splitlines():
        heading = HEADING_PATTERN.match(line)
        if heading:
            current_section = heading.group(2).strip()
            if current_section in sections:
                duplicates.append(current_section)
            sections.setdefault(current_section, [])
            continue

        if current_section is not None:
            sections[current_section].append(line)

    return sections, duplicates


def non_empty_lines(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip()]


def task_definition_lines(sections: dict[str, list[str]]) -> list[tuple[str, str]]:
    definitions: list[tuple[str, str]] = []

    for section, lines in sections.items():
        for line in lines:
            candidate = line.strip()
            if candidate.startswith(("- ", "* ")):
                candidate = candidate[2:].strip()
            if TASK_DEFINITION_PATTERN.match(candidate):
                definitions.append((section, candidate))

    return definitions


def validate_text(text: str) -> list[str]:
    errors: list[str] = []
    sections, duplicate_sections = parse_sections(text)

    if not text.strip():
        return ["NEXT_TASK.md is empty."]

    for section in REQUIRED_SECTIONS:
        if section not in sections:
            errors.append(f"Missing required section: {section}.")
            continue
        if not non_empty_lines(sections[section]):
            errors.append(f"Required section is empty: {section}.")

    for section in duplicate_sections:
        errors.append(f"Duplicate section: {section}.")

    task_id_lines = non_empty_lines(sections.get("Task ID", []))
    if len(task_id_lines) != 1:
        errors.append("Task ID section must contain exactly one non-empty task definition line.")
    elif not TASK_DEFINITION_PATTERN.match(task_id_lines[0]):
        errors.append("Task ID section must use format: RX-000 - Short task name.")

    definitions = task_definition_lines(sections)
    if len(definitions) != 1:
        errors.append(f"NEXT_TASK.md must contain exactly one task definition; found {len(definitions)}.")
    elif definitions[0][0] != "Task ID":
        errors.append("The only task definition must appear in the Task ID section.")

    return errors


def validate_file(path: Path) -> list[str]:
    if not path.exists():
        return [f"NEXT_TASK.md file not found: {path}."]
    if not path.is_file():
        return [f"NEXT_TASK.md path is not a file: {path}."]
    return validate_text(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate NEXT_TASK.md contains exactly one complete RX task.")
    parser.add_argument("path", nargs="?", default="NEXT_TASK.md", help="Path to NEXT_TASK.md")
    args = parser.parse_args(argv)

    path = Path(args.path)
    errors = validate_file(path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"{path}: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
