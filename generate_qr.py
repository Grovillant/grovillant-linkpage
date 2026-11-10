"""Reproducible print assets. Existing release directories are never overwritten."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys
import tempfile
import os
import qrcode
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from qr_common import ROOT, registry

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version',required=True); p.add_argument('--output-root',type=Path,default=ROOT/'print-pack')
    args=p.parse_args()
    if not re.fullmatch(r'\d+\.\d+\.\d+',args.version): p.error('版本必须为 x.y.z')
    data=registry(); args.output_root.mkdir(parents=True,exist_ok=True)
    target=args.output_root/('v'+args.version)
    if target.exists(): p.error('版本已存在，拒绝覆盖；请用新版本或另一个 output-root 比较')
    with tempfile.TemporaryDirectory(dir=args.output_root,prefix='.building-') as temp:
        stage=Path(temp); entries=[]
        for a in data['assets']:
            # One matrix for both formats, no logo over modules. H + six white modules.
            qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,box_size=32,border=6)
            qr.add_data(a['stable_url']); qr.make(fit=True)
            matrix=qr.get_matrix(); n=len(matrix); px=n*32
            stem=f"grovillant-qr-{a['qr_id']}-v{args.version}-PRINT"
            png=stage/(stem+'-600dpi.png')
            qr.make_image(fill_color='black',back_color='white').convert('RGB').save(png,dpi=(600,600))
            cells=''.join(f'<rect x="{x}" y="{y}" width="1" height="1"/>' for y,row in enumerate(matrix) for x,cell in enumerate(row) if cell)
            svg=stage/(stem+'.svg')
            svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{a["recommended_size_mm"]}mm" height="{a["recommended_size_mm"]}mm" viewBox="0 0 {n} {n}" shape-rendering="crispEdges"><rect width="{n}" height="{n}" fill="white"/><g fill="black">{cells}</g></svg>\n')
            for file,fmt in ((svg,'SVG'),(png,'PNG')):
                entries.append(dict(file=file.name,qr_id=a['qr_id'],purpose=a['asset_name'],url=a['stable_url'],target=a['current_target'],utm=a['utm'],version=args.version,sha256=sha(file),format=fmt,pixels=[px,px] if fmt=='PNG' else None,dpi=600 if fmt=='PNG' else None,modules_including_border=n,quiet_zone_modules=6,error_correction='H',logo_overlay=False,recommended_size_mm=a['recommended_size_mm'],minimum_trial_size_mm=a['minimum_trial_size_mm'],release_status='artwork_ready_physical_and_live_acceptance_required'))
        for name in ['PRINT-README-中文.md']:
            (stage/name).write_bytes((ROOT/'qr'/name).read_bytes())
        manifest=dict(schema_version=1,version=args.version,registry_sha256=sha(ROOT/'qr/registry.json'),generator_sha256=sha(Path(__file__)),dependencies={x:importlib.metadata.version(x) for x in ['qrcode','Pillow']},files=entries,documents=[dict(file='PRINT-README-中文.md',sha256=sha(stage/'PRINT-README-中文.md'))])
        (stage/'QR-MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        sums=''.join(f'{sha(f)}  {f.name}\n' for f in sorted(stage.iterdir()) if f.is_file())
        (stage/'SHA256SUMS.txt').write_text(sums)
        # mkdir is the exclusive reservation even if two generators run at once.
        target.mkdir()
        for file in stage.iterdir(): os.rename(file,target/file.name)
    print(target)
if __name__=='__main__': main()
