import argparse
import json
from pathlib import Path


RELEASE_BASENAME = "do-the-thing"
REQUIRED_RELEASE_FILES = ("install.sh", "install.ps1", "pack")


def build_release_asset_filename(version: str, archive_format: str) -> str:
    if archive_format not in {"tar.gz", "zip"}:
        raise ValueError("unsupported archive format")
    return f"{RELEASE_BASENAME}-{version}.{archive_format}"


def build_release_asset_url(repo: str, version: str, archive_format: str) -> str:
    filename = build_release_asset_filename(version, archive_format)
    return f"https://github.com/{repo}/releases/download/{version}/{filename}"


def extract_release_version(release_metadata: str) -> str:
    payload = json.loads(release_metadata)
    version = payload.get("tag_name")
    if not isinstance(version, str) or not version:
        raise ValueError("missing tag_name in release metadata")
    return version


def validate_extracted_release(root: Path) -> Path:
    candidates = [root]
    candidates.extend(path for path in root.iterdir() if path.is_dir())

    for candidate in candidates:
        missing = [
            name for name in REQUIRED_RELEASE_FILES if not (candidate / name).exists()
        ]
        if not missing:
            return candidate

    raise ValueError("missing required release files: install.sh, install.ps1, pack")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo")
    parser.add_argument("--version")
    parser.add_argument("--archive-format")
    parser.add_argument("--print-asset-url", action="store_true")
    parser.add_argument("--validate-extracted-root")
    args = parser.parse_args()

    if args.print_asset_url:
        if not args.repo or not args.version or not args.archive_format:
            raise SystemExit("--repo, --version, and --archive-format are required")
        print(build_release_asset_url(args.repo, args.version, args.archive_format))
        return 0

    if args.validate_extracted_root:
        print(validate_extracted_release(Path(args.validate_extracted_root)))
        return 0

    raise SystemExit("no action requested")


if __name__ == "__main__":
    raise SystemExit(main())
