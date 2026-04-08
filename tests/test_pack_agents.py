import unittest
from pathlib import Path


class PackAgentMetadataTests(unittest.TestCase):
    def test_helper_agents_are_hidden_subagents(self):
        repo_root = Path(__file__).resolve().parents[1]
        for name in ["analyzer", "implementer", "reviewer"]:
            content = (repo_root / "pack" / "agents" / f"{name}.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("mode: subagent", content)
            self.assertIn("hidden: true", content)


if __name__ == "__main__":
    unittest.main()
