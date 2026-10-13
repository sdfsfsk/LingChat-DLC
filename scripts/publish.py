"""Publish ZIP/manifest pairs atomically through a draft release; never edit catalogs."""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent


def release_files(dist):
    dist = dist.resolve()
    plan = json.loads((dist / "release-assets.json").read_text(encoding="utf-8"))
    if not plan or len(plan) > 256:
        raise ValueError("Invalid release plan")
    files = {}
    for entry in plan:
        archive = (dist / entry["archive"]).resolve()
        manifest = (dist / entry["manifest"]).resolve()
        if archive.parent != dist or manifest.parent != dist:
            raise ValueError("Release files must stay inside dist")
        if archive.name != f"{entry['id']}-{entry['version']}.zip" or manifest.name != f"{entry['id']}@{entry['version']}.manifest.toml":
            raise ValueError("Release file identity mismatch")
        if not 0 < archive.stat().st_size <= 128 * 1024 * 1024 or not 0 < manifest.stat().st_size <= 65536:
            raise ValueError("Release file size exceeds runtime limits")
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            raise ValueError("Archive changed after packaging")
        with zipfile.ZipFile(archive) as z:
            if z.getinfo("manifest.toml").file_size > 65536 or z.read("manifest.toml") != manifest.read_bytes():
                raise ValueError("Exported manifest differs from the ZIP")
        for file in (archive, manifest):
            if file.name in files:
                raise ValueError("Duplicate release file")
            files[file.name] = (file, "sha256:" + hashlib.sha256(file.read_bytes()).hexdigest())
    return files


def check_immutable(files, releases):
    for release in releases:
        if release.get("draft"):
            continue
        for asset in release.get("assets", []):
            if asset["name"] in files and (asset.get("digest") or "").lower() != files[asset["name"]][1]:
                raise ValueError(f"Published {asset['name']} differs or has no digest; bump its manifest version")


def gh(*args):
    return subprocess.check_output(["gh", *args], text=True)


def publish(tag, repository, revision, root=ROOT):
    files = release_files(root / "dist")
    pages = json.loads(gh("api", "--paginate", "--slurp", f"repos/{repository}/releases?per_page=100"))
    check_immutable(files, [release for page in pages for release in page])
    gh("release", "create", tag, "--repo", repository, "--draft", "--target", revision,
       "--title", f"LingChat DLC {tag}", "--generate-notes")
    gh("release", "upload", tag, "--repo", repository, *[str(path) for path, _ in files.values()])
    # A public release is only visible after every manifest and ZIP has uploaded.
    gh("release", "edit", tag, "--repo", repository, "--draft=false")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tag")
    parser.add_argument("--repo", default=os.environ.get("DLC_REPOSITORY", "sdfsfsk/LingChat-DLC"))
    parser.add_argument("--revision", default=os.environ.get("GITHUB_SHA", "main"))
    args = parser.parse_args()
    publish(args.tag, args.repo, args.revision)
