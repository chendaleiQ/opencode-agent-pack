import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class RuntimeProfileTests(unittest.TestCase):
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

    def test_profiles_module_exists(self):
        path = self.repo_root / ".opencode" / "plugins" / "runtime" / "profiles.js"
        self.assertTrue(path.exists(), "missing profiles.js runtime module")

    def test_profile_definitions_cover_three_levels(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "profiles.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            console.log(JSON.stringify(Object.keys(mod.PROFILES).sort()));
            """
        )
        profiles = json.loads(output)
        self.assertEqual(["minimal", "standard", "strict"], profiles)

    def test_minimal_profile_disables_blocking_features(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "profiles.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            console.log(JSON.stringify(mod.getProfileFeatures('minimal')));
            """
        )
        features = json.loads(output)
        self.assertTrue(features["auditLogging"])
        self.assertTrue(features["toolCallTracking"])
        self.assertFalse(features["protectedConfigBlock"])
        self.assertFalse(features["noVerifyBlock"])
        self.assertFalse(features["closeGate"])
        self.assertFalse(features["completionRewrite"])

    def test_standard_profile_enables_blocking_but_not_all_evidence(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "profiles.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            console.log(JSON.stringify(mod.getProfileFeatures('standard')));
            """
        )
        features = json.loads(output)
        self.assertTrue(features["protectedConfigBlock"])
        self.assertTrue(features["noVerifyBlock"])
        self.assertTrue(features["closeGate"])
        self.assertTrue(features["completionRewrite"])
        self.assertTrue(features["evidenceStaleness"])
        self.assertFalse(features["requireAllEvidence"])

    def test_strict_profile_requires_all_evidence(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "profiles.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            console.log(JSON.stringify(mod.getProfileFeatures('strict')));
            """
        )
        features = json.loads(output)
        self.assertTrue(features["requireAllEvidence"])
        self.assertTrue(features["evidenceStaleness"])
        self.assertTrue(features["closeGate"])

    def test_profile_from_lane_maps_correctly(self):
        module_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "profiles.js"
        ).as_uri()
        output = self._run_node(
            f"""
            const mod = await import({json.dumps(module_url)});
            console.log(JSON.stringify({{
                quick: mod.profileFromLane('quick'),
                standard: mod.profileFromLane('standard'),
                guarded: mod.profileFromLane('guarded'),
                strict: mod.profileFromLane('strict'),
                unknown: mod.profileFromLane('something'),
            }}));
            """
        )
        mapping = json.loads(output)
        self.assertEqual("minimal", mapping["quick"])
        self.assertEqual("standard", mapping["standard"])
        self.assertEqual("strict", mapping["guarded"])
        self.assertEqual("strict", mapping["strict"])
        self.assertEqual("standard", mapping["unknown"])

    def test_triage_auto_sets_profile_in_state(self):
        state_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = self._run_node(
                f"""
                const mod = await import({json.dumps(state_url)});
                const context = {{ configDir: {json.dumps(tmpdir)}, projectKey: 'proj-a', sessionID: 'sess-1' }};
                mod.recordTriage(context, {{ lane: 'guarded', complexity: 'low', risk: 'high', needsReviewer: true, finalApprovalTier: 'tier_top' }});
                const state = mod.loadState(context);
                console.log(JSON.stringify({{ profile: state.profile }}));
                """
            )
        result = json.loads(output)
        self.assertEqual("strict", result["profile"])

    def test_minimal_profile_does_not_block_no_verify(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        state_url = (
            self.repo_root / ".opencode" / "plugins" / "runtime" / "state_store.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const plugin = await import({json.dumps(plugin_url)});
                const stateMod = await import({json.dumps(state_url)});
                const hooks = await plugin.DoTheThingPlugin({{
                    project: {{ id: 'proj-1' }},
                    directory: {json.dumps(str(self.repo_root))},
                    worktree: {json.dumps(str(self.repo_root))},
                }});
                // First set profile to minimal via triage with lane=quick
                await hooks['experimental.text.complete'](
                    {{ sessionID: 'sess-1', messageID: 'm1', partID: 'p1' }},
                    {{ text: '{{"lane":"quick","complexity":"low","risk":"low","needsReviewer":false,"finalApprovalTier":"tier_top"}}' }}
                );
                // Now try no-verify — should NOT be blocked under minimal profile
                try {{
                    await hooks['tool.execute.before'](
                        {{ tool: 'bash', sessionID: 'sess-1', callID: 'call-1' }},
                        {{ args: {{ command: 'git commit -m "x" --no-verify' }} }}
                    );
                    console.log('not-blocked');
                }} catch (error) {{
                    console.log('blocked: ' + error.message);
                }}
                """,
                env=env,
            )
        self.assertEqual("not-blocked", output)

    def test_minimal_profile_does_not_rewrite_completion(self):
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["OPENCODE_CONFIG_DIR"] = tmpdir
            output = self._run_node(
                f"""
                const plugin = await import({json.dumps(plugin_url)});
                const hooks = await plugin.DoTheThingPlugin({{
                    project: {{ id: 'proj-1' }},
                    directory: {json.dumps(str(self.repo_root))},
                    worktree: {json.dumps(str(self.repo_root))},
                }});
                // Set profile to minimal via quick triage
                await hooks['experimental.text.complete'](
                    {{ sessionID: 'sess-1', messageID: 'm1', partID: 'p1' }},
                    {{ text: '{{"lane":"quick","complexity":"low","risk":"low","needsReviewer":false,"finalApprovalTier":"tier_top"}}' }}
                );
                // Edit a file
                await hooks['tool.execute.after'](
                    {{ tool: 'edit', sessionID: 'sess-1', callID: 'call-2', args: {{ filePath: 'src/a.ts' }} }},
                    {{ title: 'edit', output: '', metadata: {{}} }}
                );
                // Attempt completion — minimal should NOT rewrite
                const payload = {{ text: 'quick | low | low | closeReason\\nchangeSummary: test' }};
                await hooks['experimental.text.complete'](
                    {{ sessionID: 'sess-1', messageID: 'm2', partID: 'p2' }},
                    payload
                );
                console.log(payload.text.startsWith('Completion blocked') ? 'blocked' : 'not-blocked');
                """,
                env=env,
            )
        self.assertEqual("not-blocked", output)


if __name__ == "__main__":
    unittest.main()
