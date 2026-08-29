#!/usr/bin/env python3
"""Regression tests for the deterministic Handoff bundle validator."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parent
INSTALL_OPENCODE = REPOSITORY_ROOT / "install-opencode.sh"
sys.path.insert(0, str(SCRIPT_DIR))

import validate_handoff as validator  # noqa: E402

validate_bundle = validator.validate_bundle


class HandoffValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temporary_directory.name) / "handoff"
        shutil.copytree(
            REPOSITORY_ROOT,
            self.repo_root,
            ignore=shutil.ignore_patterns(".git", "__pycache__"),
        )

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
        skill = self.path("skills/handoff/SKILL.md")
        skill.unlink()
        self.assert_error("skills/handoff/SKILL.md")

    def test_valid_bundle_has_no_errors(self) -> None:
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_rejects_disable_model_invocation_true(self) -> None:
        path = self.path("skills/handoff/SKILL.md")
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
        path = self.path("skills/handoff/SKILL.md")
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
        path = self.path("skills/handoff/agents/openai.yaml")
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "  allow_implicit_invocation: false\n", ""
            ),
            encoding="utf-8",
        )
        self.assert_error("allow_implicit_invocation must be false")

    def test_rejects_implicit_invocation_false_only_in_comment(self) -> None:
        path = self.path("skills/handoff/agents/openai.yaml")
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "  allow_implicit_invocation: false\n",
                "  # allow_implicit_invocation: false\n",
            ),
            encoding="utf-8",
        )
        self.assert_error("allow_implicit_invocation must be false")

    def test_rejects_missing_platform_reference_section(self) -> None:
        path = self.path("skills/handoff/SKILL.md")
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
        path = self.path("commands/handoff.md")
        path.write_text(
            path.read_text(encoding="utf-8") + "\nPrefer **standard** when\n",
            encoding="utf-8",
        )
        self.assert_error("thin shell must not host shared workflow prose")

    def test_rejects_command_description_without_offer_trigger(self) -> None:
        invalid = "Write a handoff dossier for a fresh standard or frontier agent"
        for relative_path in ("commands/handoff.md", "opencode/commands/handoff.md"):
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
        path = self.path("skills/handoff/SKILL.md")
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
        path = self.path("skills/handoff/references/codex.md")
        self.assertIn("SKILL.md", path.read_text(encoding="utf-8"))
        self.assertIn("follow it", path.read_text(encoding="utf-8").lower())

    def test_rejects_codex_adapter_without_skill_delegation(self) -> None:
        path = self.path("skills/handoff/references/codex.md")
        path.write_text(
            "# Codex invocation\n\n## Invocation\n\n- Skill: `$handoff:handoff`\n",
            encoding="utf-8",
        )
        self.assert_error("must explicitly delegate to SKILL.md")

    def test_rejects_cursor_adapter_hosting_workflow_prose(self) -> None:
        path = self.path("skills/handoff/references/cursor.md")
        path.write_text(
            path.read_text(encoding="utf-8") + "\nPrefer **standard** when\n",
            encoding="utf-8",
        )
        self.assert_error("adapter must not host shared workflow prose")

    def test_rejects_dossier_without_receiver_tier_gate(self) -> None:
        path = self.path("skills/handoff/references/dossier.md")
        pristine = path.read_text(encoding="utf-8")
        markers = (
            *validator.DOSSIER_RECEIVER_STARTUP_MARKERS,
            *validator.DOSSIER_RESUME_MARKERS,
        )
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, pristine)
                path.write_text(pristine.replace(marker, ""), encoding="utf-8")
                self.assert_error(f"missing required marker '{marker}'")
                path.write_text(pristine, encoding="utf-8")

    def test_rejects_tier_ref_without_receiver_classification(self) -> None:
        path = self.path("skills/handoff/references/tier-selection.md")
        pristine = path.read_text(encoding="utf-8")
        markers = (
            "Receiver classification",
            *validator.TIER_RECEIVER_CLASSIFICATION_MARKERS,
        )
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, pristine)
                path.write_text(pristine.replace(marker, ""), encoding="utf-8")
                self.assert_error(f"missing required marker '{marker}'")
                path.write_text(pristine, encoding="utf-8")

    def test_rejects_dossier_gate_markers_outside_startup_section(self) -> None:
        path = self.path("skills/handoff/references/dossier.md")
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

    def test_claude_manifest_omits_version(self) -> None:
        claude_path = ".claude-plugin/plugin.json"
        claude = json.loads(self.path(claude_path).read_text(encoding="utf-8"))
        self.assertNotIn("version", claude)
        claude["version"] = "1.0.0"
        self.write_json(claude_path, claude)
        self.assert_error("must omit version")

    def test_antigravity_manifest_omits_version(self) -> None:
        ag_path = "plugin.json"
        ag = json.loads(self.path(ag_path).read_text(encoding="utf-8"))
        self.assertNotIn("version", ag)
        ag["version"] = "1.0.0"
        self.write_json(ag_path, ag)
        self.assert_error("must omit version")

    def test_rejects_non_standalone_opencode_command_suffix(self) -> None:
        path = self.path("opencode/commands/handoff.md")
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "*/opencode/commands/handoff.md)",
                "*/plugins/handoff/opencode/commands/handoff.md)",
            ),
            encoding="utf-8",
        )
        self.assert_error("standalone command suffix")


class OpenCodeInstallerTests(unittest.TestCase):
    def run_installer(
        self, root: Path, home: Path, *argv: str, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", str(root / "install-opencode.sh"), *argv],
            cwd=cwd or root,
            env={**os.environ, "HOME": str(home)},
            capture_output=True,
            text=True,
            check=False,
        )

    def remove_legacy_handoff_link(self, home: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "sh",
                "-c",
                """if [ ! -L \"$HOME/.config/opencode/commands/handoff.md\" ]; then
  echo \"Refusing: Handoff command is not a symlink.\" >&2
  exit 1
fi
case \"$(readlink \"$HOME/.config/opencode/commands/handoff.md\")\" in
  */agent-plugins/plugins/handoff/opencode/commands/handoff.md)
    rm \"$HOME/.config/opencode/commands/handoff.md\"
    ;;
  *)
    echo \"Refusing: Handoff command does not point at the legacy catalog.\" >&2
    exit 1
    ;;
esac""",
            ],
            env={**os.environ, "HOME": str(home)},
            capture_output=True,
            text=True,
            check=False,
        )

    def test_global_install_list_and_uninstall_only_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "handoff"
            shutil.copytree(
                REPOSITORY_ROOT,
                root,
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
            )
            home = Path(tmp) / "home"
            command = home / ".config/opencode/commands/handoff.md"
            foreign = home / ".config/opencode/commands/foreign.md"
            foreign.parent.mkdir(parents=True)
            foreign.symlink_to(home / "foreign.md")

            install = self.run_installer(root, home, "install")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertTrue(command.is_symlink())

            listed = self.run_installer(root, home, "list")
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertIn("Handoff installed:", listed.stdout)

            uninstall = self.run_installer(root, home, "uninstall")
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertFalse(command.exists())
            self.assertTrue(foreign.is_symlink())

    def test_project_install_list_and_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "handoff"
            project = Path(tmp) / "project"
            home = Path(tmp) / "home"
            shutil.copytree(
                REPOSITORY_ROOT,
                root,
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
            )
            project.mkdir()

            install = self.run_installer(root, home, "install", "--project", cwd=project)
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertTrue((project / ".opencode/commands/handoff.md").is_symlink())

            listed = self.run_installer(root, home, "list", "--project", cwd=project)
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertIn("Handoff installed:", listed.stdout)

            uninstall = self.run_installer(root, home, "uninstall", "--project", cwd=project)
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertFalse((project / ".opencode/commands/handoff.md").exists())

    def test_rejects_invalid_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "handoff"
            shutil.copytree(
                REPOSITORY_ROOT,
                root,
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
            )
            home = Path(tmp) / "home"
            for argv in (("install", "handoff"), ("list", "--project", "extra"), ("unknown",)):
                with self.subTest(argv=argv):
                    self.assertNotEqual(
                        self.run_installer(root, home, *argv).returncode, 0
                    )

    def test_preserves_traversal_target_at_handoff_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "handoff"
            shutil.copytree(
                REPOSITORY_ROOT,
                root,
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
            )
            home = Path(tmp) / "home"
            command = home / ".config/opencode/commands/handoff.md"
            command.parent.mkdir(parents=True)
            foreign_target = root / "opencode" / ".." / ".." / "foreign.md"
            command.symlink_to(foreign_target)

            install = self.run_installer(root, home, "install")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertEqual(command.readlink(), foreign_target)

            uninstall = self.run_installer(root, home, "uninstall")
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertEqual(command.readlink(), foreign_target)

    def test_legacy_link_migrates_only_after_guarded_removal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "handoff"
            shutil.copytree(
                REPOSITORY_ROOT,
                root,
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
            )
            home = Path(tmp) / "home"
            command = home / ".config/opencode/commands/handoff.md"
            command.parent.mkdir(parents=True)
            legacy_target = (
                Path(tmp)
                / "agent-plugins/plugins/handoff/opencode/commands/handoff.md"
            )
            command.symlink_to(legacy_target)

            install = self.run_installer(root, home, "install")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertEqual(command.readlink(), legacy_target)

            removal = self.remove_legacy_handoff_link(home)
            self.assertEqual(removal.returncode, 0, removal.stderr)
            self.assertFalse(command.is_symlink())

            install = self.run_installer(root, home, "install")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertEqual(
                command.resolve(), (root / "opencode/commands/handoff.md").resolve()
            )

            refusal = self.remove_legacy_handoff_link(home)
            self.assertNotEqual(refusal.returncode, 0)
            self.assertEqual(
                command.resolve(), (root / "opencode/commands/handoff.md").resolve()
            )


class StandalonePackagingTests(unittest.TestCase):
    def test_license_is_exact_mit(self) -> None:
        self.assertEqual(
            (REPOSITORY_ROOT / "LICENSE").read_text(encoding="utf-8"),
            "MIT License\n\nCopyright (c) 2026 Per Sjöström\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
            "of this software and associated documentation files (the \"Software\"), to deal\n"
            "in the Software without restriction, including without limitation the rights\n"
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
            "copies of the Software, and to permit persons to whom the Software is\n"
            "furnished to do so, subject to the following conditions:\n\n"
            "The above copyright notice and this permission notice shall be included in all\n"
            "copies or substantial portions of the Software.\n\n"
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
            "SOFTWARE.\n",
        )

    def test_manifests_name_standalone_repository(self) -> None:
        expected = "https://github.com/psjostrom/handoff"
        for relative_path in (
            ".codex-plugin/plugin.json",
            ".cursor-plugin/plugin.json",
        ):
            self.assertEqual(
                json.loads((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")).get(
                    "repository"
                ),
                expected,
            )

    def test_readme_documents_standalone_installs(self) -> None:
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        for marker in (
            "claude plugin marketplace add psjostrom/agent-plugins",
            "claude plugin install handoff@agent-plugins",
            "codex plugin marketplace add psjostrom/agent-plugins",
            "codex plugin add handoff@agent-plugins",
            "https://github.com/psjostrom/handoff",
            "./install-opencode.sh install",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, readme)


class AntigravityPackagingTests(unittest.TestCase):
    def test_antigravity_manifest_and_adapter(self) -> None:
        self.assertTrue((REPOSITORY_ROOT / "plugin.json").is_file())
        self.assertTrue((REPOSITORY_ROOT / "skills/handoff/references/antigravity.md").is_file())
        manifest = json.loads((REPOSITORY_ROOT / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("name"), "handoff")
        self.assertNotIn("version", manifest)


if __name__ == "__main__":
    unittest.main()

