import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class EvidenceStalenessTests(unittest.TestCase):
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

    def test_edit_sets_last_edit_at_timestamp(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(module_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'sess-1' }};
                mod.recordEditedFile(context, 'src/a.ts');
                const state = mod.loadState(context);
                console.log(JSON.stringify({{ lastEditAt: state.lastEditAt }}));
                """
            )
        result = json.loads(output)
        self.assertIsNotNone(result["lastEditAt"])
        self.assertIsInstance(result["lastEditAt"], str)

    def test_verification_before_edit_is_not_stale(self):
        """Verification recorded and no subsequent edit — should count as fresh."""
        gate_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(gate_url)});
            const state = {{
                phase: 'closable',
                triage: {{ lane: 'standard', needsReviewer: false }},
                evidence: {{
                    triage: [{{ kind: 'triage', at: '2026-01-01T00:00:00Z' }}],
                    review: [],
                    verification: [{{ kind: 'verification', status: 'passed', at: '2026-01-01T01:00:00Z' }}],
                    manual: [],
                    escalation: [],
                }},
                editedFiles: ['src/a.ts'],
                lastEditAt: '2026-01-01T00:30:00Z',
                verification: {{ status: 'passed', commands: [{{ category: 'tests' }}] }},
                reviewer: {{ status: 'not_required' }},
            }};
            const missing = mod.resolveMissingEvidence(state);
            console.log(JSON.stringify(missing));
            """
        )
        missing = json.loads(output)
        self.assertEqual([], missing)

    def test_verification_before_edit_becomes_stale(self):
        """Verification recorded BEFORE file edit — typed evidence should be considered stale."""
        gate_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(gate_url)});
            const state = {{
                phase: 'closable',
                triage: {{ lane: 'standard', needsReviewer: false }},
                evidence: {{
                    triage: [{{ kind: 'triage', at: '2026-01-01T00:00:00Z' }}],
                    review: [],
                    verification: [{{ kind: 'verification', status: 'passed', at: '2026-01-01T00:30:00Z' }}],
                    manual: [],
                    escalation: [],
                }},
                editedFiles: ['src/a.ts'],
                lastEditAt: '2026-01-01T01:00:00Z',
                verification: {{ status: 'stale', commands: [{{ category: 'tests' }}] }},
                reviewer: {{ status: 'not_required' }},
            }};
            const missing = mod.resolveMissingEvidence(state);
            console.log(JSON.stringify(missing));
            """
        )
        missing = json.loads(output)
        self.assertIn("missing verification evidence", missing)

    def test_fresh_verification_after_edit_is_valid(self):
        """Verification recorded AFTER file edit — should count as fresh."""
        gate_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(gate_url)});
            const state = {{
                phase: 'closable',
                triage: {{ lane: 'standard', needsReviewer: false }},
                evidence: {{
                    triage: [{{ kind: 'triage', at: '2026-01-01T00:00:00Z' }}],
                    review: [],
                    verification: [{{ kind: 'verification', status: 'passed', at: '2026-01-01T02:00:00Z' }}],
                    manual: [],
                    escalation: [],
                }},
                editedFiles: ['src/a.ts'],
                lastEditAt: '2026-01-01T01:00:00Z',
                verification: {{ status: 'passed', commands: [{{ category: 'tests' }}] }},
                reviewer: {{ status: 'not_required' }},
            }};
            const missing = mod.resolveMissingEvidence(state);
            console.log(JSON.stringify(missing));
            """
        )
        missing = json.loads(output)
        self.assertEqual([], missing)

    def test_manual_evidence_before_edit_becomes_stale(self):
        """Manual evidence recorded BEFORE file edit — should be considered stale."""
        gate_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(gate_url)});
            const state = {{
                phase: 'closable',
                triage: {{ lane: 'standard', needsReviewer: false }},
                evidence: {{
                    triage: [{{ kind: 'triage', at: '2026-01-01T00:00:00Z' }}],
                    review: [],
                    verification: [],
                    manual: [{{ kind: 'manual', status: 'passed', at: '2026-01-01T00:30:00Z' }}],
                    escalation: [],
                }},
                editedFiles: ['src/a.ts'],
                lastEditAt: '2026-01-01T01:00:00Z',
                verification: {{ status: 'stale', commands: [] }},
                reviewer: {{ status: 'not_required' }},
            }};
            const missing = mod.resolveMissingEvidence(state);
            console.log(JSON.stringify(missing));
            """
        )
        missing = json.loads(output)
        self.assertIn("missing verification evidence", missing)

    def test_integration_edit_after_verification_marks_last_edit_at(self):
        """Full integration: recordVerification → recordEditedFile → lastEditAt is set after verification."""
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(module_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'sess-1' }};
                mod.recordVerification(context, 'tests', 'npm test', 'bash');
                // Small delay to ensure timestamps differ
                await new Promise(r => setTimeout(r, 50));
                mod.recordEditedFile(context, 'src/a.ts');
                const state = mod.loadState(context);
                const verificationAt = state.evidence.verification[0]?.at;
                console.log(JSON.stringify({{
                    lastEditAt: state.lastEditAt,
                    verificationAt,
                    editIsAfter: state.lastEditAt > verificationAt,
                }}));
                """
            )
        result = json.loads(output)
        self.assertTrue(result["editIsAfter"])


if __name__ == "__main__":
    unittest.main()
