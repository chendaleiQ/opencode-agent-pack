import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class OpenCodePluginRuntimeTests(unittest.TestCase):
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

    def test_runtime_files_exist(self):
        expected = [
            self.repo_root / ".opencode" / "plugins" / "runtime" / "paths.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "audit_store.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "hook_runtime.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "profiles.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "audit_stats.js",
        ]

        for path in expected:
            self.assertTrue(path.exists(), f"missing runtime file: {path}")

    def test_plugin_exports_runtime_hooks(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                console.log(JSON.stringify(Object.keys(hooks).sort()));
                """,
                env=env,
            )
        keys = json.loads(output)
        self.assertIn("config", keys)
        self.assertIn("tool.execute.before", keys)
        self.assertIn("tool.execute.after", keys)
        self.assertIn("experimental.chat.system.transform", keys)
        self.assertIn("experimental.text.complete", keys)

    def test_runtime_blocks_git_commit_no_verify(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
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
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'sess-1', messageID: 'm0', partID: 'p0' }},
                  {{ text: {triage_payload} }}
                );
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'bash', sessionID: 'sess-1', callID: 'call-1' }},
                    {{ args: {{ command: 'git commit -m "x" --no-verify' }} }}
                  );
                  console.log('not-blocked');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertIn("blocked git commit --no-verify", output)

    def test_runtime_blocks_protected_config_edit(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
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
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'sess-1', messageID: 'm0', partID: 'p0' }},
                  {{ text: {triage_payload} }}
                );
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'edit', sessionID: 'sess-1', callID: 'call-2' }},
                    {{ args: {{ filePath: 'eslint.config.js' }} }}
                  );
                  console.log('not-blocked');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertIn("blocked protected config edit", output)

    def test_runtime_blocks_bash_execution_before_triage(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'bash', sessionID: 'sess-1', callID: 'call-bash' }},
                    {{ args: {{ command: 'npm test' }} }}
                  );
                  console.log('not-blocked');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertIn("triage before execution", output)

    def test_runtime_allows_pre_triage_read_only_discovery_tools(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['chat.message'](
                  {{ sessionID: 'sess-1', agent: 'leader', messageID: 'm1' }},
                  {{ parts: [{{ text: 'What does git status do?' }}] }}
                );
                const results = [];
                for (const [tool, args] of [
                  ['glob', {{ pattern: '**/*.md', path: '.' }}],
                  ['grep', {{ pattern: 'status', path: '.' }}],
                  ['read', {{ filePath: 'README.md' }}],
                ]) {{
                  try {{
                    await hooks['tool.execute.before'](
                      {{ tool, sessionID: 'sess-1', callID: `call-${{tool}}` }},
                      {{ args }}
                    );
                    results.push(`${{tool}}:allowed`);
                  }} catch (error) {{
                    results.push(`${{tool}}:${{error.message}}`);
                  }}
                }}
                console.log(JSON.stringify(results));
                """,
                env=env,
            )
        self.assertEqual(
            ["glob:allowed", "grep:allowed", "read:allowed"],
            json.loads(output),
        )

    def test_runtime_allows_tool_execution_after_triage_is_recorded(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
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
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'sess-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {triage_payload} }}
                );
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'read', sessionID: 'sess-1', callID: 'call-read' }},
                    {{ args: {{ filePath: 'README.md' }} }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual("allowed", output)

    def test_runtime_allows_pre_triage_skill_loading_for_triage_path(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'skill', sessionID: 'sess-1', callID: 'call-skill' }},
                    {{ args: {{ name: 'dtt-change-triage' }} }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual("allowed", output)

    def test_runtime_blocks_todowrite_before_triage(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'todowrite', sessionID: 'sess-1', callID: 'call-todo' }},
                    {{ args: {{ todos: [] }} }}
                  );
                  console.log('not-blocked');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertIn("triage before execution", output)

    def test_runtime_blocks_command_execution_before_triage(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                try {{
                  await hooks['command.execute.before'](
                    {{ command: 'providers', sessionID: 'sess-1', arguments: '' }},
                    {{ parts: [] }}
                  );
                  console.log('not-blocked');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertIn("triage before execution", output)

    def test_runtime_allows_command_execution_after_triage(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
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
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'sess-1', messageID: 'm0', partID: 'p0' }},
                  {{ text: {triage_payload} }}
                );
                try {{
                  await hooks['command.execute.before'](
                    {{ command: 'providers', sessionID: 'sess-1', arguments: '' }},
                    {{ parts: [] }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual("allowed", output)

    def test_runtime_system_guard_reports_planning_gate_stage(self):
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
        self.assertIn("planning gate", output.lower())
        self.assertIn("spec", output.lower())

    def test_runtime_blocks_implementation_tools_until_plan_is_approved(self):
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
        self.assertIn("planning gate", result.stdout)
        self.assertIn("spec", result.stdout.lower())

    def test_runtime_chinese_approval_message_advances_planning_gate_state(self):
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
        self.assertNotEqual("undefined", result.stdout.strip())
        planning_gate = json.loads(result.stdout.strip())
        self.assertEqual("approved", planning_gate["specStatus"])
        self.assertEqual("plan", planning_gate["blockedStage"])

    def test_runtime_short_chinese_keyi_approval_advances_planning_gate_state(self):
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
        self.assertEqual("approved", planning_gate["specStatus"])
        self.assertEqual("plan", planning_gate["blockedStage"])
        self.assertEqual(1, len(planning_gate["approvals"]))

    def test_runtime_short_chinese_jixu_approval_advances_planning_gate_state(self):
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
        self.assertEqual("approved", planning_gate["specStatus"])
        self.assertEqual("plan", planning_gate["blockedStage"])
        self.assertEqual(1, len(planning_gate["approvals"]))

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
                await hooks['chat.message'](
                  {{ sessionID: 'leader-1', agent: 'leader', messageID: 'm2' }},
                  {{ parts: [{{ text: 'approved' }}] }}
                );
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
                await hooks['chat.message'](
                  {{ sessionID: 'leader-1', agent: 'leader', messageID: 'm3' }},
                  {{ parts: [{{ text: 'approved' }}] }}
                );
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

    def test_runtime_blocks_apply_patch_mixed_or_non_markdown_planning_paths(self):
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
        self.assertNotIn("allowed", result.stdout)
        self.assertEqual(2, result.stdout.lower().count("planning gate"))
        self.assertIn("spec", result.stdout.lower())

    def test_runtime_blocks_apply_patch_delete_planning_doc_during_planning_gate(
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
        self.assertNotIn("allowed", result.stdout)
        self.assertIn("planning gate", result.stdout.lower())
        self.assertIn("spec", result.stdout.lower())

    def test_runtime_blocks_plan_generation_skill_while_spec_stage_is_blocked(self):
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
        self.assertIn("planning gate", result.stdout.lower())
        self.assertIn("spec", result.stdout.lower())

    def test_runtime_blocks_plan_generation_task_while_spec_stage_is_blocked(self):
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
        self.assertIn("planning gate", result.stdout.lower())
        self.assertIn("spec", result.stdout.lower())

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

    def test_runtime_blocks_unrelated_skill_during_spec_stage(self):
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
        self.assertIn("planning gate", result.stdout)
        self.assertIn("spec", result.stdout.lower())

    def test_runtime_blocks_unrelated_skill_during_plan_stage(self):
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
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm2', partID: 'p2' }},
                  {{ text: JSON.stringify({{ planningArtifact: 'spec', summary: 'spec drafted' }}) }}
                );
                await hooks['chat.message'](
                  {{ sessionID: 'leader-1', agent: 'leader', messageID: 'm3' }},
                  {{ parts: [{{ text: '这个方案我批准，继续写计划。' }}] }}
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
        self.assertIn("planning gate", result.stdout)
        self.assertIn("plan", result.stdout.lower())

    def test_runtime_rewrites_plan_text_while_spec_stage_is_blocked(self):
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
        self.assertNotIn("## Plan", result.stdout)
        self.assertIn("spec", result.stdout.lower())
        self.assertIn("approval", result.stdout.lower())

    def test_runtime_rewrites_execution_text_while_spec_stage_is_blocked(self):
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
        self.assertNotIn("Now I will implement", result.stdout)
        self.assertIn("spec", result.stdout.lower())
        self.assertIn("approval", result.stdout.lower())

    def test_runtime_rewrites_execution_text_while_plan_stage_is_blocked(self):
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
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'leader-1', messageID: 'm2', partID: 'p2' }},
                  {{ text: JSON.stringify({{ planningArtifact: 'spec', summary: 'spec drafted' }}) }}
                );
                await hooks['chat.message'](
                  {{ sessionID: 'leader-1', agent: 'leader', messageID: 'm3' }},
                  {{ parts: [{{ text: 'approved' }}] }}
                );
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
        self.assertNotIn("Now I will implement", result.stdout)
        self.assertIn("plan", result.stdout.lower())
        self.assertIn("approval", result.stdout.lower())

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
                await hooks['chat.message'](
                  {{ sessionID: 'leader-1', agent: 'leader', messageID: 'm3' }},
                  {{ parts: [{{ text: 'approved' }}] }}
                );
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

    def test_runtime_rewrites_mixed_spec_and_plan_text_while_spec_stage_is_blocked(
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
        self.assertNotIn("## Plan", result.stdout)
        self.assertIn("spec", result.stdout.lower())
        self.assertIn("approval", result.stdout.lower())

    def test_runtime_rewrites_mixed_plan_and_execution_text_while_plan_stage_is_blocked(
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
                await hooks['chat.message'](
                  {{ sessionID: 'leader-1', agent: 'leader', messageID: 'm3' }},
                  {{ parts: [{{ text: 'approved' }}] }}
                );
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
        self.assertNotIn("Now I will implement", result.stdout)
        self.assertIn("plan", result.stdout.lower())
        self.assertIn("approval", result.stdout.lower())

    def test_runtime_rewrites_blocked_completion_attempt(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        payload_text = json.dumps(
            "standard | high | low | reviewerPassed | closeReason\nchangeSummary: test"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['tool.execute.after'](
                  {{ tool: 'edit', sessionID: 'sess-1', callID: 'call-3', args: {{ filePath: 'src/a.ts' }} }},
                  {{ title: 'edit', output: '', metadata: {{}} }}
                );
                const payload = {{ text: {payload_text} }};
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'sess-1', messageID: 'm1', partID: 'p1' }},
                  payload
                );
                console.log(payload.text);
                """,
                env=env,
            )
        self.assertIn("Completion blocked by do-the-thing runtime.", output)

    def test_runtime_non_leader_tool_bypasses_triage_gate(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['chat.message'](
                  {{ sessionID: 'build-1', agent: 'plan', messageID: 'm1' }},
                  {{ parts: [{{ text: 'make a plan' }}] }}
                );
                try {{
                  await hooks['tool.execute.before'](
                    {{ tool: 'bash', sessionID: 'build-1', callID: 'call-build' }},
                    {{ args: {{ command: 'npm run build' }} }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual("allowed", output)

    def test_runtime_non_leader_command_bypasses_triage_gate(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['chat.message'](
                  {{ sessionID: 'plan-1', agent: 'plan', messageID: 'm1' }},
                  {{ parts: [{{ text: 'make a plan' }}] }}
                );
                try {{
                  await hooks['command.execute.before'](
                    {{ command: 'providers', sessionID: 'plan-1', arguments: '' }},
                    {{ parts: [] }}
                  );
                  console.log('allowed');
                }} catch (error) {{
                  console.log(error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual("allowed", output)

    def test_runtime_non_leader_completion_is_not_rewritten(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        payload_text = json.dumps(
            "standard | high | low | reviewerPassed | closeReason\nchangeSummary: test"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['chat.message'](
                  {{ sessionID: 'custom-1', agent: 'custom-agent', messageID: 'm1' }},
                  {{ parts: [{{ text: 'do something else' }}] }}
                );
                const payload = {{ text: {payload_text} }};
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'custom-1', messageID: 'm2', partID: 'p2' }},
                  payload
                );
                console.log(payload.text);
                """,
                env=env,
            )
        self.assertNotIn("Completion blocked by do-the-thing runtime.", output)

    def test_runtime_non_leader_system_guard_is_not_injected(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['chat.message'](
                  {{ sessionID: 'custom-1', agent: 'custom-agent', messageID: 'm1' }},
                  {{ parts: [{{ text: 'do something else' }}] }}
                );
                const output = {{ system: [] }};
                await hooks['experimental.chat.system.transform'](
                  {{ sessionID: 'custom-1' }},
                  output
                );
                console.log(JSON.stringify(output.system));
                """,
                env=env,
            )
        self.assertEqual("[]", output)

    def test_runtime_records_debug_entry_type_from_message(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});
                await hooks['chat.message'](
                  {{ sessionID: 'sess-1', agent: 'leader', messageID: 'm1' }},
                  {{ parts: [{{ text: 'please debug why tests are failing' }}] }}
                );
                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'sess-1.json'), 'utf-8'));
                console.log(JSON.stringify({{ entryType: state.entryType, phase: state.phase }}));
                """,
                env=env,
            )
        state = json.loads(output)
        self.assertEqual("debug", state["entryType"])

    def test_runtime_ignores_non_json_reviewer_output(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        reviewer_output = json.dumps(
            """Findings\n无发现\n\nScope/Risk judgement\n范围保持在启动验证内，风险仍为低。\n\nVerification gaps\n无\n\nReviewer pass/fail\npass\n\n是否建议升级以及理由\n不建议升级。"""
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                import fs from 'fs';
                import path from 'path';
                const mod = await import({json.dumps(plugin_url)});
                const hooks = await mod.DoTheThingPlugin({{
                  project: {{ id: 'proj-1' }},
                  directory: {json.dumps(str(self.repo_root))},
                  worktree: {json.dumps(str(self.repo_root))},
                }});

                await hooks['chat.message'](
                  {{ sessionID: 'review-1', agent: 'reviewer', messageID: 'm0' }},
                  {{ parts: [{{ text: 'review this task' }}] }}
                );
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'review-1', messageID: 'm1', partID: 'p1' }},
                  {{ text: {reviewer_output} }}
                );

                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'review-1.json'), 'utf-8'));
                console.log(JSON.stringify({{
                  reviewerStatus: state.reviewer.status,
                  reviewEvidence: state.evidence.review,
                }}));
                """,
                env=env,
            )
        state = json.loads(output)
        self.assertEqual("missing", state["reviewerStatus"])
        self.assertEqual([], state["reviewEvidence"])

    def test_runtime_merges_reviewer_task_state_back_into_leader_session(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
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
                    "verdict": "pass",
                    "reviewTierUsed": "tier_mid",
                    "specCompliance": "pass",
                    "codeQuality": "pass",
                    "mustEscalate": False,
                    "recommendedLane": "standard",
                    "recommendedTierUpgrade": {
                        "needed": False,
                        "from": "tier_mid",
                        "to": "tier_mid",
                        "reason": "",
                    },
                    "scopeDrift": False,
                    "unresolvedRisk": False,
                    "sensitiveHit": {
                        "touchesAuth": False,
                        "touchesDbSchema": False,
                        "touchesPublicApi": False,
                        "touchesDestructiveAction": False,
                    },
                    "verifyStatus": "passed",
                    "endGateCheck": {
                        "quickReady": False,
                        "standardReady": True,
                        "guardedReady": False,
                        "strictReady": False,
                    },
                    "findings": [],
                    "requiredActions": [],
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

                await hooks['chat.message'](
                  {{ sessionID: 'review-1', agent: 'reviewer', messageID: 'm2' }},
                  {{ parts: [{{ text: 'review this task' }}] }}
                );
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'review-1', messageID: 'm3', partID: 'p3' }},
                  {{ text: {reviewer_output} }}
                );

                await hooks['tool.execute.after'](
                  {{
                    tool: 'task',
                    sessionID: 'leader-1',
                    callID: 'call-review',
                    args: {{ subagent_type: 'reviewer', description: '审查启动任务' }},
                  }},
                  {{
                    title: '审查启动任务',
                    metadata: {{ sessionID: 'review-1' }},
                    output: 'done',
                  }}
                );

                const file = path.join({json.dumps(tmpdir)}, 'do-the-thing', 'sessions');
                const projectDir = fs.readdirSync(file)[0];
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'leader-1.json'), 'utf-8'));
                console.log(JSON.stringify({{
                  reviewerStatus: state.reviewer.status,
                  reviewEvidence: state.evidence.review,
                  phase: state.phase,
                }}));
                """,
                env=env,
            )
        state = json.loads(output)
        self.assertEqual("passed", state["reviewerStatus"])
        self.assertEqual(1, len(state["reviewEvidence"]))
        self.assertEqual("reviewing", state["phase"])

    def test_runtime_records_escalation_evidence_from_reviewer_upgrade_signal(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
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
        self.assertIn("reviewer", escalation[0]["reason"])


if __name__ == "__main__":
    unittest.main()
