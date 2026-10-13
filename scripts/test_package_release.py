import importlib.util
import json
import pathlib
import tempfile
import unittest
import zipfile
from unittest.mock import patch


def load(name):
    spec = importlib.util.spec_from_file_location(name, pathlib.Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


packager, publisher = load("package"), load("publish")


class PackageReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        declaration = b"id='new-game'\nname='A new game'\nversion='1.0.0'\n"
        for folder in ["packages/arbitrary-folder", "dist/arbitrary-folder"]:
            path = self.root / folder
            path.mkdir(parents=True)
            (path / "manifest.toml").write_bytes(declaration)
        (self.root / "dist/arbitrary-folder/content.txt").write_text("content", encoding="utf-8")

    def test_discovers_a_new_folder_exports_exact_manifest_and_keeps_legacy_catalogs(self):
        legacy = self.root / "catalog-v2.json"
        legacy.write_bytes(b"old clients only")
        first = packager.build_packages(self.root)
        second = packager.build_packages(self.root)
        self.assertEqual(first, second)
        self.assertEqual(legacy.read_bytes(), b"old clients only")
        self.assertFalse((self.root / "catalog.json").exists())
        with zipfile.ZipFile(self.root / "dist" / first[0]["archive"]) as archive:
            self.assertEqual(archive.read("manifest.toml"), (self.root / "dist" / first[0]["manifest"]).read_bytes())
        self.assertEqual(len(publisher.release_files(self.root / "dist")), 2)

    def test_rejects_a_manifest_edited_separately_from_its_package(self):
        plan = packager.build_packages(self.root)
        (self.root / "dist" / plan[0]["manifest"]).write_text("different", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "differs"):
            publisher.release_files(self.root / "dist")

    def test_published_versions_are_immutable_without_a_central_catalog(self):
        packager.build_packages(self.root)
        files = publisher.release_files(self.root / "dist")
        name, (_, digest) = next(iter(files.items()))
        publisher.check_immutable(files, [{"assets": [{"name": name, "digest": digest}]}])
        for bad in [None, "sha256:wrong"]:
            with self.assertRaisesRegex(ValueError, "bump"):
                publisher.check_immutable(files, [{"assets": [{"name": name, "digest": bad}]}])

    def test_publish_only_exposes_the_release_after_all_uploads_succeed(self):
        packager.build_packages(self.root)
        calls = []
        def run(*args):
            calls.append(args)
            return "[[]]" if args[0] == "api" else ""
        with patch.object(publisher, "gh", side_effect=run):
            publisher.publish("v-next", "owner/repo", "commit", self.root)
        self.assertIn("--draft", calls[1])
        self.assertEqual(calls[2][:2], ("release", "upload"))
        self.assertIn("--draft=false", calls[3])
        self.assertTrue(any(arg.endswith(".manifest.toml") for arg in calls[2]))
        def fail_upload(*args):
            if args[:2] == ("release", "upload"):
                raise RuntimeError("Upload interrupted")
            return run(*args)
        calls.clear()
        with patch.object(publisher, "gh", side_effect=fail_upload):
            with self.assertRaises(RuntimeError):
                publisher.publish("v-next", "owner/repo", "commit", self.root)
        self.assertFalse(any("--draft=false" in args for args in calls))

    def test_plan_cannot_upload_files_outside_dist(self):
        plan = packager.build_packages(self.root)
        plan[0]["archive"] = "../private.zip"
        (self.root / "dist/release-assets.json").write_text(json.dumps(plan), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "inside dist"):
            publisher.release_files(self.root / "dist")


if __name__ == "__main__":
    unittest.main()
