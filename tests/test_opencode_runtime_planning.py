import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.runtime_test_case import OpenCodeRuntimeTestCase


class OpenCodeRuntimePlanningTests(OpenCodeRuntimeTestCase):
    def test_runtime_system_guard_reports_planning_state_as_guidance(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                const output = {{ system: [] }};
                await hooks['experimental.chat.system.transform'](
                  {{ sessionID: 'leader-1' }},
                  output
                );
                console.log(JSON.stringify(output.system));
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = "\n".join(json.loads(result.stdout.strip()))
        self.assertIn("planning state pending", output.lower())
        self.assertIn("guidance only", output.lower())
        self.assertIn("spec", output.lower())
    def test_runtime_allows_implementation_tools_during_planning_gate(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'edit', sessionID: 'leader-1', callID: 'call-edit' }},
                    {{ args: {{ filePath: 'src/app.ts' }} }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("allowed", result.stdout)
        self.assertNotIn("planning gate", result.stdout.lower())
    def test_runtime_chinese_approval_message_does_not_advance_planning_gate_state(
        self,
    ):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
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
                  {{ parts: [{{ text: '这个方案我批准，继续写计划。' }}] }}
                );
                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'leader-1.json'), 'utf-8'));
                console.log(JSON.stringify(state.planningGate));
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        planning_gate = json.loads(result.stdout.strip())
        self.assertEqual("drafted", planning_gate["specStatus"])
        self.assertEqual("spec", planning_gate["blockedStage"])
        self.assertEqual([], planning_gate["approvals"])
    def test_runtime_short_chinese_keyi_approval_does_not_advance_planning_gate_state(
        self,
    ):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
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
                  {{ parts: [{{ text: '可以' }}] }}
                );
                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'leader-1.json'), 'utf-8'));
                console.log(JSON.stringify(state.planningGate));
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        planning_gate = json.loads(result.stdout.strip())
        self.assertEqual("drafted", planning_gate["specStatus"])
        self.assertEqual("spec", planning_gate["blockedStage"])
        self.assertEqual([], planning_gate["approvals"])
    def test_runtime_short_chinese_jixu_approval_does_not_advance_planning_gate_state(
        self,
    ):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
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
                  {{ parts: [{{ text: '继续' }}] }}
                );
                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'leader-1.json'), 'utf-8'));
                console.log(JSON.stringify(state.planningGate));
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        planning_gate = json.loads(result.stdout.strip())
        self.assertEqual("drafted", planning_gate["specStatus"])
        self.assertEqual("spec", planning_gate["blockedStage"])
        self.assertEqual([], planning_gate["approvals"])
    def test_runtime_question_approval_advances_spec_planning_gate(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        question_args = json.dumps(
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
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
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
                await hooks['tool.execute.before'](
                  {{ tool: 'question', sessionID: 'leader-1', callID: 'call-question' }},
                  {{ args: {question_args} }}
                );
                await hooks.event({{
                  event: {{
                    type: 'question.asked',
                    properties: {{ id: 'q-spec-1', sessionID: 'leader-1', ...{question_args} }},
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
        self.assertEqual(result.returncode, 0, result.stderr)
        planning_gate = json.loads(result.stdout.strip())
        self.assertEqual("approved", planning_gate["specStatus"])
        self.assertEqual("plan", planning_gate["blockedStage"])
        self.assertEqual(1, len(planning_gate["approvals"]))
        self.assertEqual(1, len(planning_gate["decisions"]))
        self.assertEqual("approved", planning_gate["decisions"][0]["decision"])
    def test_runtime_question_feedback_keeps_spec_gate_blocked(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        question_args = json.dumps(
            {
                "questions": [
                    {
                        "header": "Spec 审批",
                        "multiple": False,
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
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
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
                await hooks['tool.execute.before'](
                  {{ tool: 'question', sessionID: 'leader-1', callID: 'call-question' }},
                  {{ args: {question_args} }}
                );
                await hooks.event({{
                  event: {{
                    type: 'question.asked',
                    properties: {{ id: 'q-spec-1', sessionID: 'leader-1', ...{question_args} }},
                  }},
                }});
                await hooks.event({{
                  event: {{
                    type: 'question.replied',
                    properties: {{
                      sessionID: 'leader-1',
                      requestID: 'q-spec-1',
                      answers: [['需要补充 spec']],
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
        self.assertEqual(result.returncode, 0, result.stderr)
        planning_gate = json.loads(result.stdout.strip())
        self.assertEqual("changes_requested", planning_gate["specStatus"])
        self.assertEqual("spec", planning_gate["blockedStage"])
        self.assertEqual([], planning_gate["approvals"])
        self.assertEqual("changes_requested", planning_gate["decisions"][0]["decision"])
    def test_runtime_question_approval_advances_plan_planning_gate(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        spec_question_args = self._spec_approval_question_args()
        question_args = self._plan_approval_question_args()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
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
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm4', partID: 'p4' }},
                  {{ text: JSON.stringify({{ planningArtifact: 'plan', summary: 'plan drafted' }}) }}
                );
                await hooks['tool.execute.before'](
                  {{ tool: 'question', sessionID: 'leader-1', callID: 'call-question' }},
                  {{ args: {question_args} }}
                );
                await hooks.event({{
                  event: {{
                    type: 'question.asked',
                    properties: {{ id: 'q-plan-1', sessionID: 'leader-1', ...{question_args} }},
                  }},
                }});
                await hooks.event({{
                  event: {{
                    type: 'question.replied',
                    properties: {{
                      sessionID: 'leader-1',
                      requestID: 'q-plan-1',
                      answers: [['批准 plan，开始实现']],
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
        self.assertEqual(result.returncode, 0, result.stderr)
        planning_gate = json.loads(result.stdout.strip())
        self.assertIsNone(planning_gate["blockedStage"])
        self.assertEqual("approved", planning_gate["specStatus"])
        self.assertEqual("approved", planning_gate["planStatus"])
        self.assertEqual(2, len(planning_gate["approvals"]))
        self.assertEqual(2, len(planning_gate["decisions"]))
        self.assertEqual("approved", planning_gate["decisions"][0]["decision"])
        self.assertEqual("approved", planning_gate["decisions"][1]["decision"])
    def test_runtime_question_rejection_keeps_spec_gate_blocked(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        question_args = json.dumps(
            {
                "questions": [
                    {
                        "header": "Spec 审批",
                        "multiple": False,
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
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
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
                await hooks['tool.execute.before'](
                  {{ tool: 'question', sessionID: 'leader-1', callID: 'call-question' }},
                  {{ args: {question_args} }}
                );
                await hooks.event({{
                  event: {{
                    type: 'question.asked',
                    properties: {{ id: 'q-spec-1', sessionID: 'leader-1', ...{question_args} }},
                  }},
                }});
                await hooks.event({{
                  event: {{
                    type: 'question.rejected',
                    properties: {{ sessionID: 'leader-1', requestID: 'q-spec-1' }},
                  }},
                }});
                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'leader-1.json'), 'utf-8'));
                console.log(JSON.stringify(state.planningGate));
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        planning_gate = json.loads(result.stdout.strip())
        self.assertEqual("rejected", planning_gate["specStatus"])
        self.assertEqual("spec", planning_gate["blockedStage"])
        self.assertEqual("rejected", planning_gate["decisions"][0]["decision"])
    def test_runtime_allows_unrelated_question_during_planning_gate(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        question_args = json.dumps(
            {
                "questions": [
                    {
                        "header": "系统依赖",
                        "multiple": False,
                        "options": [
                            {"label": "安装依赖", "description": "继续安装系统依赖。"},
                            {"label": "先停一下", "description": "暂时不安装。"},
                        ],
                        "question": "是否安装 Homebrew 依赖？",
                    }
                ]
            },
            ensure_ascii=False,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'question', sessionID: 'leader-1', callID: 'call-question' }},
                    {{ args: {question_args} }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("allowed", result.stdout)
        self.assertNotIn("planning gate", result.stdout.lower())
    def test_runtime_allows_planning_doc_write_before_plan_approval(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'write', sessionID: 'leader-1', callID: 'call-write' }},
                    {{ args: {{ filePath: 'docs/dtt/specs/example-spec.md' }} }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("allowed", result.stdout)
    def test_runtime_allows_apply_patch_for_spec_and_plan_docs_only(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        spec_question_args = self._spec_approval_question_args()
        plan_question_args = self._plan_approval_question_args()
        spec_patch = json.dumps(
            "\n".join(
                [
                    "*** Begin Patch",
                    "*** Add File: docs/dtt/specs/example-spec.md",
                    "+# Spec",
                    "*** End Patch",
                ]
            )
        )
        plan_patch = json.dumps(
            "\n".join(
                [
                    "*** Begin Patch",
                    "*** Add File: docs/dtt/plans/example-plan.md",
                    "+# Plan",
                    "*** End Patch",
                ]
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                await hooks['tool.execute.before'](
                  {{ tool: 'apply_patch', sessionID: 'leader-1', callID: 'call-spec' }},
                  {{ args: {{ patchText: {spec_patch} }} }}
                );
                await hooks['tool.execute.after'](
                  {{
                    tool: 'apply_patch',
                    sessionID: 'leader-1',
                    callID: 'call-spec',
                    args: {{ patchText: {spec_patch} }},
                  }},
                  {{ title: 'write spec', output: '', metadata: {{}} }}
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
                await hooks['tool.execute.before'](
                  {{ tool: 'apply_patch', sessionID: 'leader-1', callID: 'call-plan' }},
                  {{ args: {{ patchText: {plan_patch} }} }}
                );
                await hooks['tool.execute.after'](
                  {{
                    tool: 'apply_patch',
                    sessionID: 'leader-1',
                    callID: 'call-plan',
                    args: {{ patchText: {plan_patch} }},
                  }},
                  {{ title: 'write plan', output: '', metadata: {{}} }}
                );
                await hooks['tool.execute.before'](
                  {{ tool: 'question', sessionID: 'leader-1', callID: 'call-plan-question' }},
                  {{ args: {plan_question_args} }}
                );
                await hooks.event({{
                  event: {{
                    type: 'question.asked',
                    properties: {{ id: 'q-plan-1', sessionID: 'leader-1', ...{plan_question_args} }},
                  }},
                }});
                await hooks.event({{
                  event: {{
                    type: 'question.replied',
                    properties: {{
                      sessionID: 'leader-1',
                      requestID: 'q-plan-1',
                      answers: [['批准 plan，开始实现']],
                    }},
                  }},
                }});
                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'leader-1.json'), 'utf-8'));
                console.log(JSON.stringify({{
                  blockedStage: state.planningGate.blockedStage,
                  specStatus: state.planningGate.specStatus,
                  planStatus: state.planningGate.planStatus,
                  specArtifacts: state.planningGate.specArtifacts,
                  planArtifacts: state.planningGate.planArtifacts,
                  editedFiles: state.editedFiles,
                }}));
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(result.stdout.strip())
        self.assertIsNone(state["blockedStage"])
        self.assertEqual("approved", state["specStatus"])
        self.assertEqual("approved", state["planStatus"])
        self.assertEqual(1, len(state["specArtifacts"]))
        self.assertEqual(1, len(state["planArtifacts"]))
        self.assertEqual([], state["editedFiles"])
    def test_runtime_allows_apply_patch_mixed_or_non_markdown_planning_paths(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        mixed_patch = json.dumps(
            "\n".join(
                [
                    "*** Begin Patch",
                    "*** Add File: docs/dtt/specs/example-spec.md",
                    "+# Spec",
                    "*** Add File: src/implementation.js",
                    "+export const changed = true;",
                    "*** End Patch",
                ]
            )
        )
        non_markdown_patch = json.dumps(
            "\n".join(
                [
                    "*** Begin Patch",
                    "*** Add File: docs/dtt/specs/example-spec.txt",
                    "+not markdown",
                    "*** End Patch",
                ]
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                for (const patchText of [{mixed_patch}, {non_markdown_patch}]) {{
                  try {{
                    await hooks['tool.execute.before'](
                      {{ tool: 'apply_patch', sessionID: 'leader-1', callID: 'call-patch' }},
                      {{ args: {{ patchText }} }}
                    );
                    console.log('allowed');
                  }} catch (error) {{
                    console.log(error.message);
                  }}
                }}
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(2, result.stdout.count("allowed"))
        self.assertNotIn("planning gate", result.stdout.lower())
    def test_runtime_allows_apply_patch_delete_planning_doc_during_planning_gate(
        self,
    ):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        delete_patch = json.dumps(
            "\n".join(
                [
                    "*** Begin Patch",
                    "*** Delete File: docs/dtt/specs/example-spec.md",
                    "*** End Patch",
                ]
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'apply_patch', sessionID: 'leader-1', callID: 'call-patch' }},
                    {{ args: {{ patchText: {delete_patch} }} }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("allowed", result.stdout)
        self.assertNotIn("planning gate", result.stdout.lower())
    def test_runtime_allows_plan_generation_skill_while_spec_stage_is_blocked(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'skill', sessionID: 'leader-1', callID: 'call-skill' }},
                    {{ args: {{ name: 'dtt-writing-plans' }} }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("allowed", result.stdout)
        self.assertNotIn("planning gate", result.stdout.lower())
    def test_runtime_allows_plan_generation_task_while_spec_stage_is_blocked(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'task', sessionID: 'leader-1', callID: 'call-task' }},
                    {{ args: {{ subagent_type: 'plan', description: 'Generate implementation plan' }} }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("allowed", result.stdout)
        self.assertNotIn("planning gate", result.stdout.lower())
    def test_runtime_planning_doc_write_does_not_count_as_implementation_edit(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                await hooks['tool.execute.after'](
                  {{
                    tool: 'write',
                    sessionID: 'leader-1',
                    callID: 'call-write',
                    args: {{ filePath: 'docs/dtt/specs/example-spec.md' }},
                  }},
                  {{ title: 'write spec', output: '', metadata: {{}} }}
                );
                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'leader-1.json'), 'utf-8'));
                console.log(JSON.stringify({{
                  editedFiles: state.editedFiles,
                  blockedStage: state.planningGate.blockedStage,
                  specStatus: state.planningGate.specStatus,
                  specArtifacts: state.planningGate.specArtifacts,
                }}));
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(result.stdout.strip())
        self.assertEqual([], state["editedFiles"])
        self.assertEqual("spec", state["blockedStage"])
        self.assertEqual("drafted", state["specStatus"])
        self.assertEqual(1, len(state["specArtifacts"]))
    def test_runtime_negative_chinese_approval_message_does_not_advance_planning_gate_state(
        self,
    ):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
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
                  {{ parts: [{{ text: '这个方案如果评审通过我再批准，现在还不能通过。' }}] }}
                );
                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'leader-1.json'), 'utf-8'));
                console.log(JSON.stringify(state.planningGate));
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        planning_gate = json.loads(result.stdout.strip())
        self.assertEqual("drafted", planning_gate["specStatus"])
        self.assertEqual("spec", planning_gate["blockedStage"])
    def test_runtime_english_conditional_approval_message_does_not_advance_planning_gate_state(
        self,
    ):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
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
                  {{ parts: [{{ text: 'Approve once the tests pass.' }}] }}
                );
                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'leader-1.json'), 'utf-8'));
                console.log(JSON.stringify(state.planningGate));
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        planning_gate = json.loads(result.stdout.strip())
        self.assertEqual("drafted", planning_gate["specStatus"])
        self.assertEqual("spec", planning_gate["blockedStage"])
    def test_runtime_allows_unrelated_skill_during_spec_stage(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'skill', sessionID: 'leader-1', callID: 'call-skill' }},
                    {{ args: {{ name: 'dtt-systematic-debugging' }} }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("allowed", result.stdout)
        self.assertNotIn("planning gate", result.stdout.lower())
    def test_runtime_allows_unrelated_skill_during_plan_stage(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        spec_question_args = self._spec_approval_question_args()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
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
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'skill', sessionID: 'leader-1', callID: 'call-skill' }},
                    {{ args: {{ name: 'dtt-systematic-debugging' }} }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("allowed", result.stdout)
        self.assertNotIn("planning gate", result.stdout.lower())
    def test_runtime_keeps_plan_text_while_spec_stage_is_blocked(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        blocked_text = "## Plan\n1. Implement the runtime change"
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                const output = {{ text: {json.dumps(blocked_text)} }};
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm2', partID: 'p2' }},
                  output
                );
                console.log(output.text);
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(blocked_text, result.stdout.strip())
    def test_runtime_keeps_execution_text_while_spec_stage_is_blocked(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                const output = {{ text: 'Now I will implement the fix and run review.' }};
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm2', partID: 'p2' }},
                  output
                );
                console.log(output.text);
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            "Now I will implement the fix and run review.", result.stdout.strip()
        )
    def test_runtime_keeps_execution_text_while_plan_stage_is_blocked(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        spec_question_args = self._spec_approval_question_args()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
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
                const output = {{ text: 'Now I will implement the fix.' }};
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm4', partID: 'p4' }},
                  output
                );
                console.log(output.text);
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual("Now I will implement the fix.", result.stdout.strip())
    def test_runtime_keeps_spec_text_while_spec_stage_is_blocked(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        allowed_text = (
            "# Spec\nDetails\nPlease approve this spec before I write the plan."
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                const output = {{ text: {json.dumps(allowed_text)} }};
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm2', partID: 'p2' }},
                  output
                );
                console.log(output.text);
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(allowed_text, result.stdout.strip())
    def test_runtime_keeps_plan_text_while_plan_stage_is_blocked(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        spec_question_args = self._spec_approval_question_args()
        allowed_text = (
            "# Plan\n1. Add a guard\nPlease approve this plan before execution."
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
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
                const output = {{ text: {json.dumps(allowed_text)} }};
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm4', partID: 'p4' }},
                  output
                );
                console.log(output.text);
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(allowed_text, result.stdout.strip())
    def test_runtime_keeps_mixed_spec_and_plan_text_while_spec_stage_is_blocked(
        self,
    ):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        mixed_text = (
            "# Spec\nDetails\nPlease approve this spec before I write the plan.\n\n"
            "## Plan\n1. Implement the runtime change"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                const output = {{ text: {json.dumps(mixed_text)} }};
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm2', partID: 'p2' }},
                  output
                );
                console.log(output.text);
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(mixed_text, result.stdout.strip())
    def test_runtime_keeps_mixed_plan_and_execution_text_while_plan_stage_is_blocked(
        self,
    ):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        triage_payload = json.dumps(
            json.dumps(
                {
                    "lane": "standard",
                    "complexity": "high",
                    "risk": "low",
                    "needsPlan": True,
                    "needsReviewer": False,
                    "finalApprovalTier": "tier_top",
                },
                ensure_ascii=False,
            )
        )
        spec_question_args = self._spec_approval_question_args()
        mixed_text = (
            "# Plan\n1. Add a guard\nPlease approve this plan before execution.\n\n"
            "Now I will implement the fix and close this out."
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            result = self._run_node_result(
                f"""
                const mod = await import({json.dumps(plugin_url)});
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
                const output = {{ text: {json.dumps(mixed_text)} }};
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm4', partID: 'p4' }},
                  output
                );
                console.log(output.text);
                """,
                env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(mixed_text, result.stdout.strip())


if __name__ == "__main__":
    unittest.main()
