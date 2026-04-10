# Leader Default Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or `dtt-executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `leader` the default installed agent while hiding the pack's helper agents from normal user discovery.

**Architecture:** Reuse the install-time JSON merge pattern already used for provider allowlists by adding a shared Python helper for `opencode.json`. Keep the behavioral prompts intact and only add OpenCode agent metadata where needed so `analyzer`, `implementer`, and `reviewer` become hidden subagents while `leader` remains user-facing.

**Tech Stack:** Bash, PowerShell, Python 3, Markdown agent files, Python `unittest`

---

### Task 1: Add shared `opencode.json` merge helper

**Files:**
- Create: `pack/tools/opencode_config.py`
- Test: `tests/test_opencode_config.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class OpenCodeConfigTests(unittest.TestCase):
    def test_set_default_agent_preserves_existing_fields(self):
        repo_root = Path(__file__).resolve().parents[1]
        script = repo_root / "pack" / "tools" / "opencode_config.py"

        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "opencode.json"
            config_path.write_text(
                json.dumps({"provider": "openai", "model": "gpt-5.4"}),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--config-path",
                    str(config_path),
                    "--set-default-agent",
                    "leader",
                ],
                check=True,
            )

            self.assertEqual(
                json.loads(config_path.read_text(encoding="utf-8")),
                {
                    "provider": "openai",
                    "model": "gpt-5.4",
                    "default_agent": "leader",
                },
            )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_opencode_config -v`
Expected: FAIL with `No such file or directory` for `pack/tools/opencode_config.py`

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("opencode config must be a JSON object")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--set-default-agent")
    args = parser.parse_args()

    config_path = Path(args.config_path)
    data = load_json(config_path)

    if args.set_default_agent:
        data["default_agent"] = args.set_default_agent

    write_json(config_path, data)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_opencode_config -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pack/tools/opencode_config.py tests/test_opencode_config.py
git commit -m "feat: add opencode config merge helper"
```

### Task 2: Use the helper in both installers

**Files:**
- Modify: `install.sh:6-77`
- Modify: `install.sh:229-238`
- Modify: `install.ps1:71-143`
- Modify: `install.ps1:261-347`
- Test: `tests/test_install_sh_provider_allowlist.py`

- [ ] **Step 1: Write the failing test**

```python
    def test_non_interactive_install_sets_default_agent_and_preserves_existing_config(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "opencode"
            data_dir = home / ".local" / "share" / "opencode"
            cache_dir = home / ".cache" / "opencode"
            config_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            cache_dir.mkdir(parents=True)

            (config_dir / "opencode.json").write_text(
                json.dumps({"provider": "openai", "model": "gpt-5.4"}),
                encoding="utf-8",
            )

            subprocess.run(
                ["bash", "install.sh", "--force"],
                cwd=repo_root,
                env={**os.environ, "HOME": str(home)},
                stdin=subprocess.DEVNULL,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertEqual(
                json.loads((config_dir / "opencode.json").read_text(encoding="utf-8")),
                {
                    "provider": "openai",
                    "model": "gpt-5.4",
                    "default_agent": "leader",
                },
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_install_sh_provider_allowlist.InstallShProviderAllowlistTests.test_non_interactive_install_sets_default_agent_and_preserves_existing_config -v`
Expected: FAIL because `default_agent` is missing from `opencode.json`

- [ ] **Step 3: Write minimal implementation**

```bash
# install.sh
opencode_config() {
  "$PYTHON_BIN" "${SCRIPT_DIR}/pack/tools/opencode_config.py" "$@"
}

write_default_agent() {
  local config_path="$1"
  opencode_config \
    --config-path "$config_path" \
    --set-default-agent leader
}

# after restore_user_config / after copy
write_default_agent "${TARGET}/opencode.json"
```

```powershell
# install.ps1
function Invoke-OpenCodeConfig {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $invokeArgs = @()
    if ($script:PythonPrefixArgs) {
        $invokeArgs += $script:PythonPrefixArgs
    }
    $invokeArgs += (Join-Path $script:PackDir "tools/opencode_config.py")
    $invokeArgs += $Arguments

    & $script:PythonBin @invokeArgs | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "opencode_config.py failed"
    }
}

function Write-DefaultAgent {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ConfigPath
    )

    Invoke-OpenCodeConfig @(
        "--config-path", $ConfigPath,
        "--set-default-agent", "leader"
    )
}

# after restore / copy
Write-DefaultAgent -ConfigPath (Join-Path $resolvedTarget "opencode.json")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_install_sh_provider_allowlist -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add install.sh install.ps1 tests/test_install_sh_provider_allowlist.py
git commit -m "feat: set leader as default installed agent"
```

### Task 3: Mark helper agents as hidden subagents

**Files:**
- Modify: `pack/agents/analyzer.md:1-8`
- Modify: `pack/agents/implementer.md:1-8`
- Modify: `pack/agents/reviewer.md:1-10`
- Test: `tests/test_pack_agents.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from pathlib import Path


class PackAgentMetadataTests(unittest.TestCase):
    def test_helper_agents_are_hidden_subagents(self):
        repo_root = Path(__file__).resolve().parents[1]
        for name in ["analyzer", "implementer", "reviewer"]:
            content = (repo_root / "pack" / "agents" / f"{name}.md").read_text(encoding="utf-8")
            self.assertIn("mode: subagent", content)
            self.assertIn("hidden: true", content)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_pack_agents -v`
Expected: FAIL because the markdown files do not yet contain OpenCode metadata

- [ ] **Step 3: Write minimal implementation**

```markdown
---
description: Pack internal analyzer agent dispatched by leader
mode: subagent
hidden: true
---

# Agent: analyzer
```

```markdown
---
description: Pack internal implementer agent dispatched by leader
mode: subagent
hidden: true
---

# Agent: implementer
```

```markdown
---
description: Pack internal reviewer agent dispatched by leader
mode: subagent
hidden: true
---

# Agent: reviewer
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_pack_agents -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pack/agents/analyzer.md pack/agents/implementer.md pack/agents/reviewer.md tests/test_pack_agents.py
git commit -m "feat: hide internal helper agents"
```

### Task 4: Verify full install behavior end-to-end

**Files:**
- Modify: `tests/test_install_sh_provider_allowlist.py:9-117`
- Test: `tests/test_opencode_config.py`
- Test: `tests/test_pack_agents.py`

- [ ] **Step 1: Add repeated-install coverage**

```python
    def test_repeated_non_interactive_install_keeps_default_agent_stable(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "opencode"
            data_dir = home / ".local" / "share" / "opencode"
            cache_dir = home / ".cache" / "opencode"
            config_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            cache_dir.mkdir(parents=True)

            (config_dir / "opencode.json").write_text(
                json.dumps({"provider": "openai"}),
                encoding="utf-8",
            )

            env = {**os.environ, "HOME": str(home)}
            subprocess.run(["bash", "install.sh", "--force"], cwd=repo_root, env=env, stdin=subprocess.DEVNULL, text=True, capture_output=True, check=True)
            subprocess.run(["bash", "install.sh", "--force"], cwd=repo_root, env=env, stdin=subprocess.DEVNULL, text=True, capture_output=True, check=True)

            self.assertEqual(
                json.loads((config_dir / "opencode.json").read_text(encoding="utf-8")),
                {"provider": "openai", "default_agent": "leader"},
            )
```

- [ ] **Step 2: Run the focused test suite**

Run: `python3 -m unittest tests.test_opencode_config tests.test_pack_agents tests.test_install_sh_provider_allowlist -v`
Expected: PASS

- [ ] **Step 3: Run a manual smoke check of installed agent files**

Run: `bash install.sh --target "/tmp/do-the-thing-smoke" --force`
Expected: installer succeeds and writes `/tmp/do-the-thing-smoke/opencode.json`

Run: `python3 - <<'PY'
import json
from pathlib import Path
cfg = Path('/tmp/do-the-thing-smoke/opencode.json')
print(json.loads(cfg.read_text(encoding='utf-8')).get('default_agent'))
PY`
Expected: output is `leader`

- [ ] **Step 4: Commit**

```bash
git add tests/test_install_sh_provider_allowlist.py tests/test_opencode_config.py tests/test_pack_agents.py
git commit -m "test: cover leader default agent install flow"
```
