import json
import subprocess
import unittest
from pathlib import Path


class OpenCodeRuntimeTestCase(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def _run_node(self, source: str, env: dict | None = None) -> str:
        result = subprocess.run(
            ["node", "--input-type=module", "-e", source],
            check=True,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            env=env,
        )
        return result.stdout.strip()

    def _run_node_result(
        self, source: str, env: dict | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["node", "--input-type=module", "-e", source],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            env=env,
        )

    def _spec_approval_question_args(self) -> str:
        return json.dumps(
            {
                "questions": [
                    {
                        "header": "Spec 审批",
                        "multiple": False,
                        "custom": True,
                        "options": [
                            {
                                "label": "批准 spec，进入 plan",
                                "description": "Spec 已通过，可以开始写 plan。",
                            },
                            {
                                "label": "需要补充 spec",
                                "description": "Spec 还需要调整，继续停在 spec 阶段。",
                            },
                            {
                                "label": "拒绝 spec",
                                "description": "取消当前方案。",
                            },
                        ],
                        "question": "请确认当前 spec 是否通过。",
                    }
                ]
            },
            ensure_ascii=False,
        )

    def _plan_approval_question_args(self) -> str:
        return json.dumps(
            {
                "questions": [
                    {
                        "header": "Plan 审批",
                        "multiple": False,
                        "custom": True,
                        "options": [
                            {
                                "label": "批准 plan，开始实现",
                                "description": "Plan 已通过，可以进入实现。",
                            },
                            {
                                "label": "需要修改 plan",
                                "description": "Plan 还需要调整，继续停在 plan 阶段。",
                            },
                            {
                                "label": "拒绝 plan",
                                "description": "取消当前计划。",
                            },
                        ],
                        "question": "请确认当前 plan 是否通过。",
                    }
                ]
            },
            ensure_ascii=False,
        )
