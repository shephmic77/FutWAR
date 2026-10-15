const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');
const core = require('../profile/explorer_core.js');

const site = path.resolve(__dirname, '..', 'site');
const html = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
assert.ok(Buffer.byteLength(html) < 250_000, 'published HTML should stay small enough to render before player data loads');
assert.match(html, /Player search is ready/);
assert.match(html, /Opening .*finishing the player profile download/);
assert.match(html, /Public research prototype/);
assert.doesNotMatch(html, /<script id="explorer-data" type="application\/json">[A-Za-z0-9+/]{1000}/);

const readGzipJson = filename => JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(site, filename)), { maxOutputLength: 500_000_000 }).toString('utf8'));
const data = readGzipJson('futwar-data.json.gz');
const search = readGzipJson('futwar-search.json.gz');
assert.equal(data.records.length, 22418);
assert.ok(search.groups.length > 5000 && search.groups.length < data.records.length);
assert.ok(data.images.length > 100);
for (const asset of data.images) {
  assert.ok(asset.site_url, `${asset.kind}/${asset.label} should have a published asset path`);
  assert.ok(!asset.data_url, `${asset.kind}/${asset.label} should not inflate the main JSON with base64`);
  assert.ok(fs.existsSync(path.join(site, asset.site_url)), `${asset.site_url} should exist`);
}
for (const label of ['light', 'dark']) {
  const logo = data.images.find(asset => asset.kind === 'brand' && asset.label === label);
  assert.ok(logo, `user supplied ${label} logo should be bundled`);
  assert.match(html, new RegExp(`brand-${label}`));
}
const groups = new Map(search.groups.map(group => [group.id, group.rows]));
assert.equal(core.searchGroups(groups, 'modric').matches.length, 1, 'Modric should resolve to one profile group');
assert.equal(core.searchGroups(groups, 'dybala').matches.length, 1, 'Dybala should resolve to one profile group');
console.log(`Passed: ${data.records.length.toLocaleString()} records, ${search.groups.length.toLocaleString()} searchable profiles, ${data.images.length} external images, user logos, and unique Modric/Dybala search.`);
