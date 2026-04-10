import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class AuditLoggingTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def _run_node(self, source: str) -> str:
        result = subprocess.run(
            ["node", "--input-type=module", "-e", source],
            check=True,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def test_audit_store_appends_jsonl_records(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "audit_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                import fs from 'fs';
                const mod = await import({json.dumps(module_url)});
                mod.appendAuditRecord({{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a' }}, {{ type: 'session.created' }});
                mod.appendAuditRecord({{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a' }}, {{ type: 'completion.attempt', allowed: false }});
                const file = {json.dumps(str(Path(tmpdir) / "do-the-thing" / "audit" / "proj-a" / "audit.jsonl"))};
                console.log(fs.readFileSync(file, 'utf-8'));
                """
            )
        lines = [json.loads(line) for line in output.splitlines() if line.strip()]
        self.assertEqual(2, len(lines))
        self.assertEqual("session.created", lines[0]["type"])
        self.assertEqual("completion.attempt", lines[1]["type"])
        self.assertFalse(lines[1]["allowed"])


if __name__ == "__main__":
    unittest.main()
