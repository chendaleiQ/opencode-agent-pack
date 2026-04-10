#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def sync_opencode_plugin(data: dict, plugin_value: str) -> None:
    plugins = data.get("plugin")
    if not isinstance(plugins, list):
        plugins = []

    next_plugins = []
    insert_at = None
    for plugin in plugins:
        if plugin == plugin_value:
            if insert_at is None:
                insert_at = len(next_plugins)
            continue
        if isinstance(plugin, str) and plugin.startswith("do-the-thing@"):
            if insert_at is None:
                insert_at = len(next_plugins)
            continue
        if plugin not in next_plugins:
            next_plugins.append(plugin)

    if insert_at is None:
        next_plugins.append(plugin_value)
    else:
        next_plugins.insert(insert_at, plugin_value)

    data["plugin"] = next_plugins


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("opencode config must be a JSON object")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--set-default-agent")
    parser.add_argument("--set-opencode-plugin")
    args = parser.parse_args()

    config_path = Path(args.config_path)
    data = load_json(config_path)

    if args.set_default_agent:
        data["default_agent"] = args.set_default_agent

    if args.set_opencode_plugin:
        sync_opencode_plugin(data, args.set_opencode_plugin)

    write_json(config_path, data)


if __name__ == "__main__":
    main()
