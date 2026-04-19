import json
import subprocess
import unittest
from pathlib import Path

from tools.workflow_contract import (
    load_contract,
    planning_allows_free_text,
    planning_artifact_field,
    planning_artifact_kinds,
    planning_requires_question_tool,
    provider_policy_allowed_providers_field,
    provider_policy_namespace,
    reviewer_required_fields,
    triage_required_fields,
)


class WorkflowContractSchemaTests(unittest.TestCase):
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

    def test_contract_declares_question_only_planning_approvals(self):
        contract = load_contract()

        self.assertTrue(planning_requires_question_tool())
        self.assertFalse(planning_allows_free_text())
        self.assertEqual("planningArtifact", planning_artifact_field())
        self.assertEqual(["spec", "plan"], planning_artifact_kinds())
        self.assertIn("triage", contract)
        self.assertIn("reviewer", contract)

    def test_runtime_js_contract_matches_python_contract(self):
        module_url = (
            self.repo_root
            / ".opencode"
            / "plugins"
            / "runtime"
            / "workflow_contract.js"
        ).as_uri()
        payload = json.loads(
            self._run_node(
                f"""
                const mod = await import({json.dumps(module_url)});
                console.log(JSON.stringify({{
                  triage: mod.TRIAGE_REQUIRED_FIELDS,
                  reviewer: mod.REVIEWER_REQUIRED_FIELDS,
                  artifactField: mod.PLANNING_ARTIFACT_FIELD,
                  artifactKinds: mod.PLANNING_ARTIFACT_KINDS,
                  requiresQuestion: mod.PLANNING_REQUIRES_QUESTION_TOOL,
                  allowsFreeText: mod.PLANNING_ALLOWS_FREE_TEXT,
                }}));
                """
            )
        )

        self.assertEqual(triage_required_fields(), payload["triage"])
        self.assertEqual(reviewer_required_fields(), payload["reviewer"])
        self.assertEqual(planning_artifact_field(), payload["artifactField"])
        self.assertEqual(planning_artifact_kinds(), payload["artifactKinds"])
        self.assertEqual(planning_requires_question_tool(), payload["requiresQuestion"])
        self.assertEqual(planning_allows_free_text(), payload["allowsFreeText"])

    def test_triage_and_reviewer_docs_reference_contract_required_fields(self):
        triage_doc = (
            self.repo_root / "skills" / "dtt-change-triage" / "SKILL.md"
        ).read_text(encoding="utf-8")
        reviewer_doc = (self.repo_root / "agents" / "reviewer.md").read_text(
            encoding="utf-8"
        )

        for field in triage_required_fields():
            self.assertIn(f'"{field}"', triage_doc)
        for field in reviewer_required_fields():
            self.assertIn(f'"{field}"', reviewer_doc)

    def test_provider_policy_contract_matches_helper(self):
        policy_doc = (
            self.repo_root / "commands" / "providers.md"
        ).read_text(encoding="utf-8")

        self.assertEqual("doTheThing", provider_policy_namespace())
        self.assertEqual("allowedProviders", provider_policy_allowed_providers_field())
        self.assertIn("doTheThing.allowedProviders", policy_doc)


if __name__ == "__main__":
    unittest.main()
