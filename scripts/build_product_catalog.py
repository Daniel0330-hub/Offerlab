#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
corpus=json.loads((ROOT/'data/corpus/job-corpus-v0.1.json').read_text())
full_keys=['unicom','cssc','cdb','cict','casic','xidian']
full=[]; full_groups=set(); source_totals={}; selected_totals={}
for key in full_keys:
    path=ROOT/('data/catalog/china-unicom-2027-relevant-jobs-v1.0.json' if key=='unicom' else f'data/catalog/{key}-relevant-jobs-v1.0.json')
    if not path.exists(): continue
    data=json.loads(path.read_text()); full.extend(data['jobs']); source_totals[key]=data['source_total']; selected_totals[key]=data['selected_total']
    full_groups.update(x['parent_group'] for x in data['jobs'])
# A completed full sweep replaces that group's earlier hand-curated product samples.
other=[x for x in corpus if x.get('parent_group') not in full_groups]
jobs=other+full
out={
 'catalog_version':'1.0',
 'purpose':'User-facing candidate job catalog; separate from frozen evaluation datasets',
 'jobs':jobs,
 'coverage':{'job_count':len(jobs),'parent_group_count':len(set(x.get('parent_group','') for x in jobs)),
             'full_sweep_parent_group_count':len(full_groups),'full_sweep_source_totals':source_totals,
             'full_sweep_selected_totals':selected_totals,'legacy_curated_other_enterprises_count':len(other)}
}
path=ROOT/'data/catalog/job-candidate-catalog-v1.0.json'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2))
config=json.loads((ROOT/'data/evaluation/retrieval-config-v1.1.json').read_text())
(ROOT/'prototype/jobs-data.js').write_text('window.OFFERLAB_DATA = '+json.dumps({'jobs':jobs,'retrievalConfig':config},ensure_ascii=False,separators=(',',':'))+';\n')
print(json.dumps(out['coverage'],ensure_ascii=False,indent=2))
