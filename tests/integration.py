"""Uses privately supplied originals; never operates on the supplied directory."""
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch as mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import patch

if len(sys.argv) != 2:
    raise SystemExit('Usage: python3 tests/integration.py ORIGINAL_GAME_OR_BACKUP_DIR')
original = Path(sys.argv[1]).resolve()
meta = patch.manifest()
patch.checked_originals(original, meta)
with tempfile.TemporaryDirectory(prefix='xplane-zh-test-') as directory:
    game = Path(directory)
    for name in patch.FILES:
        (game / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original / name, game / name)
    preferences = game / 'Output/preferences/test-preservation.prf'
    preferences.parent.mkdir(parents=True)
    preferences.write_bytes(b'keep user bindings unchanged\n')
    # Temporary copies are never loaded by the running simulator.
    with mock.object(patch, 'ensure_not_running'):
        patch.apply(game)
        assert all(v == 'patched' for v in patch.inspect(game, meta).values())
        patch.apply(game)
        patch.restore(game)
        assert all(v == 'original' for v in patch.inspect(game, meta).values())
    assert preferences.read_bytes() == b'keep user bindings unchanged\n'
    patch.checked_originals(game / patch.BACKUP, meta)
print('PASS: exact generation, install, repeat install, byte-exact restore, retained backup and preference preservation.')
