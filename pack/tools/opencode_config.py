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
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


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
