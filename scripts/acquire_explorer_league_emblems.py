"""Archive official league artwork; retain raw bytes and display provenance."""
import hashlib
import json
import re
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    assets=[]
    for label,url,page,filename in [
        ('Premier League','https://www.premierleague.com/resources/v1.54.15/i/svg-files/elements/pl-logo-light.svg','https://www.premierleague.com/en','premier-league.svg'),
        ('La Liga','https://assets.laliga.com/assets/public/logos/favicon.ico','https://www.laliga.com/en-GB','laliga.ico')]:
        raw=urllib.request.urlopen(url,timeout=30).read()
        path=ROOT/'data/raw/explorer_assets/2026-10-10/leagues'/filename;path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            if path.read_bytes()!=raw:raise ValueError('Immutable asset changed')
        else:path.write_bytes(raw)
        display=path
        if label=='Premier League':
            # The official lockup contains a lion at x=0..40 and text at x>=45.
            # Crop its vector viewport only; raw paths and original SVG are kept.
            svg=raw.decode('utf-8')
            svg=re.sub(r'<svg[^>]*>', '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="48" viewBox="0 0 40 48">',svg,count=1)
            display=ROOT/'data/processed/explorer_assets/premier-league-lion.svg';display.parent.mkdir(parents=True,exist_ok=True);display.write_text(svg,encoding='utf-8')
        assets.append(dict(kind='league',label=label,title=label+' official emblem',path=display.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(display.read_bytes()).hexdigest(),raw_path=path.relative_to(ROOT).as_posix(),raw_sha256=hashlib.sha256(raw).hexdigest(),source_url=url,source_page=page,artist=label,license='Rights retained; private research use only; redistribution permission unconfirmed',retrieved_at_utc=datetime.now(timezone.utc).isoformat(),display_changes='Vector viewport limited to lion; no path changes' if label=='Premier League' else 'CSS fit only',historical_accuracy='Current illustrative emblem, not verification of every historical edition'))
    (ROOT/'data/explorer_league_emblems.json').write_text(json.dumps({'assets':assets},indent=2),encoding='utf-8')
    print('Archived two official league emblems with raw/display fingerprints.')

if __name__=='__main__':main()
