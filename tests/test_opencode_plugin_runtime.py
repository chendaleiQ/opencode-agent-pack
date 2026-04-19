import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.runtime_test_case import OpenCodeRuntimeTestCase


class OpenCodePluginRuntimeTests(OpenCodeRuntimeTestCase):
    def test_runtime_files_exist(self):
        expected = [
            self.repo_root / ".opencode" / "plugins" / "runtime" / "paths.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js",
            self.repo_root
            / ".opencode"
            / "plugins"
            / "runtime"
            / "state_store_planning.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "audit_store.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "hook_runtime.js",
            self.repo_root
            / ".opencode"
            / "plugins"
            / "runtime"
            / "hook_runtime_helpers.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "profiles.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "audit_stats.js",
            self.repo_root
            / ".opencode"
            / "plugins"
            / "runtime"
            / "workflow_contract.js",
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
    def test_runtime_records_failed_verification_from_bash_tool_result(self):
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
                import fs from 'fs';
                import path from 'path';
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
                await hooks['tool.execute.before'](
                  {{ tool: 'bash', sessionID: 'sess-1', callID: 'call-bash' }},
                  {{ args: {{ command: 'npm test' }} }}
                );
                await hooks['tool.execute.after'](
                  {{
                    tool: 'bash',
                    sessionID: 'sess-1',
                    callID: 'call-bash',
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
                const state = JSON.parse(fs.readFileSync(path.join(file, projectDir, 'sess-1.json'), 'utf-8'));
                console.log(JSON.stringify({{
                  verification: state.verification,
                  evidence: state.evidence.verification,
                }}));
                """,
                env=env,
            )
        payload = json.loads(output)
        self.assertEqual("failed", payload["verification"]["status"])
        self.assertIsNone(payload["verification"]["pendingCommand"])
        self.assertEqual("failed", payload["verification"]["commands"][0]["status"])
        self.assertEqual("tests", payload["verification"]["commands"][0]["category"])
        self.assertEqual("failed", payload["evidence"][0]["status"])
        self.assertEqual("tests", payload["evidence"][0]["category"])
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
