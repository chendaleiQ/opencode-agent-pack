import unittest
from pathlib import Path


class EvalRegressionSkeletonTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_eval_cases_cover_core_lane_and_escalation_scenarios(self):
        cases_dir = self.repo_root / "evals" / "cases"
        expected = [
            "quick-doc-typo-implementer-only.md",
            "quick-investigation-analyzer-only.md",
            "quick-review-reviewer-only.md",
            "quick-to-guarded-auth-escalation.md",
            "standard-feature-plan-and-batches.md",
            "strict-db-migration-destructive.md",
            "verification-failure-must-escalate.md",
        ]

        for name in expected:
            self.assertTrue((cases_dir / name).exists(), f"missing eval case: {name}")

    def test_eval_readme_documents_manual_regression_process(self):
        content = (self.repo_root / "evals" / "README.md").read_text(encoding="utf-8")
        self.assertIn("manual", content.lower())
        self.assertIn("rubric", content.lower())
        self.assertIn("cases", content.lower())


if __name__ == "__main__":
    unittest.main()
