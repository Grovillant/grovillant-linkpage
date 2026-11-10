"""Explicit local write only: registry -> Vercel 307 and HTML fallback."""
import argparse
import html
import json
from qr_common import ROOT, registry

def outputs():
    routes=[]; files={}
    for a in registry()['assets']:
        if a['qr_id']=='brand': continue
        path='/q/'+a['qr_id']; dest=a['current_target']
        for source in (path,path+'/'):
            routes.append(dict(source=source,destination=dest,permanent=False))
        files[ROOT/path.lstrip('/')/'index.html'] = ('<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8">\n'
            '<meta name="robots" content="noindex">\n'
            f'<meta http-equiv="refresh" content="0;url={html.escape(dest,quote=True)}">\n'
            f'<script>window.location.replace({json.dumps(dest)});</script>\n'
            f'</head><body><a href="{html.escape(dest,quote=True)}">Continue to Grovillant</a></body></html>\n')
    allowed = {a['qr_id']: a['utm']['medium'] for a in registry()['assets'] if a['utm']}
    files[ROOT/'qr-analytics.js'] = """// Generated from qr/registry.json. No individual tracking or storage.
(() => {
  const allowed = ALLOWED;
  window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
  window.va('beforeSend', (event) => {
    try {
      const url = new URL(event.url);
      if (url.origin !== 'https://grovillant.com' || url.pathname !== '/') return null;
      const campaign = url.searchParams.get('utm_campaign');
      const medium = url.searchParams.get('utm_medium');
      const valid = url.searchParams.get('utm_source') === 'qr' &&
        Object.prototype.hasOwnProperty.call(allowed, campaign) && allowed[campaign] === medium &&
        ['utm_source', 'utm_medium', 'utm_campaign'].every(k => url.searchParams.getAll(k).length === 1);
      url.search = ''; url.hash = '';
      if (valid) {
        url.searchParams.set('utm_source', 'qr');
        url.searchParams.set('utm_medium', medium);
        url.searchParams.set('utm_campaign', campaign);
      }
      return { ...event, url: url.toString() };
    } catch (_) { return null; }
  });
})();
""".replace('ALLOWED', json.dumps(allowed, sort_keys=True))
    files[ROOT/'vercel.json']=json.dumps({'redirects':routes},indent=2)+'\n'
    return files
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--write',action='store_true'); args=p.parse_args()
    for path,content in outputs().items():
        if args.write:
            path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content)
        else: assert path.exists() and path.read_text()==content, f'配置不同步: {path}'
    print('PASS: 跳转配置与注册表一致' if not args.write else '已生成本地配置；未部署')
