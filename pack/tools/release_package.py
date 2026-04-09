import argparse
import shutil
import tarfile
import zipfile
from pathlib import Path


RELEASE_ITEMS = ("install.sh", "install.ps1", "pack")
RELEASE_BASENAME = "do-the-thing"


def build_release_archives(repo_root: Path, out_dir: Path, version: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    tar_path = out_dir / f"{RELEASE_BASENAME}-{version}.tar.gz"
    zip_path = out_dir / f"{RELEASE_BASENAME}-{version}.zip"

    with tarfile.open(tar_path, "w:gz") as tar:
        for item in RELEASE_ITEMS:
            tar.add(repo_root / item, arcname=item)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in RELEASE_ITEMS:
            path = repo_root / item
            if path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file():
                        archive.write(child, child.relative_to(repo_root))
            else:
                archive.write(path, item)

    return tar_path, zip_path


def build_release_artifacts(repo_root: Path, out_dir: Path, version: str):
    tar_path, zip_path = build_release_archives(repo_root, out_dir, version)
    bootstrap_sh = out_dir / "install.sh"
    bootstrap_ps1 = out_dir / "install.ps1"

    shutil.copy2(repo_root / "bootstrap" / "install.sh", bootstrap_sh)
    shutil.copy2(repo_root / "bootstrap" / "install.ps1", bootstrap_ps1)

    return {
        "tar.gz": tar_path,
        "zip": zip_path,
        "bootstrap.sh": bootstrap_sh,
        "bootstrap.ps1": bootstrap_ps1,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
    )
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    build_release_artifacts(Path(args.repo_root), Path(args.out_dir), args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
