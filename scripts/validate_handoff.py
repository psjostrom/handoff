#!/usr/bin/env python3
"""Deterministically validate the Handoff cross-platform plugin bundle."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

PLUGIN_ROOT = Path("plugins/handoff")
CODEX_MANIFEST = PLUGIN_ROOT / ".codex-plugin/plugin.json"
CLAUDE_MANIFEST = PLUGIN_ROOT / ".claude-plugin/plugin.json"
CURSOR_MANIFEST = PLUGIN_ROOT / ".cursor-plugin/plugin.json"
CLAUDE_COMMAND = PLUGIN_ROOT / "commands/handoff.md"
OPENCODE_COMMAND = PLUGIN_ROOT / "opencode/commands/handoff.md"
SKILL = PLUGIN_ROOT / "skills/handoff/SKILL.md"
OPENAI_METADATA = PLUGIN_ROOT / "skills/handoff/agents/openai.yaml"
DOSSIER_REF = PLUGIN_ROOT / "skills/handoff/references/dossier.md"
TIER_REF = PLUGIN_ROOT / "skills/handoff/references/tier-selection.md"
CODEX_REFERENCE = PLUGIN_ROOT / "skills/handoff/references/codex.md"
CLAUDE_REFERENCE = PLUGIN_ROOT / "skills/handoff/references/claude-code.md"
CURSOR_REFERENCE = PLUGIN_ROOT / "skills/handoff/references/cursor.md"
OPENCODE_REFERENCE = PLUGIN_ROOT / "skills/handoff/references/opencode.md"
CODEX_MARKETPLACE = Path(".agents/plugins/marketplace.json")
CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
CURSOR_MARKETPLACE = Path(".cursor-plugin/marketplace.json")
AGENTS_MD = Path("AGENTS.md")
README = Path("README.md")

DESCRIPTION = (
    "Creates self-contained handoff dossiers so a fresh standard or frontier "
    "agent can continue a task."
)
SKILL_DESCRIPTION = (
    "Creates a self-contained handoff dossier for continuing work in a fresh "
    "agent session at standard or frontier capability. Use when the user "
    "invokes /handoff, asks for a handoff, context is polluted, or work should "
    "continue on a cheaper or stronger model."
)
KEYWORDS = ["handoff", "context", "dossier", "agent-transfer"]
CODEX_INVOCATION = "$handoff:handoff"
CLAUDE_INVOCATION = "/handoff:handoff"
CURSOR_INVOCATION = "/handoff"
DEFAULT_PROMPT = (
    "Use $handoff:handoff to write a handoff dossier for the next agent."
)
AUTO_RUN_CONFIRMATION_MARKER = "never auto-run without user confirmation"
PLATFORM_REFERENCE_SECTION = "select the platform reference"
_CURSOR_BARE_INVOCATION_RE = re.compile(
    r"(?:`/handoff`|(?<![/\w])/handoff(?![/\w:]))"
)

# Presence of this key set to true is forbidden; absence is OK.
FORBIDDEN_DISABLE_TRUE = re.compile(
    r"(?m)^disable-model-invocation:\s*true\s*$"
)
ALLOW_IMPLICIT_INVOCATION_FALSE = re.compile(
    r"(?m)^\s*allow_implicit_invocation:\s*false\s*$"
)

DOSSIER_MARKERS = (
    "Receiver startup",
    "Mission",
    "Workspace",
    "State of work",
    "Decisions & hidden facts",
    "Risks & open questions",
    "Next actions",
    "Handoff metadata",
    "Resume prompt",
    "standard",
    "frontier",
)

DOSSIER_RECEIVER_STARTUP_MARKERS = (
    "Tier gate",
    "Auto",
    "unknown",
    "unlabeled",
    "proceed anyway",
    "After the gate passes",
)

DOSSIER_RECEIVER_STARTUP_ORDER = (
    "Tier gate",
    "Auto",
    "unknown",
    "unlabeled",
    "proceed anyway",
    "After the gate passes",
)

DOSSIER_RESUME_MARKERS = (
    "Required tier",
    "Auto",
    "unknown",
    "unlabeled",
    "proceed anyway",
)

TIER_MARKERS = (
    "standard",
    "frontier",
    "When unsure, recommend **standard**",
    "Prefer **standard** when",
    "Prefer **frontier** when",
    "Receiver classification",
)

TIER_RECEIVER_CLASSIFICATION_MARKERS = (
    "proceed anyway",
    "unlabeled",
)

THIN_SHELL_REQUIRED = (
    "Read completely",
    "SKILL.md",
)
THIN_SHELL_FORBIDDEN = (
    "Prefer **standard** when",
    "Prefer **frontier** when",
    "### Emphasis by tier",
)


def _display(path: Path) -> str:
    return path.as_posix()


def _load_json(repo_root: Path, relative_path: Path, errors: list[str]) -> Any:
    path = repo_root / relative_path
    if not path.is_file():
        errors.append(f"missing required JSON file: {_display(relative_path)}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"malformed JSON in {_display(relative_path)}: {exc}")
        return None


def _read_text(repo_root: Path, relative_path: Path, errors: list[str]) -> Optional[str]:
    path = repo_root / relative_path
    if not path.is_file():
        errors.append(f"missing required file: {_display(relative_path)}")
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read {_display(relative_path)}: {exc}")
        return None


def _value_at(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _require_equal(
    data: Any,
    keys: tuple[str, ...],
    expected: Any,
    label: str,
    source_path: Path,
    errors: list[str],
) -> None:
    actual = _value_at(data, *keys)
    if actual != expected:
        errors.append(
            f"{_display(source_path)}: {label} must be {expected!r}; found {actual!r}"
        )


def _valid_codex_version(value: Any) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"1\.0\.0(?:\+codex\.[a-z0-9]+(?:-[a-z0-9]+)*)?", value)
        is not None
    )


def _has_cursor_invocation(text: str) -> bool:
    return _CURSOR_BARE_INVOCATION_RE.search(text) is not None


def _parse_simple_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    block = text[4:end]
    result: dict[str, str] = {}
    for line in block.splitlines():
        if not line or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        value = raw.strip()
        if value[:1] in {'"', "'"} and value[-1:] == value[:1]:
            value = value[1:-1]
        result[key] = value
    return result


def _marketplace_has_plugin(data: Any, source: Path, errors: list[str]) -> None:
    if not isinstance(data, dict):
        errors.append(f"{_display(source)}: marketplace root must be a JSON object")
        return
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        errors.append(f"{_display(source)}: marketplace plugins must be a list")
        return
    handoff_entry: Any = None
    for entry in plugins:
        if isinstance(entry, dict) and entry.get("name") == "handoff":
            handoff_entry = entry
            break
    if handoff_entry is None:
        errors.append(f"{_display(source)}: missing handoff plugin entry")
        return
    if "description" in handoff_entry:
        _require_equal(
            handoff_entry,
            ("description",),
            DESCRIPTION,
            "marketplace handoff description",
            source,
            errors,
        )
    if "keywords" in handoff_entry:
        _require_equal(
            handoff_entry,
            ("keywords",),
            KEYWORDS,
            "marketplace handoff keywords",
            source,
            errors,
        )


def _validate_skill_adapter_reference(
    text: Optional[str], path: Path, errors: list[str]
) -> None:
    """Codex/Cursor adapters must delegate to SKILL.md and stay thin."""

    if text is None:
        return
    if "SKILL.md" not in text:
        errors.append(f"{_display(path)}: must explicitly delegate to SKILL.md")
    lowered = text.lower()
    if not (
        "follow it" in lowered
        or "owns the workflow" in lowered
        or ("read shared" in lowered and "skill.md" in lowered)
    ):
        errors.append(
            f"{_display(path)}: must explicitly delegate workflow to SKILL.md"
        )
    for marker in THIN_SHELL_FORBIDDEN:
        if marker in text:
            errors.append(
                f"{_display(path)}: adapter must not host shared workflow prose "
                f"{marker!r}"
            )


def _validate_manifests(
    codex: Any, claude: Any, cursor: Any, errors: list[str]
) -> None:
    if isinstance(codex, dict):
        _require_equal(codex, ("name",), "handoff", "Codex manifest name", CODEX_MANIFEST, errors)
        if not _valid_codex_version(codex.get("version")):
            errors.append(
                f"{_display(CODEX_MANIFEST)}: Codex manifest version must be '1.0.0' "
                "or '1.0.0+codex.<cachebuster>'"
            )
        _require_equal(codex, ("description",), DESCRIPTION, "Codex manifest description", CODEX_MANIFEST, errors)
        _require_equal(codex, ("author", "name"), "psjostrom", "Codex manifest author.name", CODEX_MANIFEST, errors)
        _require_equal(
            codex,
            ("author", "url"),
            "https://github.com/psjostrom",
            "Codex manifest author.url",
            CODEX_MANIFEST,
            errors,
        )
        _require_equal(
            codex,
            ("repository",),
            "https://github.com/psjostrom/agent-plugins",
            "Codex manifest repository",
            CODEX_MANIFEST,
            errors,
        )
        _require_equal(codex, ("keywords",), KEYWORDS, "Codex manifest keywords", CODEX_MANIFEST, errors)
        _require_equal(codex, ("skills",), "./skills/", "Codex manifest skills path", CODEX_MANIFEST, errors)
        interface_expectations = {
            "displayName": "Handoff",
            "shortDescription": "Write handoff dossiers for the next agent",
            "longDescription": (
                "Create a self-contained handoff dossier under .handoff/ so a fresh "
                "standard or frontier agent can continue the task."
            ),
            "developerName": "psjostrom",
            "category": "Developer Tools",
            "capabilities": ["Interactive", "Read", "Write"],
            "defaultPrompt": [DEFAULT_PROMPT],
        }
        for key, expected in interface_expectations.items():
            _require_equal(
                codex,
                ("interface", key),
                expected,
                f"Codex interface {key}",
                CODEX_MANIFEST,
                errors,
            )
    elif codex is not None:
        errors.append(f"{_display(CODEX_MANIFEST)}: Codex manifest root must be a JSON object")

    if isinstance(claude, dict):
        _require_equal(claude, ("name",), "handoff", "Claude manifest name", CLAUDE_MANIFEST, errors)
        if claude.get("version") != "1.0.0":
            errors.append(
                f"{_display(CLAUDE_MANIFEST)}: Claude manifest version must be exactly "
                f"'1.0.0'; found {claude.get('version')!r}"
            )
        _require_equal(claude, ("description",), DESCRIPTION, "Claude manifest description", CLAUDE_MANIFEST, errors)
        _require_equal(claude, ("author", "name"), "psjostrom", "Claude manifest author.name", CLAUDE_MANIFEST, errors)
        _require_equal(claude, ("keywords",), KEYWORDS, "Claude manifest keywords", CLAUDE_MANIFEST, errors)
    elif claude is not None:
        errors.append(f"{_display(CLAUDE_MANIFEST)}: Claude manifest root must be a JSON object")

    if isinstance(cursor, dict):
        _require_equal(cursor, ("name",), "handoff", "Cursor manifest name", CURSOR_MANIFEST, errors)
        _require_equal(cursor, ("displayName",), "Handoff", "Cursor displayName", CURSOR_MANIFEST, errors)
        if cursor.get("version") != "1.0.0":
            errors.append(
                f"{_display(CURSOR_MANIFEST)}: Cursor manifest version must be exactly "
                f"'1.0.0'; found {cursor.get('version')!r}"
            )
        _require_equal(cursor, ("description",), DESCRIPTION, "Cursor manifest description", CURSOR_MANIFEST, errors)
        _require_equal(cursor, ("author", "name"), "psjostrom", "Cursor manifest author.name", CURSOR_MANIFEST, errors)
        _require_equal(
            cursor,
            ("author", "url"),
            "https://github.com/psjostrom",
            "Cursor manifest author.url",
            CURSOR_MANIFEST,
            errors,
        )
        _require_equal(
            cursor,
            ("repository",),
            "https://github.com/psjostrom/agent-plugins",
            "Cursor manifest repository",
            CURSOR_MANIFEST,
            errors,
        )
        _require_equal(cursor, ("keywords",), KEYWORDS, "Cursor manifest keywords", CURSOR_MANIFEST, errors)
        _require_equal(cursor, ("skills",), "./skills/", "Cursor manifest skills path", CURSOR_MANIFEST, errors)
    elif cursor is not None:
        errors.append(f"{_display(CURSOR_MANIFEST)}: Cursor manifest root must be a JSON object")


def _validate_skill_text(skill: Optional[str], errors: list[str]) -> None:
    if skill is None:
        return
    fm = _parse_simple_frontmatter(skill)
    if fm.get("name") != "handoff":
        errors.append(f"{_display(SKILL)}: skill frontmatter name must be 'handoff'")
    if fm.get("description") != SKILL_DESCRIPTION:
        errors.append(
            f"{_display(SKILL)}: skill frontmatter description must match SKILL_DESCRIPTION"
        )
    if FORBIDDEN_DISABLE_TRUE.search(skill):
        errors.append(
            f"{_display(SKILL)}: must not set disable-model-invocation: true"
        )
    for marker in (
        "standard",
        "frontier",
        ".handoff/",
        "info/exclude",
        "check-ignore",
        "I recommend a",
        "do you agree",
        CODEX_INVOCATION,
        CLAUDE_INVOCATION,
    ):
        if marker not in skill:
            errors.append(f"{_display(SKILL)}: missing required marker {marker!r}")
    normalized_skill = skill.lower()
    confirmation_index = normalized_skill.find(AUTO_RUN_CONFIRMATION_MARKER)
    platform_reference_index = normalized_skill.find(PLATFORM_REFERENCE_SECTION)
    if confirmation_index < 0:
        errors.append(
            f"{_display(SKILL)}: missing required marker "
            "'never auto-run without user confirmation'"
        )
    if platform_reference_index < 0:
        errors.append(
            f"{_display(SKILL)}: missing required platform reference selection "
            f"section ({PLATFORM_REFERENCE_SECTION!r})"
        )
    elif confirmation_index >= 0 and confirmation_index > platform_reference_index:
        errors.append(
            f"{_display(SKILL)}: auto-run confirmation gate must precede "
            "platform reference selection"
        )
    if not _has_cursor_invocation(skill):
        errors.append(f"{_display(SKILL)}: missing bare Cursor invocation /handoff")


def _validate_reference_markers(
    text: Optional[str], path: Path, markers: tuple[str, ...], errors: list[str]
) -> None:
    if text is None:
        return
    for marker in markers:
        if marker not in text:
            errors.append(f"{_display(path)}: missing required marker {marker!r}")


def _section_between(text: str, start: str, end: Optional[str]) -> Optional[str]:
    start_index = text.find(start)
    if start_index < 0:
        return None
    content_start = start_index + len(start)
    if end is None:
        return text[content_start:]
    end_index = text.find(end, content_start)
    if end_index < 0:
        return text[content_start:]
    return text[content_start:end_index]


def _validate_section_markers(
    text: Optional[str],
    path: Path,
    section_name: str,
    start: str,
    end: Optional[str],
    markers: tuple[str, ...],
    errors: list[str],
) -> Optional[str]:
    if text is None:
        return None
    section = _section_between(text, start, end)
    if section is None:
        errors.append(f"{_display(path)}: missing {section_name} section")
        return None
    for marker in markers:
        if marker not in section:
            errors.append(f"{_display(path)}: missing required marker {marker!r}")
    return section


def _validate_ordered_markers(
    section: Optional[str], path: Path, section_name: str, markers: tuple[str, ...], errors: list[str]
) -> None:
    if section is None:
        return
    positions: list[int] = []
    for marker in markers:
        index = section.find(marker)
        if index < 0:
            return
        positions.append(index)
    if positions != sorted(positions):
        errors.append(
            f"{_display(path)}: {section_name} markers out of order "
            f"(expected {' -> '.join(markers)})"
        )


def _validate_dossier_contract(text: Optional[str], path: Path, errors: list[str]) -> None:
    startup = _validate_section_markers(
        text,
        path,
        "Receiver startup",
        "**Receiver startup**",
        "**Mission**",
        DOSSIER_RECEIVER_STARTUP_MARKERS,
        errors,
    )
    _validate_ordered_markers(
        startup, path, "Receiver startup", DOSSIER_RECEIVER_STARTUP_ORDER, errors
    )
    _validate_section_markers(
        text,
        path,
        "Resume prompt",
        "**Resume prompt**",
        "## Emphasis by tier",
        DOSSIER_RESUME_MARKERS,
        errors,
    )


def _validate_tier_receiver_classification(
    text: Optional[str], path: Path, errors: list[str]
) -> None:
    _validate_section_markers(
        text,
        path,
        "Receiver classification",
        "## Receiver classification",
        None,
        TIER_RECEIVER_CLASSIFICATION_MARKERS,
        errors,
    )


def _validate_thin_shell(text: Optional[str], path: Path, errors: list[str]) -> None:
    if text is None:
        return
    for marker in THIN_SHELL_REQUIRED:
        if marker not in text:
            errors.append(f"{_display(path)}: thin shell missing {marker!r}")
    for marker in THIN_SHELL_FORBIDDEN:
        if marker in text:
            errors.append(
                f"{_display(path)}: thin shell must not host shared workflow prose {marker!r}"
            )


def _validate_openai_metadata(text: Optional[str], errors: list[str]) -> None:
    if text is None:
        return
    required = (
        'display_name: "Handoff"',
        "short_description:",
        "default_prompt:",
        CODEX_INVOCATION,
    )
    for marker in required:
        if marker not in text:
            errors.append(f"{_display(OPENAI_METADATA)}: missing {marker!r}")
    if not ALLOW_IMPLICIT_INVOCATION_FALSE.search(text):
        errors.append(
            f"{_display(OPENAI_METADATA)}: allow_implicit_invocation must be false"
        )


def _validate_docs(agents: Optional[str], readme: Optional[str], errors: list[str]) -> None:
    if agents is not None:
        for marker in (
            "plugins/handoff/",
            "validate_handoff.py",
            "test_validate_handoff.py",
        ):
            if marker not in agents:
                errors.append(f"{_display(AGENTS_MD)}: missing {marker!r}")
    if readme is not None:
        for marker in ("handoff", "`/handoff`", "install-opencode.sh install handoff"):
            if marker not in readme:
                errors.append(f"{_display(README)}: missing {marker!r}")


def validate_bundle(repo_root: Path) -> list[str]:
    errors: list[str] = []

    codex = _load_json(repo_root, CODEX_MANIFEST, errors)
    claude = _load_json(repo_root, CLAUDE_MANIFEST, errors)
    cursor = _load_json(repo_root, CURSOR_MANIFEST, errors)
    _validate_manifests(codex, claude, cursor, errors)

    for market in (CODEX_MARKETPLACE, CLAUDE_MARKETPLACE, CURSOR_MARKETPLACE):
        data = _load_json(repo_root, market, errors)
        _marketplace_has_plugin(data, market, errors)

    skill = _read_text(repo_root, SKILL, errors)
    _validate_skill_text(skill, errors)
    dossier = _read_text(repo_root, DOSSIER_REF, errors)
    _validate_reference_markers(dossier, DOSSIER_REF, DOSSIER_MARKERS, errors)
    _validate_dossier_contract(dossier, DOSSIER_REF, errors)
    tier = _read_text(repo_root, TIER_REF, errors)
    _validate_reference_markers(tier, TIER_REF, TIER_MARKERS, errors)
    _validate_tier_receiver_classification(tier, TIER_REF, errors)
    for ref in (CODEX_REFERENCE, CLAUDE_REFERENCE, CURSOR_REFERENCE, OPENCODE_REFERENCE):
        text = _read_text(repo_root, ref, errors)
        if text is not None and "invocation" not in text.lower():
            errors.append(f"{_display(ref)}: must document invocation")
        if ref in (CODEX_REFERENCE, CURSOR_REFERENCE):
            _validate_skill_adapter_reference(text, ref, errors)

    _validate_thin_shell(_read_text(repo_root, CLAUDE_COMMAND, errors), CLAUDE_COMMAND, errors)
    opencode_cmd = _read_text(repo_root, OPENCODE_COMMAND, errors)
    _validate_thin_shell(opencode_cmd, OPENCODE_COMMAND, errors)
    if opencode_cmd is not None and "SHARED_ROOT" not in opencode_cmd:
        errors.append(f"{_display(OPENCODE_COMMAND)}: must resolve SHARED_ROOT")

    _validate_openai_metadata(_read_text(repo_root, OPENAI_METADATA, errors), errors)
    _validate_docs(
        _read_text(repo_root, AGENTS_MD, errors),
        _read_text(repo_root, README, errors),
        errors,
    )
    return errors


def main() -> int:
    errors = validate_bundle(Path(__file__).resolve().parents[3])
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("handoff bundle OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
