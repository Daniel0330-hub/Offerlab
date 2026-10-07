#!/usr/bin/env python3
import json,collections
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[1]
scan=json.loads((ROOT/'data/sources/full-catalog-rescan-v1.2.json').read_text())
cat=json.loads((ROOT/'data/catalog/job-candidate-catalog-v1.1.json').read_text())
counts=collections.Counter(x['parent_group'] for x in cat['jobs'])
for r in scan['enterprises']:
 r['included_in_capped_corpus']=counts.get(r['parent_group'],0)
 r['cap_compliant']=counts.get(r['parent_group'],0)<=50
 r['verification_basis']='full_campaign_api_scan' if r['status']=='full_sweep_completed' else ('current_official_url_rescan' if r['rescan_result']=='reachable' else 'prior_audit_plus_current_access_attempt')
summary={'scope_count':len(scan['enterprises']),'groups_in_corpus':len(counts),'corpus_records':sum(counts.values()),'max_per_group':max(counts.values()),
 'full_sweep_completed':sum(r['status']=='full_sweep_completed' for r in scan['enterprises']),'official_urls_reachable_now':sum(r['rescan_result']=='reachable' for r in scan['enterprises']),
 'official_urls_access_failed':sum(r['rescan_result']=='access_failed' for r in scan['enterprises']),'missing_official_url_in_registry':sum(r['rescan_result']=='no_official_url_in_registry' for r in scan['enterprises'])}
out={'version':'1.2','updated_at':date.today().isoformat(),'policy':'Maximum 50 selected records per parent group; full raw snapshots retained separately.','summary':summary,'enterprises':scan['enterprises']}
(ROOT/'data/sources/full-catalog-coverage-audit-v1.2.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
