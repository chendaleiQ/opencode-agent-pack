import unittest
from pathlib import Path


class PackSkillsTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_pack_includes_builtin_method_skills(self):
        skills_dir = self.repo_root / "pack" / "skills"
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
        content = (self.repo_root / "pack" / "agents" / "leader.md").read_text(
            encoding="utf-8"
        )

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
        content = (self.repo_root / "pack" / "agents" / "leader.md").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "若 quick 过程中出现失败、异常或原因不清，先插入 `systematic-debugging`",
            content,
        )
        self.assertIn(
            "若 `needsPlan=true`，先 `brainstorming`，再 `writing-plans`", content
        )
        self.assertIn(
            "reviewer（tier_mid，按 `requesting-code-review` 方式输出）", content
        )
        self.assertIn("结束前执行 `verification-before-completion`", content)

    def test_pack_prefers_builtin_skills_over_external_superpowers(self):
        content = (self.repo_root / "pack" / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("plugin 内建 method skills 优先", content)
        self.assertIn("外部工作流系统不得替代本 plugin 工作流", content)

    def test_leader_absorbs_subagent_driven_development_discipline(self):
        content = (self.repo_root / "pack" / "agents" / "leader.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("fresh context per task", content)
        self.assertIn("实现者先自检，再进入 reviewer", content)
        self.assertIn("spec compliance first, then code quality", content)

    def test_implementer_and_reviewer_reference_tdd_and_review_ordering(self):
        implementer = (self.repo_root / "pack" / "agents" / "implementer.md").read_text(
            encoding="utf-8"
        )
        reviewer = (self.repo_root / "pack" / "agents" / "reviewer.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("`test-driven-development`", implementer)
        self.assertIn('"selfReviewSummary": "short note"', implementer)
        self.assertIn("先做 spec compliance，再看 code quality", reviewer)
        self.assertIn('"specCompliance": "pass|fail"', reviewer)
        self.assertIn('"codeQuality": "pass|fail"', reviewer)
        self.assertIn('"severity": "high|medium|low"', reviewer)
        self.assertIn('"file": "path/to/file"', reviewer)
        self.assertIn('"summary": "what is wrong"', reviewer)

    def test_leader_references_plan_execution_and_branch_finish_hooks(self):
        content = (self.repo_root / "pack" / "agents" / "leader.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("plan 已存在且需要按批推进 -> `executing-plans`", content)
        self.assertIn(
            "用户进入合并/PR/保留/丢弃收尾场景 -> `finishing-a-development-branch`",
            content,
        )
        self.assertIn("有 plan 的 standard/strict 任务可按批执行", content)
        self.assertIn(
            "完成实现且验证通过后，再进入 `finishing-a-development-branch`", content
        )

    def test_readme_documents_builtin_method_skills(self):
        content = (self.repo_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("## Built-In Method Skills", content)
        self.assertIn("`change-triage` still decides the workflow skeleton", content)
        self.assertIn(
            "pack-native method skills should be preferred over external equivalents",
            content,
        )
        self.assertIn("`test-driven-development`", content)
        self.assertIn("`dispatching-parallel-agents`", content)
        self.assertIn("`executing-plans`", content)
        self.assertIn("`finishing-a-development-branch`", content)

    def test_docs_deemphasize_external_superpowers(self):
        english = (self.repo_root / "README.md").read_text(encoding="utf-8")
        chinese = (self.repo_root / "README.zh-CN.md").read_text(encoding="utf-8")

        self.assertIn("External workflow systems are not needed", english)
        self.assertIn("外部工作流系统", chinese)

    def test_docs_use_pack_methods_path_instead_of_superpowers(self):
        self.assertTrue((self.repo_root / "docs" / "pack-methods").exists())
        self.assertFalse((self.repo_root / "docs" / "superpowers").exists())


if __name__ == "__main__":
    unittest.main()
