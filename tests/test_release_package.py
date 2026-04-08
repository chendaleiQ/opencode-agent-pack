import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

from pack.tools.release_package import build_release_artifacts


class ReleasePackageTests(unittest.TestCase):
    def test_build_release_artifacts_include_archives_and_bootstrap_scripts(self):
        repo_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_release_artifacts(repo_root, out_dir, "v1.2.3")
            tar_path = artifacts["tar.gz"]
            zip_path = artifacts["zip"]
            bootstrap_sh = artifacts["bootstrap.sh"]
            bootstrap_ps1 = artifacts["bootstrap.ps1"]

            with tarfile.open(tar_path, "r:gz") as tar:
                tar_names = tar.getnames()
            with zipfile.ZipFile(zip_path) as archive:
                zip_names = archive.namelist()

            self.assertIn("install.sh", tar_names)
            self.assertIn("install.ps1", tar_names)
            self.assertIn("pack/tools/release_bootstrap.py", tar_names)
            self.assertTrue(any(name.startswith("pack/") for name in tar_names))

            self.assertIn("install.sh", zip_names)
            self.assertIn("install.ps1", zip_names)
            self.assertIn("pack/tools/release_bootstrap.py", zip_names)
            self.assertTrue(any(name.startswith("pack/") for name in zip_names))
            self.assertEqual(bootstrap_sh.name, "install.sh")
            self.assertEqual(bootstrap_ps1.name, "install.ps1")
            self.assertTrue(
                bootstrap_sh.read_text(encoding="utf-8").startswith(
                    "#!/usr/bin/env bash"
                )
            )
            self.assertIn(
                "Invoke-WebRequest", bootstrap_ps1.read_text(encoding="utf-8")
            )


if __name__ == "__main__":
    unittest.main()
