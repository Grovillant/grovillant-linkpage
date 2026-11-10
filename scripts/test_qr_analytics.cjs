// Offline VM only. Does not load the external analytics script or send requests.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const window = {};
vm.runInNewContext(fs.readFileSync(path.join(root, 'qr-analytics.js'), 'utf8'), {window, URL});
const filter = window.vaq[0][1];
const assets = JSON.parse(fs.readFileSync(path.join(root, 'qr/registry.json'))).assets;
for (const asset of assets) {
  assert.equal(filter({url:asset.current_target}).url, asset.current_target);
  assert.equal(filter({url:asset.current_target + (asset.utm ? '&' : '?') + 'private=example#secret'}).url, asset.current_target);
}
for (const query of ['utm_source=qr&utm_medium=print&utm_campaign=person-123', 'utm_source=qr&utm_medium=wrong&utm_campaign=pkg', 'utm_source=qr&utm_source=person&utm_medium=print&utm_campaign=pkg']) {
  assert.equal(filter({url:'https://grovillant.com/?'+query}).url,'https://grovillant.com/');
}
assert.equal(filter({url:'https://other.example/private'}),null);
assert.equal(filter({url:'https://grovillant.com/private/person-123'}),null);
assert.equal(filter({url:'invalid'}),null);
console.log('PASS: six destinations; unknown parameters/hash/duplicate UTM stripped; foreign/private URLs dropped');
