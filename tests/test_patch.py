import collections
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch as mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import patch

class TranslationData(unittest.TestCase):
    def test_parameters_whitespace_and_command_references(self):
        overlay = patch.read_json(patch.ROOT / 'data/translation-overlay.json')
        self.assertEqual(len(overlay), patch.manifest()['overlay_entries'])
        for key, value in overlay.items():
            with self.subTest(key=key):
                for pattern in [r'%(\d+)(?::[^%]*)?%', r'\[sim/[^\]]+\]']:
                    self.assertEqual(collections.Counter(re.findall(pattern, key)), collections.Counter(re.findall(pattern, value)))
                self.assertEqual(re.match(r'[ \t]*', key)[0], re.match(r'[ \t]*', value)[0])
                self.assertEqual(re.search(r'[ \t]*$', key)[0], re.search(r'[ \t]*$', value)[0])

    def test_data_output_table(self):
        rows = patch.read_json(patch.ROOT / 'data/data-output-labels.json')
        self.assertEqual(len(rows), 173)
        self.assertEqual(len({r['pointer_offset'] for r in rows}), 173)
        self.assertEqual(len({r['label'] for r in rows}), 173)
        for row in rows:
            self.assertRegex(row['chinese'], r'[\u3400-\u9fff]')
            self.assertNotIn('\0', row['label'] + row['chinese'])

class FileSafety(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.game = Path(self.temporary.name)
        self.originals = {name: ('original ' + name).encode() for name in patch.FILES}
        self.outputs = {name: ('translated ' + name).encode() for name in patch.FILES}
        self.meta = {kind: {name: patch.sha(value) for name, value in data.items()} for kind, data in [('original', self.originals), ('installed', self.outputs)]}
        for name, content in self.originals.items():
            patch.atomic_write(self.game / name, content)

    def tearDown(self):
        self.temporary.cleanup()

    def test_unknown_files_are_rejected_before_writes(self):
        path = self.game / patch.FILES[0]
        path.write_bytes(b'new Steam version')
        with mock.object(patch, 'manifest', return_value=self.meta):
            with self.assertRaisesRegex(ValueError, 'Unsupported'):
                patch.apply(self.game)
        self.assertEqual(path.read_bytes(), b'new Steam version')
        self.assertFalse((self.game / patch.BACKUP).exists())

    def test_failed_second_write_rolls_back_both_files(self):
        real_write = patch.atomic_write
        calls = []
        def fail_second(path, data):
            calls.append(path)
            if len(calls) == 2:
                raise OSError('simulated second-file failure')
            real_write(path, data)
        with mock.object(patch, 'atomic_write', side_effect=fail_second):
            with self.assertRaises(OSError):
                patch.transaction(self.game, self.outputs)
        for name, content in self.originals.items():
            self.assertEqual((self.game / name).read_bytes(), content)

    def test_tampered_backup_prevents_restore(self):
        backup = self.game / patch.BACKUP
        for name, content in self.originals.items():
            patch.atomic_write(backup / name, content)
            patch.atomic_write(self.game / name, self.outputs[name])
        patch.atomic_write(backup / 'state.json', json.dumps(self.meta).encode())
        (backup / patch.FILES[0]).write_bytes(b'corrupt backup')
        with mock.object(patch, 'manifest', return_value=self.meta):
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                patch.restore(self.game)
        for name, content in self.outputs.items():
            self.assertEqual((self.game / name).read_bytes(), content)

if __name__ == '__main__':
    unittest.main()
