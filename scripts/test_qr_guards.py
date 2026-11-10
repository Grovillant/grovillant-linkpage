"""Fail-closed regressions: changed legacy URLs/UTM and corrupted print assets."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import qr_common
from validate_qr import validate
class Guards(unittest.TestCase):
    def test_registry_rejects_unsafe_changes(self):
        data=qr_common.registry()
        for field,value in [('stable_url','http://localhost/q/pkg'),('current_target','https://example.com/'),('may_disable',True)]:
            altered=copy.deepcopy(data); altered['assets'][1][field]=value
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); (root/'qr').mkdir(); (root/'qr/registry.json').write_text(json.dumps(altered))
                with patch.object(qr_common,'ROOT',root), self.assertRaises(AssertionError): qr_common.registry()
        altered=copy.deepcopy(data); altered['assets'][1]['utm']['campaign']='new'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'qr').mkdir(); (root/'qr/registry.json').write_text(json.dumps(altered))
            with patch.object(qr_common,'ROOT',root), self.assertRaises(AssertionError): qr_common.registry()
    def test_corrupt_file_rejected(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            pack=Path(tmp)/'pack'; shutil.copytree(qr_common.ROOT/'print-pack/v1.0.0',pack)
            manifest=json.loads((pack/'QR-MANIFEST.json').read_text())
            (pack/manifest['files'][0]['file']).write_text('corrupt')
            with self.assertRaises(AssertionError): validate(pack)
if __name__=='__main__': unittest.main()
