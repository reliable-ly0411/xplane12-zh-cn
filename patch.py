#!/usr/bin/env python3
"""Offline, reversible X-Plane 12 Chinese supplement installer (stdlib only)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from pe_labels import patch_executable

ROOT = Path(__file__).resolve().parent
FILES = ('X-Plane.exe', 'Resources/text/Chinese.txt')
BACKUP = '.xplane12-zh-cn-backup'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def manifest():
    return read_json(ROOT / 'data/manifest.json')

def dictionary(source):
    # Use the user's original dictionary; distribute only additions/changes.
    text = source.decode('utf-8')
    result = dict(line[7:].split('====', 1) for line in text.splitlines()
                  if line.startswith('STRING ') and '====' in line)
    result.update(read_json(ROOT / 'data/translation-overlay.json'))
    header = 'A\n900\nTRANSLATION\n# Codex local Chinese supplement for X-Plane 12.4.3-r2\n'
    return (header + '\n'.join('STRING ' + key + '====' + value
                               for key, value in result.items()) + '\n').encode('utf-8')

def ensure_not_running():
    if sys.platform == 'win32':
        listing = subprocess.check_output(
            ['tasklist', '/FI', 'IMAGENAME eq X-Plane.exe', '/FO', 'CSV', '/NH'],
            creationflags=subprocess.CREATE_NO_WINDOW).lower()
        running = b'x-plane.exe' in listing
    elif Path('/proc').is_dir():
        running = False
        for item in Path('/proc').iterdir():
            if not item.name.isdigit():
                continue
            try:
                cmd = (item / 'cmdline').read_bytes().split(b'\0')[0]
            except (OSError, ProcessLookupError):
                continue
            if cmd.replace(b'\\', b'/').rsplit(b'/', 1)[-1].lower() == b'x-plane.exe':
                running = True
                break
    else:
        raise ValueError('Only Windows and Linux/Proton are supported.')
    if running:
        raise ValueError('Close all X-Plane instances before apply/restore.')

def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.xploc-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            shutil.copymode(path, temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def inspect(game, meta):
    result = {}
    for name in FILES:
        path = game / name
        if not path.is_file():
            raise ValueError('Missing required file: ' + str(path))
        digest = sha(path.read_bytes())
        result[name] = ('original' if digest == meta['original'][name] else
                        'patched' if digest == meta['installed'][name] else 'unsupported')
    return result

def checked_originals(folder, meta):
    data = {name: (folder / name).read_bytes() for name in FILES}
    for name, content in data.items():
        if sha(content) != meta['original'][name]:
            raise ValueError('Original-file hash mismatch: ' + str(folder / name))
    return data

def transaction(game, contents):
    before = {name: (game / name).read_bytes() for name in FILES}
    try:
        for name, content in contents.items():
            atomic_write(game / name, content)
            if sha((game / name).read_bytes()) != sha(content):
                raise OSError('Write verification failed: ' + name)
    except BaseException:
        # Backups remain available even if the filesystem prevents rollback.
        for name, content in before.items():
            atomic_write(game / name, content)
        raise

def apply(game, original_dir=None, dry_run=False):
    meta = manifest()
    statuses = inspect(game, meta)
    if 'unsupported' in statuses.values():
        raise ValueError('Unsupported version or modified files; refusing to overwrite: ' + str(statuses))
    backup = game / BACKUP
    if (backup / 'state.json').exists():
        state = read_json(backup / 'state.json')
        if state['original'] != meta['original'] or state['installed'] != meta['installed']:
            raise ValueError('Backup belongs to a different patch version. Restore with that version first.')
        originals = checked_originals(backup, meta)
    elif original_dir:
        originals = checked_originals(original_dir, meta)
    elif all(value == 'original' for value in statuses.values()):
        originals = checked_originals(game, meta)
    else:
        raise ValueError('Untracked existing patch. Supply --original-dir with verified original files.')
    if all(value == 'patched' for value in statuses.values()) and (backup / 'state.json').exists():
        print('Already installed; original backups verified.')
        return
    outputs = {
        'X-Plane.exe': patch_executable(originals['X-Plane.exe'], read_json(ROOT / 'data/data-output-labels.json')),
        'Resources/text/Chinese.txt': dictionary(originals['Resources/text/Chinese.txt']),
    }
    for name, content in outputs.items():
        if sha(content) != meta['installed'][name]:
            raise ValueError('Generated output hash mismatch: ' + name)
    if dry_run:
        print('Dry run passed: original files and both generated hashes match. No files written.')
        return
    ensure_not_running()
    if not (backup / 'state.json').exists():
        # Do not overwrite a possibly interrupted/incomplete backup directory.
        if backup.exists():
            raise ValueError('Backup directory already exists without state.json; inspect it before continuing.')
        backup.mkdir()
        for name, content in originals.items():
            atomic_write(backup / name, content)
        checked_originals(backup, meta)
        atomic_write(backup / 'state.json', json.dumps(meta, ensure_ascii=False, indent=2).encode('utf-8'))
    transaction(game, outputs)
    print('Installed. Select Chinese in X-Plane General settings and restart if necessary.')
    print('Original backups: ' + str(backup))

def restore(game):
    meta = manifest()
    statuses = inspect(game, meta)
    if 'unsupported' in statuses.values():
        raise ValueError('Files changed after installation; refusing to replace an update or user edit.')
    backup = game / BACKUP
    state = read_json(backup / 'state.json')
    if state['original'] != meta['original'] or state['installed'] != meta['installed']:
        raise ValueError('Backup belongs to a different patch version.')
    originals = checked_originals(backup, meta)
    ensure_not_running()
    transaction(game, originals)
    print('Original EXE and Chinese dictionary restored. Backups retained; bindings/preferences untouched.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'apply', 'restore'])
    parser.add_argument('game', type=Path, help='X-Plane 12 installation directory')
    parser.add_argument('--dry-run', action='store_true', help='apply: generate and validate without writing')
    parser.add_argument('--original-dir', type=Path, help='apply: adopt an existing patch using verified original backups')
    args = parser.parse_args()
    if (args.dry_run or args.original_dir) and args.action != 'apply':
        parser.error('--dry-run and --original-dir are only valid with apply')
    game = args.game.expanduser().resolve()
    try:
        if args.action == 'check':
            result = inspect(game, manifest())
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if 'unsupported' in result.values() else 0
        if args.action == 'apply':
            apply(game, args.original_dir, args.dry_run)
        else:
            restore(game)
        return 0
    except (ValueError, OSError, KeyError, AssertionError, subprocess.SubprocessError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
