import tempfile
import unittest
from pathlib import Path

from pack.tools.release_bootstrap import (
    build_release_asset_filename,
    build_release_asset_url,
    extract_release_version,
    validate_extracted_release,
)


class ReleaseBootstrapTests(unittest.TestCase):
    def test_build_release_asset_url_for_tarball(self):
        self.assertEqual(
            build_release_asset_url(
                repo="chendaleiQ/do-the-thing",
                version="v1.2.3",
                archive_format="tar.gz",
            ),
            "https://github.com/chendaleiQ/do-the-thing/releases/download/v1.2.3/do-the-thing-v1.2.3.tar.gz",
        )

    def test_build_release_asset_filename_for_zip(self):
        self.assertEqual(
            build_release_asset_filename("v1.2.3", "zip"),
            "do-the-thing-v1.2.3.zip",
        )

    def test_extract_release_version_reads_tag_name(self):
        self.assertEqual(
            extract_release_version('{"tag_name": "v1.2.3"}'),
            "v1.2.3",
        )

    def test_extract_release_version_rejects_missing_tag_name(self):
        with self.assertRaisesRegex(ValueError, "missing tag_name"):
            extract_release_version("{}")

    def test_validate_extracted_release_requires_packaged_installers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pack").mkdir()
            (root / "pack" / "AGENTS.md").write_text("agents", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing required release files"):
                validate_extracted_release(root)

    def test_validate_extracted_release_accepts_nested_archive_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extracted = root / "do-the-thing-v1.2.3"
            (extracted / "pack").mkdir(parents=True)
            (extracted / "pack" / "AGENTS.md").write_text(
                "agents",
                encoding="utf-8",
            )
            (extracted / "install.sh").write_text(
                "#!/usr/bin/env bash\n", encoding="utf-8"
            )
            (extracted / "install.ps1").write_text(
                "Write-Host 'ok'\n", encoding="utf-8"
            )

            self.assertEqual(validate_extracted_release(root), extracted)


if __name__ == "__main__":
    unittest.main()
