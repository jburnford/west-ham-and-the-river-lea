"""Fingerprint scene modules/data so the browser cannot mix older scene assets."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'docs'
modules={}
assets={}
for path in sorted(ROOT.rglob('*.js')):
 relative='./'+path.relative_to(ROOT).as_posix()
 digest=hashlib.sha256(path.read_bytes()).hexdigest()[:16]
 modules[relative]=relative+'?v='+digest
for directory in [ROOT/'data',ROOT/'assets/textures']:
 for path in sorted(directory.rglob('*')):
  if not path.is_file():continue
  relative='./'+path.relative_to(ROOT).as_posix()
  digest=hashlib.sha256(path.read_bytes()).hexdigest()[:16]
  assets[relative]=relative+'?v='+digest
revision=hashlib.sha256(json.dumps([modules,assets],sort_keys=True).encode()).hexdigest()[:12]
(ROOT/'scene-manifest.json').write_text(json.dumps({'revision':revision,'modules':modules,'assets':assets},indent=2)+'\n')
print(f'Scene {revision}: {len(modules)} modules and {len(assets)} data/texture assets fingerprinted.')
