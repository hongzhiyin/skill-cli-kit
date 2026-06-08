from __future__ import annotations

import io
import json
import os
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
            skill_text = (project / "skill" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn('bins: ["exskill"]', skill_text)
            self.assertIn('cliHelp: "exskill --help"', skill_text)

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


if __name__ == "__main__":
    unittest.main()
