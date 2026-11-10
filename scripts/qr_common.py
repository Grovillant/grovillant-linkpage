"""Shared fail-closed registry contract. No network or side effects on import."""
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
ROOT = Path(__file__).resolve().parents[1]
LEGACY = {'pkg':'print','manual':'print','card':'print','fair':'offline','ad':'paid'}
def registry():
    data = json.loads((ROOT/'qr/registry.json').read_text())
    assets = data['assets']
    ids = [a['qr_id'] for a in assets]
    assert len(ids) == len(set(ids)) and set(LEGACY) <= set(ids)
    urls = [a['stable_url'] for a in assets]
    assert len(urls) == len(set(urls))
    for a in assets:
        key = a['qr_id']
        assert re.fullmatch(r'[a-z][a-z0-9-]*', key)
        assert a['status'] in ('active','retired')
        for field in ('asset_name','material_type','owner','created_date','last_review_date','version','changes','rollback'):
            assert a[field], field
        assert a['may_disable'] is False
        expected = 'https://grovillant.com' + ('' if key=='brand' else '/q/'+key)
        assert a['stable_url'] == expected
        target = urlsplit(a['current_target'])
        assert target.scheme == 'https' and target.netloc == 'grovillant.com'
        assert target.path == '/' and not target.fragment
        if key == 'brand':
            assert a['utm'] is None and not target.query
        else:
            utm = a['utm']
            assert utm['source'] == 'qr' and utm['campaign'] == key
            if key in LEGACY: assert utm['medium'] == LEGACY[key]
            assert parse_qs(target.query) == {'utm_'+k:[v] for k,v in utm.items()}
    return data
