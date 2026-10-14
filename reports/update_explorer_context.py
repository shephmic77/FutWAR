from pathlib import Path
p=Path('profile/explorer.html')
s=p.read_text(encoding='utf-8')
s=s.replace('<h2>Coverage by league & season</h2>','<div class="panel-head"><h2>Coverage by league & season</h2><button id="download-coverage">All-statistic coverage CSV</button></div>')
p.write_text(s,encoding='utf-8')
p=Path('profile/explorer.js')
s=p.read_text(encoding='utf-8').replace('initPeriod();initMetrics();',"$('download-coverage').onclick=()=>download('futwar-all-statistic-coverage.csv',csv(data.fieldCoverage),'text/csv;charset=utf-8');\ninitPeriod();initMetrics();")
p.write_text(s,encoding='utf-8')
for file,text in [('README.md','The [full-scope private explorer and data audit](docs/full_explorer_data_audit.md) exposes all 22,418 source records, dated June 30 market values, keeper overlays, comparisons and original-field coverage. Rebuild with `py scripts/build_explorer_dataset.py` then `py scripts/package_explorer.py`; open `reports/explorer/FutWAR_Explorer.html`. Missing images, injuries and historical roles remain explicit. Source checks do not certify every statistic.'),('docs/data_sources.md','The [full explorer data audit](full_explorer_data_audit.md) documents the archived publisher valuation table, owner-selected June 30 cutoff, separate keeper overlays and image credits. The new Kaggle injury research archive is anonymized and was excluded from named-profile merging. Original statistics and unresolved upstream rights are preserved.')]:
    p=Path(file)
    p.write_text(p.read_text(encoding='utf-8')+'\n'+text+'\n',encoding='utf-8')
