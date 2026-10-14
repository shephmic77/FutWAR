"""Archive a public Kaggle research candidate; inspect before any identity merge."""
import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE='https://www.kaggle.com/api/v1/datasets/'
SLUG='gumush/football-player-injuries-market-value'
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FutWAR/0.1 personal research source audit'}),timeout=45) as r:
        raw=r.read(20000001)
    if len(raw)>20000000:raise ValueError('Research candidate exceeds size guard')
    return raw
def main():
    manifest=ROOT/'data/explorer_injury_manifest.json'
    if manifest.exists():
        for item in json.loads(manifest.read_text())['files']:
            if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Archive changed')
        print('Injury candidate archive verified');return
    folder=ROOT/'data/raw/explorer_injuries/2026-10-10';folder.mkdir(parents=True,exist_ok=True)
    files=[]
    def archive(name,raw,url):
        path=folder/name
        with path.open('xb') as h:h.write(raw)
        files.append(dict(filename=name,path=path.relative_to(ROOT).as_posix(),source_url=url,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
    listing=get(BASE+'list/'+SLUG);archive('file_metadata.json',listing,BASE+'list/'+SLUG)
    try:
        card=get(BASE+'view/'+SLUG);archive('dataset_metadata.json',card,BASE+'view/'+SLUG)
    except Exception as error:print('Data card unavailable: '+str(error))
    url=BASE+'download/'+SLUG;raw=get(url);archive('source.zip',raw,url)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name in ('README.md','players.csv','injuries.csv'):
            if name not in z.namelist():raise ValueError('Expected research file missing')
            archive(name,z.read(name),url)
    manifest.write_text(json.dumps(dict(source_page='https://www.kaggle.com/datasets/'+SLUG,retrieved_at_utc=datetime.now(timezone.utc).isoformat(),status='candidate_archive_requires_readme_license_identity_and_coverage_review',redistribution='private only; no automatic upstream permission inferred',files=files),indent=2),encoding='utf-8')
    print('Archived candidate files for review')
    print((folder/'README.md').read_text(encoding='utf-8').encode('ascii','backslashreplace').decode('ascii'))
if __name__=='__main__':main()
