import unittest
from pathlib import Path


class ReleaseProcessDocsTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_release_policy_requires_protected_main_and_releasable_merges(self):
        content = (self.repo_root / "docs" / "RELEASE.md").read_text(encoding="utf-8")

        self.assertIn("main must stay releasable", content)
        self.assertIn("protect the `main` branch", content)
        self.assertIn("only merge pull requests that are ready to release", content)

    def test_maintaining_guide_requires_pr_first_development(self):
        content = (self.repo_root / "docs" / "MAINTAINING.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("All development should happen in pull requests", content)
        self.assertIn("Do not develop directly on `main`", content)
        self.assertIn("Before merging to `main`", content)


if __name__ == "__main__":
    unittest.main()
