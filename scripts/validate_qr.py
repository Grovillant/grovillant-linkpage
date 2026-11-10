"""Local static + image + HTTP smoke test. Optional bounded read-only live check.
Stdout JSON contains no customer data, request headers, or response bodies.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
import urllib.request
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from qr_common import ROOT, registry
from build_qr_routes import outputs

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(pack):
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw
    data=registry(); assets={a['qr_id']:a for a in data['assets']}
    for p,content in outputs().items(): assert p.read_text()==content,str(p)
    manifest=json.loads((pack/'QR-MANIFEST.json').read_text())
    assert manifest['registry_sha256']==digest(ROOT/'qr/registry.json')
    assert manifest['generator_sha256']==digest(ROOT/'generate_qr.py')
    expected={(k,f) for k in assets for f in ['SVG','PNG']}
    assert len(manifest['files'])==len(expected)
    assert {(f['qr_id'],f['format']) for f in manifest['files']}==expected
    listed={f['file'] for f in manifest['files']}|{'PRINT-README-中文.md','QR-MANIFEST.json','SHA256SUMS.txt'}
    assert {p.name for p in pack.iterdir()}==listed
    results=[]
    for entry in manifest['files']:
        path=pack/entry['file']; a=assets[entry['qr_id']]
        assert path.parent==pack and path.name==entry['file']
        assert digest(path)==entry['sha256']
        assert entry['url']==a['stable_url'] and entry['target']==a['current_target'] and entry['utm']==a['utm']
        assert entry['version']==manifest['version'] and entry['error_correction']=='H'
        if entry['format']=='PNG':
            im=Image.open(path); im.load()
            assert list(im.size)==entry['pixels'] and abs(im.info['dpi'][0]-600)<1
        else:
            tree=ET.parse(path).getroot(); n=entry['modules_including_border']
            assert tree.attrib['viewBox']==f'0 0 {n} {n}'
            assert tree.attrib['width']==tree.attrib['height']==str(a['recommended_size_mm'])+'mm'
            # Rasterize this restricted, self-contained SVG rect grammar from file.
            assert len(tree)==2 and tree[0].attrib==dict(width=str(n),height=str(n),fill='white')
            assert tree[1].tag.endswith('g') and tree[1].attrib=={'fill':'black'}
            im=Image.new('RGB',(n*32,n*32),'white'); draw=ImageDraw.Draw(im)
            for cell in tree[1]:
                assert cell.tag.endswith('rect') and cell.attrib['width']==cell.attrib['height']=='1'
                x=int(cell.attrib['x']); y=int(cell.attrib['y'])
                draw.rectangle((x*32,y*32,x*32+31,y*32+31),fill='black')
        ar=np.array(im.convert('RGB')); n=entry['modules_including_border']; assert im.width==im.height==n*32
        border=entry['quiet_zone_modules']*32; assert border>=4*32
        assert all(np.all(edge==255) for edge in [ar[:border],ar[-border:],ar[:,:border],ar[:,-border:]])
        for side in [im.width,360]:
            sample=im.resize((side,side),Image.Resampling.NEAREST)
            decoded,_,_=cv2.QRCodeDetector().detectAndDecode(np.array(sample))
            assert decoded==entry['url'],(entry['file'],side,decoded)
        results.append({'file':entry['file'],'decode':'PASS original + 360px','checksum':'PASS','quiet_zone':'PASS'})
    for line in (pack/'SHA256SUMS.txt').read_text().splitlines():
        sha,name=line.split('  ',1); assert Path(name).name==name and digest(pack/name)==sha
    for doc in manifest['documents']: assert digest(pack/doc['file'])==doc['sha256']
    return data,results

def offline_http(data):
    routes={r['source']:r['destination'] for r in json.loads((ROOT/'vercel.json').read_text())['redirects']}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            path=urlsplit(self.path).path
            if path in routes:
                dest=routes[path].replace('https://grovillant.com',f'http://127.0.0.1:{self.server.server_port}',1)
                self.send_response(307); self.send_header('Location',dest); self.end_headers()
            elif path=='/':
                self.send_response(200); self.end_headers(); self.wfile.write((ROOT/'index.html').read_bytes())
            else: self.send_error(404)
    try:
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    except PermissionError:
        # Socket-denied sandbox: model route lookup, do not claim real HTTP.
        for a in data['assets']:
            if a['qr_id']=='brand': continue
            path='/q/'+a['qr_id']
            assert routes[path]==routes[path+'/']==a['current_target']
            assert urlsplit(routes[path]).path=='/'  # terminal page exists; no loop
            fallback=(ROOT/path.lstrip('/')/'index.html').read_text()
            assert html.escape(a['current_target'],quote=True) in fallback
            assert json.dumps(a['current_target']) in fallback
        body=(ROOT/'index.html').read_text()
        assert re.search(r'href="https://wa.me/[^"\s]+"',body)
        assert re.search(r'href="mailto:[^"\s]+@grovillant.com"',body)
        return {'mode':'OFFLINE_ROUTE_MODEL','route_count':len(routes),'status':'PASS',
                'http_status':'NOT_TESTED_socket_bind_denied','loop':'none in configured graph',
                'utm':'PASS exact registry match','buttons':'present_only'}
    thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start(); result=[]
    try:
        for a in data['assets']:
            paths=['/'] if a['qr_id']=='brand' else ['/q/'+a['qr_id'],'/q/'+a['qr_id']+'/']
            for path in paths:
                with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}'+path,timeout=5) as response:
                    expected=a['current_target'].replace('https://grovillant.com',f'http://127.0.0.1:{server.server_port}',1)
                    assert response.status==200 and response.url==expected
                    body=response.read().decode()
                    assert re.search(r'href="https://wa.me/[^"\s]+"',body)
                    assert re.search(r'href="mailto:[^"\s]+@grovillant.com"',body)
                    result.append({'path':path,'final_status':200,'utm':'PASS','buttons':'present_only'})
    finally: server.shutdown(); server.server_close()
    return result

def online(data):
    def check(a):
        try:
            url=a['stable_url']; seen=set(); codes=[]; had_html=False
            for _ in range(5):
                if url in seen: raise ValueError('loop')
                seen.add(url)
                with urllib.request.urlopen(url,timeout=12) as r:
                    codes.append(r.status)
                    assert r.status==200
                    body=r.read(200000).decode(errors='replace')
                    dest=re.search(r'http-equiv=["\']refresh["\'][^>]*content=["\']0;url=([^"\']+)',body,re.I)
                    if dest:
                        url=html.unescape(dest.group(1)); had_html=True
                        parsed=urlsplit(url)
                        assert parsed.scheme=='https' and parsed.netloc=='grovillant.com'
                        continue
                    target=r.url
                    ok=target==a['current_target'] or (a['qr_id']=='brand' and target.rstrip('/')==a['current_target'].rstrip('/'))
                    buttons=bool(re.search(r'href="https://wa.me/[^"\s]+"',body) and re.search(r'href="mailto:[^"\s]+@grovillant.com"',body))
                    return {'qr_id':a['qr_id'],'http_statuses':codes,'target_matches':ok,'buttons_present':buttons,'html_redirect_followed':had_html,'release_gate':'manual_phone_check_required'}
            raise ValueError('redirect_limit')
        except Exception as e:
            return {'qr_id':a['qr_id'],'status':'UNVERIFIED','reason':type(e).__name__}
    with ThreadPoolExecutor(max_workers=3) as pool: return list(pool.map(check,data['assets']))
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--pack',type=Path,required=True); p.add_argument('--online',action='store_true'); args=p.parse_args()
    data,images=validate(args.pack)
    result={'local':'PASS','images':images,'offline_http':offline_http(data),'online':online(data) if args.online else 'NOT_RUN','physical_phone_test':'NOT_RUN'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if isinstance(result['online'],list) and any(r.get('status')=='UNVERIFIED' or not r.get('target_matches',False) or not r.get('buttons_present',False) for r in result['online']): raise SystemExit(2)
