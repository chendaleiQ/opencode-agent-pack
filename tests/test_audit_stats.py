import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class AuditStatsTests(unittest.TestCase):
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

    def test_audit_stats_module_exists(self):
        path = self.repo_root / ".opencode" / "plugins" / "runtime" / "audit_stats.js"
        self.assertTrue(path.exists(), "missing audit_stats.js runtime module")

    def test_empty_audit_log_returns_zero_stats(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "audit_stats.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(module_url)});
                const stats = mod.computeAuditStats({{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a' }});
                console.log(JSON.stringify(stats));
                """
            )
        stats = json.loads(output)
        self.assertEqual(0, stats["totalEvents"])
        self.assertEqual({}, stats["byType"])
        self.assertEqual([], stats["sessions"])
        self.assertEqual(0, stats["blockedAttempts"])

    def test_audit_stats_counts_events_by_type(self):
        audit_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "audit_store.js"
        ).as_uri()
        stats_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "audit_stats.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const audit = await import({json.dumps(audit_url)});
                const stats = await import({json.dumps(stats_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a' }};
                audit.appendAuditRecord(context, {{ type: 'session.created', sessionID: 'sess-1' }});
                audit.appendAuditRecord(context, {{ type: 'tool.after', sessionID: 'sess-1', tool: 'bash' }});
                audit.appendAuditRecord(context, {{ type: 'tool.after', sessionID: 'sess-1', tool: 'edit' }});
                audit.appendAuditRecord(context, {{ type: 'tool.blocked', sessionID: 'sess-2', tool: 'bash', reason: 'no-verify' }});
                audit.appendAuditRecord(context, {{ type: 'completion.attempt', sessionID: 'sess-2', allowed: false, missing: ['triage'] }});
                const result = stats.computeAuditStats(context);
                console.log(JSON.stringify(result));
                """
            )
        stats = json.loads(output)
        self.assertEqual(5, stats["totalEvents"])
        self.assertEqual(1, stats["byType"]["session.created"])
        self.assertEqual(2, stats["byType"]["tool.after"])
        self.assertEqual(1, stats["byType"]["tool.blocked"])
        self.assertEqual(1, stats["byType"]["completion.attempt"])
        self.assertIn("sess-1", stats["sessions"])
        self.assertIn("sess-2", stats["sessions"])
        self.assertEqual(2, stats["blockedAttempts"])

    def test_audit_stats_handles_malformed_lines(self):
        audit_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "audit_store.js"
        ).as_uri()
        stats_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "audit_stats.js"
        ).as_uri()
        paths_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "paths.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                import fs from 'fs';
                const paths = await import({json.dumps(paths_url)});
                const audit = await import({json.dumps(audit_url)});
                const stats = await import({json.dumps(stats_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a' }};
                // Write a valid record then a malformed line
                audit.appendAuditRecord(context, {{ type: 'session.created', sessionID: 'sess-1' }});
                const logPath = paths.auditLogPath({json.dumps(tmpdir)}, 'proj-a');
                fs.appendFileSync(logPath, 'not-json\\n', 'utf-8');
                audit.appendAuditRecord(context, {{ type: 'tool.after', sessionID: 'sess-1', tool: 'bash' }});
                const result = stats.computeAuditStats(context);
                console.log(JSON.stringify(result));
                """
            )
        stats = json.loads(output)
        self.assertEqual(2, stats["totalEvents"])


if __name__ == "__main__":
    unittest.main()
