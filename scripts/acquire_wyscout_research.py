"""Archive the CC BY 4.0 Figshare research release without modifying raw files."""
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'data/wyscout_research_manifest.json'
FOLDER = ROOT / 'data/raw/wyscout_research/2026-10-10'
ARTICLES = [7765196, 7765316, 7770422, 7770599, 11743836, 11743818]


def get(url, limit=100_000_000):
    request = urllib.request.Request(url, headers={'User-Agent': 'FutWAR/0.1 research data audit'})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read(limit + 1)
    if len(payload) > limit:
        raise ValueError('Download size guard exceeded')
    return payload


def main():
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    else:
        manifest = dict(provider='Wyscout research release via Pappalardo/Massucco Figshare',
                        collection_url='https://figshare.com/collections/Soccer_match_event_dataset/4415000',
                        citation='Pappalardo et al. (2019), doi:10.1038/s41597-019-0247-7',
                        purpose='Historical position and goalkeeper source audit; no modeling or merge',
                        articles=[], files=[])
    FOLDER.mkdir(parents=True, exist_ok=True)
    for article_id in ARTICLES:
        registered = next((a for a in manifest['articles'] if a['id'] == article_id), None)
        if registered:
            payload = (ROOT / registered['metadata_path']).read_bytes()
            if hashlib.sha256(payload).hexdigest() != registered['metadata_sha256']:
                raise ValueError('Registered metadata changed')
            metadata = json.loads(payload)
        else:
            payload = get(f'https://api.figshare.com/v2/articles/{article_id}', 1_000_000)
            metadata = json.loads(payload)
            if metadata['license']['name'] != 'CC BY 4.0':
                raise ValueError('Unreviewed article license')
            path = FOLDER / f'article_{article_id}_v{metadata["version"]}.json'
            with path.open('xb') as handle:
                handle.write(payload)
            manifest['articles'].append(dict(id=article_id, version=metadata['version'],
                title=metadata['title'], license=metadata['license'],
                metadata_path=path.relative_to(ROOT).as_posix(),
                metadata_sha256=hashlib.sha256(payload).hexdigest(),
                retrieved_at_utc=datetime.now(timezone.utc).isoformat()))
            MANIFEST.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        for source in metadata['files']:
            registered_file = next((f for f in manifest['files'] if f['id'] == source['id']), None)
            if registered_file:
                if hashlib.sha256((ROOT / registered_file['path']).read_bytes()).hexdigest() != registered_file['sha256']:
                    raise ValueError('Registered data changed')
                continue
            if Path(source['name']).name != source['name'] or source['is_link_only']:
                raise ValueError('Unexpected source filename or external link')
            path = FOLDER / source['name']
            if path.exists():
                raise ValueError('Unregistered file exists')
            payload = get(source['download_url'])
            if len(payload) != source['size'] or hashlib.md5(payload).hexdigest() != source['computed_md5']:
                raise ValueError('Publisher size/checksum mismatch')
            with path.open('xb') as handle:
                handle.write(payload)
            manifest['files'].append(dict(id=source['id'], article_id=article_id,
                path=path.relative_to(ROOT).as_posix(), source_url=source['download_url'],
                bytes=len(payload), publisher_md5=source['computed_md5'],
                sha256=hashlib.sha256(payload).hexdigest(),
                retrieved_at_utc=datetime.now(timezone.utc).isoformat()))
            MANIFEST.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
            print(source['name'] + ': archived', flush=True)


if __name__ == '__main__':
    main()
