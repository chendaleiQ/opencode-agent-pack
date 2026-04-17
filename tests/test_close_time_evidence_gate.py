import json
import subprocess
import unittest
from pathlib import Path


class CloseTimeEvidenceGateTests(unittest.TestCase):
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

    def test_close_gate_blocks_missing_triage_and_verification(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            const result = mod.evaluateCloseGate({{
              phase: 'created',
              editedFiles: ['src/a.ts'],
              verification: {{ commands: [] }},
            }});
            console.log(JSON.stringify(result));
            """
        )
        result = json.loads(output)
        self.assertFalse(result["allowed"])
        self.assertIn("state not closable", result["missing"])
        self.assertIn("missing triage", result["missing"])
        self.assertIn("missing verification evidence", result["missing"])

    def test_close_gate_requires_reviewer_when_triage_demands_it(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            const result = mod.evaluateCloseGate({{
              phase: 'verifying',
              triage: {{ lane: 'standard', needsReviewer: true }},
              editedFiles: ['src/a.ts'],
              verification: {{ commands: [{{ category: 'tests' }}] }},
              reviewer: {{ status: 'missing' }},
            }});
            console.log(JSON.stringify(result));
            """
        )
        result = json.loads(output)
        self.assertFalse(result["allowed"])
        self.assertIn("state not closable", result["missing"])
        self.assertIn("missing reviewer pass", result["missing"])

    def test_close_gate_allows_when_required_evidence_exists(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            const result = mod.evaluateCloseGate({{
              phase: 'closable',
              triage: {{ lane: 'standard', needsReviewer: true }},
              evidence: {{
                triage: [{{ kind: 'triage' }}],
                review: [{{ kind: 'review', status: 'passed' }}],
                verification: [{{ kind: 'verification', category: 'tests', status: 'passed' }}],
                manual: [],
                escalation: [],
              }},
              editedFiles: ['src/a.ts'],
              verification: {{ status: 'passed', commands: [{{ category: 'tests' }}] }},
              reviewer: {{ status: 'passed' }},
            }});
            console.log(JSON.stringify(result));
            """
        )
        result = json.loads(output)
        self.assertTrue(result["allowed"])
        self.assertEqual([], result["missing"])

    def test_close_gate_does_not_enforce_planning_gate(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            const result = mod.evaluateCloseGate({{
              phase: 'closable',
              triage: {{ lane: 'standard', needsReviewer: false }},
              planningGate: {{
                enabled: true,
                blockedStage: 'plan',
                specStatus: 'approved',
                planStatus: 'drafted',
              }},
              evidence: {{
                triage: [{{ kind: 'triage' }}],
                review: [],
                verification: [{{ kind: 'verification', category: 'tests', status: 'passed' }}],
                manual: [],
                escalation: [],
              }},
              editedFiles: ['src/a.ts'],
              verification: {{ status: 'passed', commands: [{{ category: 'tests' }}] }},
              reviewer: {{ status: 'not_required' }},
            }});
            console.log(JSON.stringify(result));
            """
        )
        result = json.loads(output)
        self.assertTrue(result["allowed"])
        self.assertNotIn("planning gate blocked at plan", result["missing"])

    def test_close_gate_allows_manual_verification(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            const result = mod.evaluateCloseGate({{
              phase: 'closable',
              triage: {{ lane: 'quick', needsReviewer: false }},
              evidence: {{
                triage: [{{ kind: 'triage' }}],
                review: [],
                verification: [],
                manual: [{{ kind: 'manual', status: 'passed' }}],
                escalation: [],
              }},
              editedFiles: ['README.md'],
              verification: {{ status: 'manual_passed', commands: [], manualChecks: [{{ note: 'manual check: verified rendered docs' }}] }},
              reviewer: {{ status: 'not_required' }},
            }});
            console.log(JSON.stringify(result));
            """
        )
        result = json.loads(output)
        self.assertTrue(result["allowed"])

    def test_close_gate_blocks_failed_verification(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            const result = mod.evaluateCloseGate({{
              phase: 'closable',
              triage: {{ lane: 'standard', needsReviewer: false }},
              editedFiles: ['src/a.ts'],
              verification: {{ status: 'failed', commands: [] }},
              reviewer: {{ status: 'not_required' }},
            }});
            console.log(JSON.stringify(result));
            """
        )
        result = json.loads(output)
        self.assertFalse(result["allowed"])
        self.assertIn("failed verification", result["missing"])

    def test_close_gate_blocks_when_phase_not_closable_even_with_evidence(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            const result = mod.evaluateCloseGate({{
              phase: 'verifying',
              triage: {{ lane: 'quick', needsReviewer: false }},
              editedFiles: ['src/a.ts'],
              verification: {{ status: 'passed', commands: [{{ category: 'tests' }}] }},
              reviewer: {{ status: 'not_required' }},
            }});
            console.log(JSON.stringify(result));
            """
        )
        result = json.loads(output)
        self.assertFalse(result["allowed"])
        self.assertIn("state not closable", result["missing"])

    def test_close_gate_reports_missing_typed_evidence_categories(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            const result = mod.evaluateCloseGate({{
              phase: 'closable',
              triage: {{ lane: 'standard', needsReviewer: true }},
              evidence: {{ triage: [], review: [], verification: [], manual: [], escalation: [] }},
              editedFiles: ['src/a.ts'],
              verification: {{ status: 'missing', commands: [] }},
              reviewer: {{ status: 'missing' }},
            }});
            console.log(JSON.stringify(result));
            """
        )
        result = json.loads(output)
        self.assertFalse(result["allowed"])
        self.assertIn("missing triage evidence", result["missing"])
        self.assertIn("missing review evidence", result["missing"])
        self.assertIn("missing verification evidence", result["missing"])

    def test_require_all_evidence_demands_review_even_without_reviewer(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            // Without requireAllEvidence — no review needed when needsReviewer=false
            const ok = mod.evaluateCloseGate({{
              phase: 'closable',
              triage: {{ lane: 'quick', needsReviewer: false }},
              evidence: {{
                triage: [{{ kind: 'triage', at: '2026-01-01T00:00:00Z' }}],
                review: [],
                verification: [{{ kind: 'verification', status: 'passed', at: '2026-01-01T02:00:00Z' }}],
                manual: [],
                escalation: [],
              }},
              editedFiles: ['src/a.ts'],
              verification: {{ status: 'passed', commands: [{{ category: 'tests' }}] }},
              reviewer: {{ status: 'not_required' }},
            }});
            // With requireAllEvidence — review required even without needsReviewer
            const strict = mod.evaluateCloseGate({{
              phase: 'closable',
              triage: {{ lane: 'quick', needsReviewer: false }},
              evidence: {{
                triage: [{{ kind: 'triage', at: '2026-01-01T00:00:00Z' }}],
                review: [],
                verification: [{{ kind: 'verification', status: 'passed', at: '2026-01-01T02:00:00Z' }}],
                manual: [],
                escalation: [],
              }},
              editedFiles: ['src/a.ts'],
              verification: {{ status: 'passed', commands: [{{ category: 'tests' }}] }},
              reviewer: {{ status: 'not_required' }},
            }}, {{ requireAllEvidence: true }});
            console.log(JSON.stringify({{ ok: ok, strict: strict }}));
            """
        )
        result = json.loads(output)
        self.assertTrue(result["ok"]["allowed"])
        self.assertFalse(result["strict"]["allowed"])
        self.assertIn("missing review evidence", result["strict"]["missing"])

    def test_staleness_disabled_ignores_old_evidence(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
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
            // With staleness enabled, old evidence is rejected
            const withStaleness = mod.resolveMissingEvidence(state, {{ checkStaleness: true }});
            // With staleness disabled, old evidence is accepted
            const withoutStaleness = mod.resolveMissingEvidence(state, {{ checkStaleness: false }});
            console.log(JSON.stringify({{ withStaleness, withoutStaleness }}));
            """
        )
        result = json.loads(output)
        self.assertIn("missing verification evidence", result["withStaleness"])
        self.assertEqual([], result["withoutStaleness"])


if __name__ == "__main__":
    unittest.main()
