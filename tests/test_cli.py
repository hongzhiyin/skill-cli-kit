from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skill_cli_kit import cli


class SkillCliKitTest(unittest.TestCase):
    def test_init_creates_auditable_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "example-skill"
            init_out = io.StringIO()
            with redirect_stdout(init_out):
                code = cli.main(
                    [
                        "init",
                        str(project),
                        "--name",
                        "example-skill",
                        "--cli",
                        "exskill",
                        "--description",
                        "Example reusable behavior.",
                    ]
                )
            self.assertEqual(code, 0)
            self.assertTrue((project / "skill" / "SKILL.md").exists())
            self.assertTrue((project / "src" / "example_skill" / "cli.py").exists())
            self.assertTrue((project / "scripts" / "sync_skill.sh").exists())
            self.assertTrue((project / "scripts" / "update_cli.sh").exists())
            self.assertTrue(os.access(project / "scripts" / "update_cli.sh", os.X_OK))
            generated_cli = (project / "src" / "example_skill" / "cli.py").read_text(encoding="utf-8")
            self.assertIn('sub.add_parser("sync-skill"', generated_cli)
            self.assertIn("scripts/sync_skill.sh", generated_cli)
            skill_text = (project / "skill" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn('bins: ["exskill"]', skill_text)
            self.assertIn('cliHelp: "exskill --help"', skill_text)
            help_result = subprocess.run(
                ["python3", "-m", "example_skill.cli", "--help"],
                cwd=str(project),
                env={**os.environ, "PYTHONPATH": str(project / "src")},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(help_result.returncode, 0, help_result.stderr)
            self.assertIn("sync-skill", help_result.stdout)

            audit_out = io.StringIO()
            with redirect_stdout(audit_out):
                audit_code = cli.main(["audit", str(project), "--json"])
            self.assertEqual(audit_code, 0)
            payload = json.loads(audit_out.getvalue())
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["summary"]["cli_name"], "exskill")
            self.assertEqual(payload["summary"]["finding_counts"]["warn"], 0)

            status_out = io.StringIO()
            with redirect_stdout(status_out):
                status_code = cli.main(["status", str(project), "--json"])
            self.assertEqual(status_code, 0)
            self.assertEqual(json.loads(status_out.getvalue())["finding_counts"]["warn"], 0)

    def test_audit_warns_when_cli_sync_skill_command_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "example-skill"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(
                    cli.main(
                        [
                            "init",
                            str(project),
                            "--name",
                            "example-skill",
                            "--cli",
                            "exskill",
                            "--description",
                            "Example reusable behavior.",
                        ]
                    ),
                    0,
                )

            cli_path = project / "src" / "example_skill" / "cli.py"
            cli_path.write_text(
                """from __future__ import annotations

import argparse
from typing import Iterable


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="exskill")
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status")
    status.set_defaults(func=lambda args: 0)
    doctor = sub.add_parser("doctor")
    doctor.set_defaults(func=lambda args: 0)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)
""",
                encoding="utf-8",
            )

            audit_out = io.StringIO()
            with redirect_stdout(audit_out):
                audit_code = cli.main(["audit", str(project), "--json"])
            self.assertEqual(audit_code, 0)
            payload = json.loads(audit_out.getvalue())
            sync_findings = [item for item in payload["findings"] if item["category"] == "sync"]
            self.assertTrue(any("sync-skill is missing" in item["message"] for item in sync_findings))
            self.assertTrue(any("--targets, --force, and --dry-run" in item["recommendation"] for item in sync_findings))

    def test_update_runs_lifecycle_and_syncs_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "example-skill"
            codex_home = Path(tmp) / "codex-home"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(
                    cli.main(
                        [
                            "init",
                            str(project),
                            "--name",
                            "example-skill",
                            "--cli",
                            "exskill",
                            "--description",
                            "Example reusable behavior.",
                        ]
                    ),
                    0,
                )

            old_codex_home = os.environ.get("CODEX_HOME")
            os.environ["CODEX_HOME"] = str(codex_home)
            try:
                out = io.StringIO()
                with redirect_stdout(out):
                    code = cli.main(["update", str(project), "--force", "--json"])
                self.assertEqual(code, 0)
            finally:
                if old_codex_home is None:
                    os.environ.pop("CODEX_HOME", None)
                else:
                    os.environ["CODEX_HOME"] = old_codex_home

            payload = json.loads(out.getvalue())
            self.assertTrue(payload["ok"])
            self.assertEqual([step["name"] for step in payload["steps"]], ["install", "tests", "precheck", "sync", "postcheck"])
            self.assertTrue((codex_home / "skills" / "example-skill" / "bin" / "exskill").exists())

    def test_update_without_project_updates_skillcli_release(self) -> None:
        calls: list[object] = []
        original = cli.cmd_release_update

        def fake_release_update(args: object) -> int:
            calls.append(args)
            return 23

        cli.cmd_release_update = fake_release_update
        try:
            code = cli.main(["update", "--version", "0.1.1", "--no-sync-skill"])
        finally:
            cli.cmd_release_update = original

        self.assertEqual(code, 23)
        self.assertEqual(len(calls), 1)
        self.assertEqual(getattr(calls[0], "project"), None)
        self.assertEqual(getattr(calls[0], "version"), "0.1.1")
        self.assertEqual(getattr(calls[0], "sync_skill"), False)

    def test_source_update_flags_require_project(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            cli.main(["update", "--force"])
        self.assertIn("require an explicit project path", str(caught.exception))

    def test_release_update_flags_reject_project(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            cli.main(["update", ".", "--version", "0.1.1"])
        self.assertIn("release update options require no project path", str(caught.exception))

    def test_audit_reports_missing_core_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "broken"
            project.mkdir()
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli.main(["audit", str(project), "--json"])
            self.assertEqual(code, 1)
            payload = json.loads(out.getvalue())
            self.assertFalse(payload["ok"])
            error_items = [item for item in payload["findings"] if item["level"] == "error"]
            self.assertTrue(error_items)
            self.assertIn("category", error_items[0])
            self.assertIn("recommendation", error_items[0])

    def test_sync_dry_run_lists_targets(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            code = cli.main(["sync-skill", "--targets", "codex,agents", "--dry-run"])
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("codex:", text)
        self.assertIn("agents:", text)

    def test_uninstall_plan_removes_generated_launcher_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install_root = root / "skillcli-root"
            bin_dir = root / "bin"
            install_root.mkdir()
            bin_dir.mkdir()

            launcher = bin_dir / "skillcli"
            launcher.write_text(
                '#!/bin/sh\nPYTHONPATH="/tmp/skillcli/src${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m skill_cli_kit.cli "$@"\n',
                encoding="utf-8",
            )

            actions = cli.plan_native_uninstall(install_root, bin_dir, keep_skills=True)
            remove_paths = {item.path for item in actions if item.action == "remove"}
            self.assertIn(install_root, remove_paths)
            self.assertIn(launcher, remove_paths)

    def test_uninstall_plan_skips_foreign_launcher_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install_root = root / "skillcli-root"
            bin_dir = root / "bin"
            foreign = root / "foreign"
            install_root.mkdir()
            bin_dir.mkdir()
            foreign.write_text("#!/bin/sh\necho foreign\n", encoding="utf-8")
            (bin_dir / "skillcli").symlink_to(foreign)

            actions = cli.plan_native_uninstall(install_root, bin_dir, keep_skills=True)
            launcher = next(item for item in actions if item.path == bin_dir / "skillcli")
            self.assertEqual(launcher.action, "skip")
            self.assertEqual(launcher.reason, "not generated by skillcli")


if __name__ == "__main__":
    unittest.main()
