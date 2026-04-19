import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class EvalRuntimeRegressionTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        self.evidence_gate_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js"
        ).as_uri()

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

    def _spec_question_args(self) -> str:
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

    def test_case_structured_approvals_require_question_path(self):
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "strict",
                    "complexity": "high",
                    "risk": "high",
                    "needsPlan": True,
                    "needsReviewer": True,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        spec_question_args = self._spec_question_args()

        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(self.plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm2', partID: 'p2' }},
                  {{ text: JSON.stringify({{ planningArtifact: 'spec', summary: 'spec drafted' }}) }}
                );
                await hooks['chat.message'](
                  {{ sessionID: 'leader-1', agent: 'leader', messageID: 'm3' }},
                  {{ parts: [{{ text: 'approved' }}] }}
                );
                await hooks['tool.execute.before'](
                  {{ tool: 'question', sessionID: 'leader-1', callID: 'call-spec-question' }},
                  {{ args: {spec_question_args} }}
                );
                await hooks.event({{
                  event: {{
                    type: 'question.asked',
                    properties: {{ id: 'q-spec-1', sessionID: 'leader-1', ...{spec_question_args} }},
                  }},
                }});
                await hooks.event({{
                  event: {{
                    type: 'question.replied',
                    properties: {{
                      sessionID: 'leader-1',
                      requestID: 'q-spec-1',
                      answers: [['批准 spec，进入 plan']],
                    }},
                  }},
                }});
                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'leader-1.json'), 'utf-8'));
                console.log(JSON.stringify(state.planningGate));
                """,
                env=env,
            )
        planning_gate = json.loads(output)
        self.assertEqual("approved", planning_gate["specStatus"])
        self.assertEqual("plan", planning_gate["blockedStage"])
        self.assertEqual(1, len(planning_gate["decisions"]))

    def test_case_verification_failure_must_block_close(self):
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                }
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                import fs from 'fs';
                import path from 'path';
                const plugin = await import({json.dumps(self.plugin_url)});
                const gate = await import({json.dumps(self.evidence_gate_url)});
                const hooks = await plugin.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                await hooks['tool.execute.after'](
                  {{ tool: 'edit', sessionID: 'leader-1', callID: 'call-edit', args: {{ filePath: 'src/a.ts' }} }},
                  {{ title: 'edit', output: '', metadata: {{}} }}
                );
                await hooks['tool.execute.before'](
                  {{ tool: 'bash', sessionID: 'leader-1', callID: 'call-test' }},
                  {{ args: {{ command: 'npm test' }} }}
                );
                await hooks['tool.execute.after'](
                  {{
                    tool: 'bash',
                    sessionID: 'leader-1',
                    callID: 'call-test',
                    args: {{ command: 'npm test' }},
                  }},
                  {{
                    title: 'npm test failed',
                    output: 'tests failed: 1 failing suite',
                    metadata: {{ exitCode: 1 }},
                  }}
                );
                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'leader-1.json'), 'utf-8'));
                const result = gate.evaluateCloseGate({{ ...state, phase: 'closable' }});
                console.log(JSON.stringify({{ verification: state.verification, closeGate: result }}));
                """,
                env=env,
            )
        payload = json.loads(output)
        self.assertEqual("failed", payload["verification"]["status"])
        self.assertIn("failed verification", payload["closeGate"]["missing"])

    def test_case_reviewer_recommends_escalation_records_evidence(self):
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsReviewer": True,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        reviewer_output = json.dumps(
            json.dumps(
                {
                    "verdict": "escalate",
                    "reviewTierUsed": "tier_mid",
                    "specCompliance": "fail",
                    "codeQuality": "fail",
                    "mustEscalate": True,
                    "recommendedLane": "strict",
                    "recommendedTierUpgrade": {
                        "needed": True,
                        "from": "tier_mid",
                        "to": "tier_top",
                        "reason": "auth-sensitive path needs stricter review",
                    },
                    "scopeDrift": False,
                    "unresolvedRisk": True,
                    "sensitiveHit": {
                        "touchesAuth": True,
                        "touchesDbSchema": False,
                        "touchesPublicApi": False,
                        "touchesDestructiveAction": False,
                    },
                    "verifyStatus": "failed",
                    "endGateCheck": {
                        "quickReady": False,
                        "standardReady": False,
                        "guardedReady": False,
                        "strictReady": False,
                    },
                    "findings": [
                        {
                            "severity": "high",
                            "file": "src/auth.ts",
                            "summary": "auth-sensitive change exceeds current lane",
                        }
                    ],
                    "requiredActions": ["escalate to strict lane"],
                },
                ensure_ascii=False,
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(self.plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                await hooks['chat.message'](
                  {{ sessionID: 'leader-1', agent: 'reviewer', messageID: 'm2' }},
                  {{ parts: [{{ text: 'review this task' }}] }}
                );
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm3', partID: 'p3' }},
                  {{ text: {reviewer_output} }}
                );
                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'leader-1.json'), 'utf-8'));
                console.log(JSON.stringify(state.evidence.escalation));
                """,
                env=env,
            )
        escalation = json.loads(output)
        self.assertEqual(1, len(escalation))
        self.assertEqual("standard", escalation[0]["fromLane"])
        self.assertEqual("strict", escalation[0]["toLane"])

    def test_case_strict_reviewer_cannot_close_blocks_final(self):
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(self.evidence_gate_url)});
            const result = mod.evaluateCloseGate({{
              phase: 'closable',
              triage: {{ lane: 'strict', needsReviewer: true }},
              evidence: {{
                triage: [{{ status: 'passed', at: '2026-04-18T00:00:00.000Z' }}],
                review: [{{ status: 'failed', at: '2026-04-18T00:00:01.000Z' }}],
                verification: [{{ status: 'passed', at: '2026-04-18T00:00:02.000Z' }}],
                manual: [],
                escalation: [],
              }},
              editedFiles: ['src/auth.ts'],
              verification: {{ status: 'passed', commands: [{{ category: 'tests' }}] }},
              reviewer: {{ status: 'failed' }},
            }});
            console.log(JSON.stringify(result));
            """
        )
        result = json.loads(output)
        self.assertFalse(result["allowed"])
        self.assertIn("missing reviewer pass", result["missing"])


if __name__ == "__main__":
    unittest.main()
