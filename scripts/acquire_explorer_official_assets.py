"""Archive a directly offered official club mark for the private website."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from acquire_open_data_catalog import get

ROOT=Path(__file__).resolve().parents[1]
def main():
    manifest=ROOT/'data/explorer_official_assets.json'
    if manifest.exists():
        data=json.loads(manifest.read_text(encoding='utf-8'))
        for a in data['assets']:
            if hashlib.sha256((ROOT/a['path']).read_bytes()).hexdigest()!=a['sha256']:raise ValueError('Official asset changed')
        print('Official asset hashes verified');return
    url='https://www.juventus.com/images/image/private/t_editorial_squared_8/f_png/dev/kxdpfwas1r2teqiyoeuq.png'
    raw=get(url);p=ROOT/'data/raw/explorer_assets/2026-10-10/clubs/juventus-official.png'
    if not raw.startswith(b'\x89PNG'):raise ValueError('Expected official PNG asset')
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as h:h.write(raw)
    data=dict(assets=[dict(id='juventus-official',kind='club',label='Juventus',title='Juventus official J Icon',
         source_page='https://www.juventus.com/en/club/logo',source_url=url,path=p.relative_to(ROOT).as_posix(),
         sha256=hashlib.sha256(raw).hexdigest(),retrieved_at_utc=datetime.now(timezone.utc).isoformat(),artist='Juventus Football Club',
         license='Rights retained by Juventus; private factual illustration; no open redistribution license verified',
         historical_season_accuracy='Current official J Icon; 2017-20 used an additional Juventus wordmark. Illustrative edition, not promised to match every season.')])
    manifest.write_text(json.dumps(data,indent=2),encoding='utf-8');print('Archived official Juventus mark')
if __name__=='__main__':main()
