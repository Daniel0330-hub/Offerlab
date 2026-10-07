#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[1]
base=json.loads((ROOT/'data/sources/central-soe-universe-v0.1.json').read_text())
extra=json.loads((ROOT/'data/sources/expanded-central-enterprise-candidates-v0.1.json').read_text())
old=[]
for p in ['central-soe-2027-source-audit-v0.1.json','expanded-enterprise-2027-source-audit-v0.1.json']:
 old+=json.loads((ROOT/'data/sources'/p).read_text())['records']
oldmap={x['parent_group']:x for x in old}
names={x['name'] for x in base['enterprises']}; names.update(x['canonical_name'] for x in extra['records'])
keys={'中国联合网络通信集团有限公司':'unicom','中国船舶集团有限公司':'cssc','国家开发银行':'cdb','中国信息通信科技集团有限公司':'cict','中国航天科工集团有限公司':'casic','中国电气装备集团有限公司':'xidian'}
rows=[]
for name in sorted(names):
 x=oldmap.get(name,{}); key=keys.get(name); cat=None
 if key:
  p=ROOT/('data/catalog/china-unicom-2027-relevant-jobs-v1.0.json' if key=='unicom' else f'data/catalog/{key}-relevant-jobs-v1.0.json')
  if p.exists():cat=json.loads(p.read_text())
 if cat: status='full_sweep_completed'
 elif x.get('processing_status') in ('no_2027_campaign','no_single_job_detail','reviewed_no_qualified_job'): status=x['processing_status']
 else: status='queued_full_sweep'
 rows.append({'parent_group':name,'status':status,'official_recruitment_url':x.get('official_recruitment_url'),
  'campaign_confirmed':x.get('2027_campaign_confirmed'),'official_total':cat and cat['source_total'],'relevant_selected':cat and cat['selected_total'],
  'old_sample_count':x.get('qualified_job_count',0),'last_reviewed':date.today().isoformat() if cat else x.get('reviewed_at'),'notes':x.get('notes','')})
summary={s:sum(r['status']==s for r in rows) for s in sorted(set(r['status'] for r in rows))}
out={'version':'1.1','updated_at':date.today().isoformat(),'scope_count':len(rows),'policy':'No per-company cap. Full campaign retrieval before relevance filtering.','summary':summary,'enterprises':rows}
(ROOT/'data/sources/full-catalog-coverage-audit-v1.1.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({'scope_count':len(rows),'summary':summary},ensure_ascii=False,indent=2))
