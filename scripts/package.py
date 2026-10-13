"""Build deterministic ZIPs and export each ZIP's own manifest (Python 3.11+)."""
import hashlib
import json
import pathlib
import re
import tomllib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
VERSION = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\Z")


def build_packages(root=ROOT):
    entries = []
    dist = root / "dist"
    dist.mkdir(exist_ok=True)
    for package in sorted((root / "packages").iterdir()):
        if not package.is_dir() or not (package / "manifest.toml").is_file():
            continue
        source = dist / package.name
        declaration = (source / "manifest.toml").read_bytes()
        if not 0 < len(declaration) <= 65536:
            raise ValueError("Package manifest exceeds 64 KiB")
        manifest = tomllib.loads(declaration.decode("utf-8"))
        ident, version = manifest["id"], manifest["version"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", ident) or not VERSION.fullmatch(version):
            raise ValueError("Invalid package ID or version")
        if any(e["id"] == ident for e in entries):
            raise ValueError(f"Duplicate package ID: {ident}")
        archive = dist / f"{ident}-{version}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for path in sorted(source.rglob("*")):
                if path.is_symlink():
                    raise ValueError(f"Package symlink is not supported: {path}")
                if path.is_file():
                    info = zipfile.ZipInfo(path.relative_to(source).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    z.writestr(info, path.read_bytes(), compresslevel=9)
        # Export the exact archived bytes, rather than maintain a second declaration.
        with zipfile.ZipFile(archive) as z:
            declaration = z.read("manifest.toml")
        exported = dist / f"{ident}@{version}.manifest.toml"
        exported.write_bytes(declaration)
        entries.append({"id": ident, "version": version, "archive": archive.name,
                        "manifest": exported.name, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()})
    if not entries:
        raise ValueError("No built packages found; run pnpm build first")
    # This disposable plan is for the publisher only. LC discovers GitHub assets directly.
    (dist / "release-assets.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return entries


if __name__ == "__main__":
    print(json.dumps(build_packages(), ensure_ascii=False, indent=2))
