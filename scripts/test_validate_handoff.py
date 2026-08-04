#!/usr/bin/env python3
"""Regression tests for the deterministic Handoff bundle validator."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(SCRIPT_DIR))

import validate_handoff as validator  # noqa: E402

validate_bundle = validator.validate_bundle


class HandoffValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temporary_directory.name)
        src = REPOSITORY_ROOT / "plugins" / "handoff"
        if src.is_dir():
            shutil.copytree(src, self.repo_root / "plugins" / "handoff")
        else:
            (self.repo_root / "plugins" / "handoff").mkdir(parents=True)
        for relative_path in (
            Path(".agents/plugins/marketplace.json"),
            Path(".claude-plugin/marketplace.json"),
            Path(".cursor-plugin/marketplace.json"),
            Path("AGENTS.md"),
            Path("README.md"),
        ):
            destination = self.repo_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPOSITORY_ROOT / relative_path, destination)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def path(self, relative_path: str) -> Path:
        return self.repo_root / relative_path

    def write_json(self, relative_path: str, value: object) -> None:
        self.path(relative_path).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def assert_error(self, fragment: str) -> list[str]:
        errors = validate_bundle(self.repo_root)
        self.assertTrue(
            any(fragment in error for error in errors),
            f"expected error containing {fragment!r}; got {errors!r}",
        )
        return errors

    def test_reports_missing_skill_when_bundle_incomplete(self) -> None:
        skill = self.path("plugins/handoff/skills/handoff/SKILL.md")
        if skill.is_file():
            skill.unlink()
        self.assert_error("plugins/handoff/skills/handoff/SKILL.md")

    def test_reports_missing_marketplace_plugin_entry(self) -> None:
        data = json.loads(
            self.path(".cursor-plugin/marketplace.json").read_text(encoding="utf-8")
        )
        data["plugins"] = [
            entry
            for entry in data["plugins"]
            if not (isinstance(entry, dict) and entry.get("name") == "handoff")
        ]
        self.write_json(".cursor-plugin/marketplace.json", data)
        self.assert_error("missing handoff plugin entry")

    def test_valid_bundle_has_no_errors(self) -> None:
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_rejects_disable_model_invocation_true(self) -> None:
        path = self.path("plugins/handoff/skills/handoff/SKILL.md")
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                "name: handoff\n",
                "name: handoff\ndisable-model-invocation: true\n",
            ),
            encoding="utf-8",
        )
        self.assert_error("must not set disable-model-invocation: true")

    def test_rejects_offer_gate_after_platform_selection(self) -> None:
        path = self.path("plugins/handoff/skills/handoff/SKILL.md")
        text = path.read_text(encoding="utf-8")
        offer_start = text.index("## 1. Offer vs execute")
        platform_start = text.index("## 2. Select the platform reference")
        offer_section = text[offer_start:platform_start]
        path.write_text(
            text[:offer_start] + text[platform_start:] + "\n" + offer_section,
            encoding="utf-8",
        )
        self.assert_error("must precede platform reference selection")

    def test_requires_explicitly_disabled_implicit_invocation(self) -> None:
        path = self.path("plugins/handoff/skills/handoff/agents/openai.yaml")
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "  allow_implicit_invocation: false\n", ""
            ),
            encoding="utf-8",
        )
        self.assert_error("allow_implicit_invocation must be false")

    def test_rejects_implicit_invocation_false_only_in_comment(self) -> None:
        path = self.path("plugins/handoff/skills/handoff/agents/openai.yaml")
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "  allow_implicit_invocation: false\n",
                "  # allow_implicit_invocation: false\n",
            ),
            encoding="utf-8",
        )
        self.assert_error("allow_implicit_invocation must be false")

    def test_rejects_missing_platform_reference_section(self) -> None:
        path = self.path("plugins/handoff/skills/handoff/SKILL.md")
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace("## 2. Select the platform reference\n", ""),
            encoding="utf-8",
        )
        self.assert_error("missing required platform reference selection section")

    def test_main_uses_repository_root_from_script_location(self) -> None:
        with mock.patch.object(validator, "validate_bundle", return_value=[]) as validate:
            self.assertEqual(0, validator.main())
        self.assertEqual((REPOSITORY_ROOT,), validate.call_args.args)

    def test_rejects_fat_claude_shell(self) -> None:
        path = self.path("plugins/handoff/commands/handoff.md")
        path.write_text(
            path.read_text(encoding="utf-8") + "\nPrefer **standard** when\n",
            encoding="utf-8",
        )
        self.assert_error("thin shell must not host shared workflow prose")

    def test_rejects_command_description_without_offer_trigger(self) -> None:
        invalid = "Write a handoff dossier for a fresh standard or frontier agent"
        for relative_path in (
            "plugins/handoff/commands/handoff.md",
            "plugins/handoff/opencode/commands/handoff.md",
        ):
            with self.subTest(path=relative_path):
                path = self.path(relative_path)
                original = path.read_text(encoding="utf-8")
                path.write_text(
                    original.replace(validator.SKILL_DESCRIPTION, invalid),
                    encoding="utf-8",
                )
                self.assert_error("command description must match SKILL_DESCRIPTION")
                path.write_text(original, encoding="utf-8")

    def test_reports_wrong_skill_description(self) -> None:
        path = self.path("plugins/handoff/skills/handoff/SKILL.md")
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                validator.SKILL_DESCRIPTION,
                "wrong description",
            ),
            encoding="utf-8",
        )
        self.assert_error("skill frontmatter description must match SKILL_DESCRIPTION")

    def test_codex_adapter_delegates_to_skill(self) -> None:
        errors = validate_bundle(self.repo_root)
        self.assertEqual([], errors)
        path = self.path("plugins/handoff/skills/handoff/references/codex.md")
        self.assertIn("SKILL.md", path.read_text(encoding="utf-8"))
        self.assertIn("follow it", path.read_text(encoding="utf-8").lower())

    def test_rejects_codex_adapter_without_skill_delegation(self) -> None:
        path = self.path("plugins/handoff/skills/handoff/references/codex.md")
        path.write_text(
            "# Codex invocation\n\n## Invocation\n\n- Skill: `$handoff:handoff`\n",
            encoding="utf-8",
        )
        self.assert_error("must explicitly delegate to SKILL.md")

    def test_rejects_cursor_adapter_hosting_workflow_prose(self) -> None:
        path = self.path("plugins/handoff/skills/handoff/references/cursor.md")
        path.write_text(
            path.read_text(encoding="utf-8") + "\nPrefer **standard** when\n",
            encoding="utf-8",
        )
        self.assert_error("adapter must not host shared workflow prose")

    def test_rejects_dossier_without_receiver_tier_gate(self) -> None:
        path = self.path("plugins/handoff/skills/handoff/references/dossier.md")
        pristine = path.read_text(encoding="utf-8")
        markers = (
            *validator.DOSSIER_RECEIVER_STARTUP_MARKERS,
            *validator.DOSSIER_RESUME_MARKERS,
        )
        for marker in markers:
            self.assertIn(marker, pristine)
            path.write_text(pristine.replace(marker, ""), encoding="utf-8")
            self.assert_error(f"missing required marker '{marker}'")
            path.write_text(pristine, encoding="utf-8")

    def test_rejects_tier_ref_without_receiver_classification(self) -> None:
        path = self.path("plugins/handoff/skills/handoff/references/tier-selection.md")
        pristine = path.read_text(encoding="utf-8")
        markers = (
            "Receiver classification",
            *validator.TIER_RECEIVER_CLASSIFICATION_MARKERS,
        )
        for marker in markers:
            self.assertIn(marker, pristine)
            path.write_text(pristine.replace(marker, ""), encoding="utf-8")
            self.assert_error(f"missing required marker '{marker}'")
            path.write_text(pristine, encoding="utf-8")

    def test_rejects_dossier_gate_markers_outside_startup_section(self) -> None:
        path = self.path("plugins/handoff/skills/handoff/references/dossier.md")
        pristine = path.read_text(encoding="utf-8")
        startup_start = pristine.index("**Receiver startup**")
        mission_start = pristine.index("**Mission**")
        stripped = (
            pristine[:startup_start]
            + "**Receiver startup** — placeholder without gate.\n\n"
            + pristine[mission_start:]
            + "\nTier gate Auto unknown unlabeled proceed anyway Required tier\n"
        )
        path.write_text(stripped, encoding="utf-8")
        self.assert_error("missing required marker 'Tier gate'")

    def test_rejects_marketplace_wrong_description_when_present(self) -> None:
        data = json.loads(
            self.path(".cursor-plugin/marketplace.json").read_text(encoding="utf-8")
        )
        for entry in data["plugins"]:
            if isinstance(entry, dict) and entry.get("name") == "handoff":
                entry["description"] = "wrong"
                break
        self.write_json(".cursor-plugin/marketplace.json", data)
        self.assert_error("marketplace handoff description")


if __name__ == "__main__":
    unittest.main()
