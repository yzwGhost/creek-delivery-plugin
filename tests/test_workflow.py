import copy
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import workflow


class WorkflowTests(unittest.TestCase):
    def test_test_document_templates_are_snapshotted_and_required(self):
        snapshot = json.loads(workflow.bundle())
        for name in ("测试计划模板.md", "测试用例模板.md", "需求与资料核对表模板.md", "缺陷记录与回归表模板.md"):
            self.assertTrue(snapshot["rules"][name].strip())
        with tempfile.TemporaryDirectory() as folder:
            rules = Path(folder) / "references"
            shutil.copytree(workflow.RULES, rules)
            shutil.copy(workflow.RULES.parent / "SKILL.md", rules.parent / "SKILL.md")
            (rules / "测试用例模板.md").unlink()
            with patch.object(workflow, "RULES", rules):
                with self.assertRaisesRegex(ValueError, "Missing rule"):
                    workflow.bundle()

    def test_sync_protocol_required_in_snapshot(self):
        snapshot = json.loads(workflow.bundle())
        self.assertEqual(snapshot["entry"], (workflow.RULES.parent / "SKILL.md").read_text(encoding="utf8"))
        with tempfile.TemporaryDirectory() as folder:
            skill = Path(folder) / "skill"
            shutil.copytree(workflow.RULES.parent, skill)
            rules = skill / "references"
            with patch.object(workflow, "RULES", rules):
                for file in (rules / "yunxiao.md", skill / "SKILL.md"):
                    original = file.read_text(encoding="utf8")
                    for fragment in ("目标项目、", "和内容摘要", "原确认失效，", "并重新确认"):
                        with self.subTest(file=file.name, removed=fragment):
                            file.write_text(original.replace(fragment, ""), encoding="utf8")
                            with self.assertRaisesRegex(ValueError, "mandatory sync"):
                                workflow.bundle()
                    with self.subTest(file=file.name):
                        file.write_text("TODO", encoding="utf8")
                        with self.assertRaisesRegex(ValueError, "mandatory sync"):
                            workflow.bundle()
                    file.write_text(original, encoding="utf8")

    def run_cli(self, *args):
        output = io.StringIO()
        with patch.object(sys, "argv", ["workflow", *map(str, args)]):
            with contextlib.redirect_stdout(output):
                workflow.main()
        return output.getvalue()

    def test_resume_and_migration(self):
        with tempfile.TemporaryDirectory() as folder:
            batch = Path(folder) / "delivery"
            self.run_cli("start", batch)
            original = (batch / "current").read_text()
            old = self.run_cli("resume", batch)
            new = json.loads(old)
            new["workflow"]["version"] = "2.0"
            with patch.object(workflow, "bundle", return_value=json.dumps(new)):
                self.assertEqual(self.run_cli("resume", batch), old)
                token = self.run_cli("diff", batch).splitlines()[-1]
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    self.run_cli("migrate", batch)
                self.assertEqual((batch / "current").read_text(), original)
                with patch.object(workflow.os, "replace", side_effect=OSError("interrupted")):
                    with self.assertRaises(OSError):
                        self.run_cli("migrate", batch, "--confirmed-diff", token)
                self.assertEqual(self.run_cli("resume", batch), old)
                self.run_cli("migrate", batch, "--confirmed-diff", token)
                committed = json.loads((batch / "current").read_text())
                self.assertEqual(committed["migrations"], [
                    {"from": original, "to": committed["snapshot"], "diff": token}
                ])
            self.assertTrue((batch / original).is_file())
            self.assertEqual(json.loads(self.run_cli("resume", batch)), new)

    def test_invalid_graphs(self):
        base = json.loads(workflow.bundle())["workflow"]
        for stage, field, value in [
            ("plan", "dependencies", ["delivery"]),
            ("plan", "dependencies", []),
            ("plan", "role", "missing"),
            ("plan", "artifact", ""),
            ("case-sync", "dependencies", ["cases"]),
            ("case-confirm", "dependencies", ["plan"]),
            ("defect-confirm", "dependencies", ["acceptance"]),
            ("defect-sync", "dependencies", ["regression"]),
        ]:
            with self.subTest(stage=stage, field=field):
                graph = copy.deepcopy(base)
                node = next(node for node in graph["stages"] if node["id"] == stage)
                node[field] = value
                with self.assertRaises(ValueError):
                    workflow.validate(graph)
