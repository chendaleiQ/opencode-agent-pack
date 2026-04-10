import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class WorkflowStateStoreTests(unittest.TestCase):
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

    def test_state_store_persists_triage_and_unique_edited_files(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(module_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'sess-1' }};
                mod.recordEditedFile(context, 'src/a.ts');
                mod.recordEditedFile(context, 'src/a.ts');
                mod.recordTriage(context, {{ lane: 'standard', complexity: 'high', risk: 'low', needsReviewer: true, finalApprovalTier: 'tier_top' }});
                const state = mod.loadState(context);
                console.log(JSON.stringify(state));
                """
            )
        state = json.loads(output)
        self.assertEqual(["src/a.ts"], state["editedFiles"])
        self.assertEqual("standard", state["triage"]["lane"])
        self.assertTrue(state["reviewer"]["required"])

    def test_initial_state_has_entry_type_phase_and_history(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(module_url)});
                const state = mod.createInitialState({{ sessionID: 'sess-1', projectKey: 'proj-a' }});
                console.log(JSON.stringify(state));
                """
            )
        state = json.loads(output)
        self.assertEqual("general", state["entryType"])
        self.assertEqual("created", state["phase"])
        self.assertTrue(len(state["phaseHistory"]) >= 1)
        self.assertIn("evidence", state)
        self.assertIn("triage", state["evidence"])
        self.assertIn("review", state["evidence"])
        self.assertIn("verification", state["evidence"])
        self.assertIn("manual", state["evidence"])
        self.assertIn("escalation", state["evidence"])

    def test_triage_moves_state_to_triaged_phase(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(module_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'sess-1' }};
                mod.recordTriage(context, {{ lane: 'quick', complexity: 'low', risk: 'low', needsReviewer: false, finalApprovalTier: 'tier_top' }});
                console.log(JSON.stringify(mod.loadState(context)));
                """
            )
        state = json.loads(output)
        self.assertEqual("triaged", state["phase"])

    def test_edit_moves_state_to_implementing_phase(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(module_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'sess-1' }};
                mod.recordEditedFile(context, 'src/a.ts');
                console.log(JSON.stringify(mod.loadState(context)));
                """
            )
        state = json.loads(output)
        self.assertEqual("implementing", state["phase"])

    def test_manual_phase_transition_to_closable_is_recorded(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(module_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'sess-1' }};
                mod.transitionPhase(context, 'closable', 'verification+review passed');
                console.log(JSON.stringify(mod.loadState(context)));
                """
            )
        state = json.loads(output)
        self.assertEqual("closable", state["phase"])
        self.assertEqual("verification+review passed", state["phaseReason"])
        self.assertTrue(
            any(item["phase"] == "closable" for item in state["phaseHistory"])
        )

    def test_edit_after_successful_verification_marks_state_stale(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(module_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'sess-1' }};
                mod.recordVerification(context, 'tests', 'npm test', 'bash');
                mod.recordEditedFile(context, 'src/a.ts');
                const state = mod.loadState(context);
                console.log(JSON.stringify(state.verification));
                """
            )
        verification = json.loads(output)
        self.assertEqual("stale", verification["status"])

    def test_state_records_typed_evidence_entries(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(module_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'sess-1' }};
                mod.recordTriage(context, {{ lane: 'standard', complexity: 'high', risk: 'low', needsReviewer: true, finalApprovalTier: 'tier_top' }});
                mod.recordReviewerResult(context, {{ specCompliance: 'pass', codeQuality: 'pass', findings: [] }});
                mod.recordVerification(context, 'tests', 'npm test', 'bash');
                mod.recordManualVerification(context, 'manual check: looked at UI');
                console.log(JSON.stringify(mod.loadState(context).evidence));
                """
            )
        evidence = json.loads(output)
        self.assertEqual(1, len(evidence["triage"]))
        self.assertEqual(1, len(evidence["review"]))
        self.assertEqual(1, len(evidence["verification"]))
        self.assertEqual(1, len(evidence["manual"]))


if __name__ == "__main__":
    unittest.main()
