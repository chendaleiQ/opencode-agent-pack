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

    def test_runtime_files_exist(self):
        expected = [
            self.repo_root / ".opencode" / "plugins" / "runtime" / "paths.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "audit_store.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "evidence_gate.js",
            self.repo_root / ".opencode" / "plugins" / "runtime" / "hook_runtime.js",
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

    def test_runtime_rewrites_blocked_completion_attempt(self):
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
                await hooks['tool.execute.after'](
                  {{ tool: 'edit', sessionID: 'sess-1', callID: 'call-3', args: {{ filePath: 'src/a.ts' }} }},
                  {{ title: 'edit', output: '', metadata: {{}} }}
                );
                const payload = {{ text: {json.dumps("standard | high | low | reviewerPassed | closeReason\nchangeSummary: test")} }};
                await hooks['experimental.text.complete'](
                  {{ sessionID: 'sess-1', messageID: 'm1', partID: 'p1' }},
                  payload
                );
                console.log(payload.text);
                """,
                env=env,
            )
        self.assertIn("Completion blocked by do-the-thing runtime.", output)

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


if __name__ == "__main__":
    unittest.main()
