import unittest
from pathlib import Path


class PackSkillsTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_pack_includes_builtin_method_skills(self):
        skills_dir = self.repo_root / "skills"
        expected = [
            "brainstorming",
            "change-triage",
            "dispatching-parallel-agents",
            "executing-plans",
            "finishing-a-development-branch",
            "receiving-code-review",
            "requesting-code-review",
            "systematic-debugging",
            "test-driven-development",
            "verification-before-completion",
            "writing-plans",
        ]

        for name in expected:
            self.assertTrue(
                (skills_dir / name / "SKILL.md").exists(), f"missing skill: {name}"
            )

    def test_leader_uses_triage_driven_skill_hooks(self):
        content = (self.repo_root / "agents" / "leader.md").read_text(encoding="utf-8")

        self.assertIn("## Built-In Method Skill Hooks", content)
        self.assertIn("needsPlan=true -> `brainstorming` then `writing-plans`", content)
        self.assertIn(
            "bugfix|investigation + failure/uncertainty -> `systematic-debugging`",
            content,
        )
        self.assertIn(
            "before any completion claim -> `verification-before-completion`",
            content,
        )

    def test_lane_protocols_include_method_skill_ordering(self):
        content = (self.repo_root / "agents" / "leader.md").read_text(encoding="utf-8")

        self.assertIn(
            "if quick encounters failure, unexpected behavior, or unclear cause, insert `systematic-debugging` first",
            content,
        )
        self.assertIn(
            "if `needsPlan=true`, run `brainstorming` first, then `writing-plans`",
            content,
        )
        self.assertIn(
            "reviewer (`tier_mid`, using `requesting-code-review` output style)",
            content,
        )
        self.assertIn("run `verification-before-completion` before closing", content)

    def test_pack_prefers_builtin_skills_over_external_superpowers(self):
        content = (self.repo_root / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("plugin-native method skills come first", content)
        self.assertIn(
            "external workflow systems must not replace this plugin workflow",
            content,
        )

    def test_leader_absorbs_subagent_driven_development_discipline(self):
        content = (self.repo_root / "agents" / "leader.md").read_text(encoding="utf-8")

        self.assertIn("fresh context per task", content)
        self.assertIn(
            "implementation tasks require implementers to self-review before work goes to reviewer",
            content,
        )
        self.assertIn("spec compliance first, then code quality", content)

    def test_implementer_and_reviewer_reference_tdd_and_review_ordering(self):
        implementer = (self.repo_root / "agents" / "implementer.md").read_text(
            encoding="utf-8"
        )
        reviewer = (self.repo_root / "agents" / "reviewer.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("`test-driven-development`", implementer)
        self.assertIn('"selfReviewSummary": "short note"', implementer)
        self.assertIn("evaluate spec compliance first, then code quality", reviewer)
        self.assertIn('"specCompliance": "pass|fail"', reviewer)
        self.assertIn('"codeQuality": "pass|fail"', reviewer)
        self.assertIn('"severity": "high|medium|low"', reviewer)
        self.assertIn('"file": "path/to/file"', reviewer)
        self.assertIn('"summary": "what is wrong"', reviewer)

    def test_leader_references_plan_execution_and_branch_finish_hooks(self):
        content = (self.repo_root / "agents" / "leader.md").read_text(encoding="utf-8")

        self.assertIn(
            "plan exists and work should advance in batches -> `executing-plans`",
            content,
        )
        self.assertIn(
            "user enters merge/PR/keep/discard closing flow -> `finishing-a-development-branch`",
            content,
        )
        self.assertIn(
            "if a plan exists, standard/strict work may proceed in batches", content
        )
        self.assertIn(
            "after implementation and verification pass, move into `finishing-a-development-branch`",
            content,
        )

    def test_readme_documents_builtin_method_skills(self):
        content = (self.repo_root / "README.md").read_text(encoding="utf-8")
        workflow = (self.repo_root / "docs" / "project" / "WORKFLOW.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## Workflow at a Glance", content)
        self.assertIn("docs/project/WORKFLOW.md", content)
        self.assertIn("docs/project/ROUTER.md", content)
        self.assertIn("`change-triage` still decides the workflow skeleton", workflow)
        self.assertIn(
            "plugin-native method skills should be preferred over external equivalents",
            workflow,
        )
        self.assertIn("`test-driven-development`", workflow)
        self.assertIn("`dispatching-parallel-agents`", workflow)
        self.assertIn("`executing-plans`", workflow)
        self.assertIn("`finishing-a-development-branch`", workflow)

    def test_docs_deemphasize_external_superpowers(self):
        english = (self.repo_root / "README.md").read_text(encoding="utf-8")
        workflow = (self.repo_root / "docs" / "project" / "WORKFLOW.md").read_text(
            encoding="utf-8"
        )
        chinese = (self.repo_root / "docs" / "project" / "README.zh-CN.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/project/WORKFLOW.md", english)
        self.assertIn("External workflow systems are not needed", workflow)
        self.assertIn("README.zh-CN", chinese)

    def test_docs_use_pack_methods_path_instead_of_superpowers(self):
        self.assertTrue((self.repo_root / "docs" / "pack-methods").exists())
        self.assertFalse((self.repo_root / "docs" / "superpowers").exists())


if __name__ == "__main__":
    unittest.main()
