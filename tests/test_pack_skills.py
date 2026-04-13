import unittest
from pathlib import Path


class PackSkillsTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_pack_includes_builtin_method_skills(self):
        skills_dir = self.repo_root / "skills"
        expected = [
            "dtt-brainstorming",
            "dtt-change-triage",
            "dtt-dispatching-parallel-agents",
            "dtt-executing-plans",
            "dtt-finishing-a-development-branch",
            "dtt-receiving-code-review",
            "dtt-requesting-code-review",
            "dtt-systematic-debugging",
            "dtt-test-driven-development",
            "dtt-verification-before-completion",
            "dtt-writing-plans",
        ]

        for name in expected:
            self.assertTrue(
                (skills_dir / name / "SKILL.md").exists(), f"missing skill: {name}"
            )

    def test_leader_uses_triage_driven_skill_hooks(self):
        content = (self.repo_root / "agents" / "leader.md").read_text(encoding="utf-8")

        self.assertIn("## Built-In Method Skill Hooks", content)
        for token in [
            "needsPlan=true",
            "`dtt-brainstorming`",
            "`dtt-writing-plans`",
            "bugfix|investigation + failure/uncertainty",
            "`dtt-systematic-debugging`",
            "before any completion claim",
            "`dtt-verification-before-completion`",
        ]:
            self.assertIn(token, content)

    def test_lane_protocols_include_method_skill_ordering(self):
        content = (self.repo_root / "agents" / "leader.md").read_text(encoding="utf-8")

        for token in [
            "if quick encounters failure, unexpected behavior, or unclear cause",
            "`dtt-systematic-debugging` first",
            "if `needsPlan=true`",
            "run `dtt-brainstorming` first",
            "`dtt-writing-plans`",
            "reviewer (`tier_mid`, using `dtt-requesting-code-review` findings-first method",
            "JSON matching `agents/reviewer.md`",
        ]:
            self.assertIn(token, content)
        self.assertIn(
            "run `dtt-verification-before-completion` before closing", content
        )

    def test_pack_prefers_builtin_skills_over_external_superpowers(self):
        content = (self.repo_root / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("plugin-native method skills come first", content)
        self.assertIn(
            "external workflow systems must not replace this plugin workflow",
            content,
        )

    def test_builtin_subagents_do_not_invoke_skills_and_docs_match(self):
        registry = (self.repo_root / "AGENTS.md").read_text(encoding="utf-8")
        leader = (self.repo_root / "agents" / "leader.md").read_text(encoding="utf-8")
        expected = "built-in subagents (`analyzer`, `implementer`, `reviewer`) must not invoke any skill"

        self.assertIn(expected, registry)
        self.assertIn(expected, leader)
        self.assertNotIn(
            "non-`leader` agents must operate only within their assigned handoff boundaries and may invoke only non-`dtt` skills appropriate to their local task",
            leader,
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

        self.assertIn("`dtt-test-driven-development`", implementer)
        self.assertIn('"selfReviewSummary": "short note"', implementer)
        self.assertIn("evaluate spec compliance first, then code quality", reviewer)
        self.assertIn('"specCompliance": "pass|fail"', reviewer)
        self.assertIn('"codeQuality": "pass|fail"', reviewer)
        self.assertIn('"severity": "high|medium|low"', reviewer)
        self.assertIn('"file": "path/to/file"', reviewer)
        self.assertIn('"summary": "what is wrong"', reviewer)

    def test_leader_references_plan_execution_and_branch_finish_hooks(self):
        content = (self.repo_root / "agents" / "leader.md").read_text(encoding="utf-8")

        for token in [
            "plan exists and work should advance in batches",
            "`dtt-executing-plans`",
            "user enters merge/PR/keep/discard closing flow",
            "`dtt-finishing-a-development-branch`",
        ]:
            self.assertIn(token, content)
        self.assertIn(
            "if a plan exists, standard/strict work may proceed in batches", content
        )
        self.assertIn(
            "after implementation and verification pass, move into `dtt-finishing-a-development-branch`",
            content,
        )

    def test_leader_reports_workflow_state_as_commentary_metadata(self):
        content = (self.repo_root / "agents" / "leader.md").read_text(encoding="utf-8")

        self.assertIn("emit a short `commentary` status marker", content)
        self.assertIn("`chat-only`", content)
        self.assertIn("emit a short `commentary` triage summary", content)
        self.assertIn("final execution summary in `commentary`", content)
        self.assertIn("concise verification evidence", content)
        self.assertIn("manual-check explanation", content)
        self.assertIn("`commentary` when closing work", content)
        self.assertIn("keep the `final` response minimal", content)

    def test_evals_expect_workflow_metadata_in_commentary(self):
        chat_only = (
            self.repo_root / "evals" / "cases" / "chat-only-status-question.md"
        ).read_text(encoding="utf-8")
        quick_upgrade = (
            self.repo_root / "evals" / "cases" / "quick-to-guarded-auth-escalation.md"
        ).read_text(encoding="utf-8")
        strict_case = (
            self.repo_root / "evals" / "cases" / "strict-db-migration-destructive.md"
        ).read_text(encoding="utf-8")
        rubric = (self.repo_root / "evals" / "rubric.md").read_text(encoding="utf-8")

        self.assertIn("workflow metadata", chat_only)
        self.assertIn("commentary", chat_only)
        self.assertIn("workflow metadata", quick_upgrade)
        self.assertIn("workflow metadata", strict_case)
        self.assertIn(
            "final unified execution summary is produced, even if emitted as workflow metadata",
            rubric,
        )

    def test_readme_documents_builtin_method_skills(self):
        content = (self.repo_root / "README.md").read_text(encoding="utf-8")
        workflow = (self.repo_root / "docs" / "project" / "WORKFLOW.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## Project Docs", content)
        self.assertIn("docs/project/WORKFLOW.md", content)
        self.assertIn("docs/project/ROUTER.md", content)
        self.assertIn(
            "`dtt-change-triage` still decides the workflow skeleton", workflow
        )
        self.assertIn(
            "plugin-native method skills should be preferred over external equivalents",
            workflow,
        )
        self.assertIn("`dtt-test-driven-development`", workflow)
        self.assertIn("`dtt-dispatching-parallel-agents`", workflow)
        self.assertIn("`dtt-executing-plans`", workflow)
        self.assertIn("`dtt-finishing-a-development-branch`", workflow)

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
