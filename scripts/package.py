"""Build deterministic ZIPs and the versioned download catalog (Python 3.11+)."""
import hashlib, json, os, pathlib, tomllib, zipfile
root = pathlib.Path(__file__).resolve().parent.parent
repository = os.environ.get('DLC_REPOSITORY', 'sdfsfsk/LingChat-DLC')
project = json.loads((root / 'package.json').read_text(encoding='utf-8'))
tag = os.environ.get('DLC_RELEASE_TAG', 'v' + project['version'])
prior_path = root / 'catalog.json'
prior = json.loads(prior_path.read_text(encoding='utf-8')) if prior_path.exists() else {'packages': []}
entries = []
for package in sorted((root / 'packages').iterdir()):
    if not package.is_dir() or not (package / 'manifest.toml').is_file():
        continue
    source = root / 'dist' / package.name
    manifest = tomllib.loads((source / 'manifest.toml').read_text(encoding='utf-8'))
    filename = f"{manifest['id']}-{manifest['version']}.zip"
    archive = root / 'dist' / filename
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(source.rglob('*')):
            if path.is_file():
                info = zipfile.ZipInfo(path.relative_to(source).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
                info.create_system = 3  # Identical Unix metadata on Windows/Linux builders.
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, path.read_bytes(), compresslevel=9)
    blob = archive.read_bytes()
    entries.append({ 'id': manifest['id'], 'name': manifest['name'], 'description': manifest['description'],
        'version': manifest['version'], 'url': f'https://github.com/{repository}/releases/download/{tag}/{filename}',
        'sha256': hashlib.sha256(blob).hexdigest(), 'size': len(blob), 'api_version': 1 })
catalog = {'schema_version': 1, 'packages': entries}
for entry in entries:
    old = next((p for p in prior['packages'] if p['id'] == entry['id']), None)
    if old and old['version'] == entry['version'] and old['sha256'] != entry['sha256']:
        raise SystemExit(f"Package {entry['id']} changed without a version bump; published versions are immutable")
(root / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(catalog, ensure_ascii=False, indent=2))
