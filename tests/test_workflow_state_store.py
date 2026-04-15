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

    def _run_node_result(self, source: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["node", "--input-type=module", "-e", source],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )

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
                mod.recordTriage(context, {{ lane: 'quick', complexity: 'low', risk: 'low', needsReviewer: false, finalApprovalTier: 'tier_top' }});
                mod.recordEditedFile(context, 'src/a.ts');
                console.log(JSON.stringify(mod.loadState(context)));
                """
            )
        state = json.loads(output)
        self.assertEqual("implementing", state["phase"])

    def test_edit_without_triage_does_not_mark_state_implementing(self):
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
        self.assertEqual("created", state["phase"])

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

    def test_initial_state_includes_planning_gate_fields(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        result = self._run_node_result(
            f"""
            const mod = await import({json.dumps(module_url)});
            const state = mod.createInitialState({{ sessionID: 'sess-1', projectKey: 'proj-a' }});
            console.log(JSON.stringify(state));
            """
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(result.stdout.strip())
        self.assertIn("planningGate", state)
        self.assertEqual(
            {
                "enabled": False,
                "blockedStage": None,
                "specStatus": "not_required",
                "planStatus": "not_required",
            },
            {
                "enabled": state["planningGate"]["enabled"],
                "blockedStage": state["planningGate"]["blockedStage"],
                "specStatus": state["planningGate"]["specStatus"],
                "planStatus": state["planningGate"]["planStatus"],
            },
        )

    def test_needs_plan_triage_enables_planning_gate_at_spec_stage(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(module_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'sess-1' }};
                mod.recordTriage(context, {{ lane: 'standard', complexity: 'high', risk: 'medium', needsPlan: true, needsReviewer: true, finalApprovalTier: 'tier_top' }});
                console.log(JSON.stringify(mod.loadState(context)));
                """
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(result.stdout.strip())
        self.assertTrue(state["triage"]["needsPlan"])
        self.assertIn("planningGate", state)
        self.assertEqual(True, state["planningGate"]["enabled"])
        self.assertEqual("spec", state["planningGate"]["blockedStage"])
        self.assertEqual("required", state["planningGate"]["specStatus"])
        self.assertEqual("required", state["planningGate"]["planStatus"])

    def test_planning_artifacts_and_approvals_are_separate_from_implementation_progress(
        self,
    ):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(module_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'sess-1' }};
                mod.recordTriage(context, {{ lane: 'standard', complexity: 'high', risk: 'medium', needsPlan: true, needsReviewer: false, finalApprovalTier: 'tier_top' }});
                mod.recordPlanningArtifact(context, 'spec', 'Need a leader-approved spec before implementation.');
                mod.recordPlanningApproval(context, 'spec', '这个方案我批准，继续写计划');
                mod.recordPlanningArtifact(context, 'plan', 'Implementation plan broken into approved steps.');
                const state = mod.loadState(context);
                console.log(JSON.stringify(state));
                """
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(result.stdout.strip())
        self.assertIn("planningGate", state)
        self.assertEqual([], state["editedFiles"])
        self.assertEqual([], state["evidence"]["verification"])
        self.assertEqual([], state["evidence"]["review"])
        self.assertEqual(1, len(state["planningGate"]["specArtifacts"]))
        self.assertEqual(1, len(state["planningGate"]["planArtifacts"]))
        self.assertEqual("approved", state["planningGate"]["specStatus"])
        self.assertEqual("drafted", state["planningGate"]["planStatus"])
        self.assertEqual("plan", state["planningGate"]["blockedStage"])

    def test_merge_child_session_state_preserves_escalation_evidence(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(module_url)});
                const parent = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'leader-1' }};
                const child = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'review-1' }};
                mod.recordTriage(parent, {{ lane: 'standard', complexity: 'high', risk: 'low', needsReviewer: true, finalApprovalTier: 'tier_top' }});
                mod.recordEscalationEvidence(child, 'reviewer recommended stricter lane', 'standard', 'strict');
                mod.mergeChildSessionState(parent, 'review-1');
                console.log(JSON.stringify(mod.loadState(parent).evidence.escalation));
                """
            )
        escalation = json.loads(output)
        self.assertEqual(1, len(escalation))
        self.assertEqual("standard", escalation[0]["fromLane"])
        self.assertEqual("strict", escalation[0]["toLane"])


if __name__ == "__main__":
    unittest.main()
