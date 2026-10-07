#!/usr/bin/env python3
"""Build the user catalog and expanded corpus with a 50-record cap per parent group."""
import json
import re
from collections import defaultdict, deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/catalog/job-candidate-catalog-v1.0.json'
OUT=ROOT/'data/catalog/job-candidate-catalog-v1.1.json'
CORPUS=ROOT/'data/corpus/job-corpus-expanded-v1.0.json'
CAP=50
PRODUCT_QUOTA=32
PRODUCT_TITLE=re.compile(r'产品经理|产品管理|产品规划|产品运营')

def quality(j):
    return (min(len(j.get('responsibilities',[])),6)*4 + min(len(j.get('skills',[])),6)*3
            + min(len(j.get('base_requirements',[])),3)*2 + (5 if j.get('source',{}).get('url') else 0))

def stratified(group,limit):
    families=defaultdict(list)
    for j in group: families[j.get('job_family') or '其他方向'].append(j)
    for xs in families.values(): xs.sort(key=lambda j:(-quality(j),j.get('title',''),j.get('job_id','')))
    queues=deque(sorted(((k,deque(v)) for k,v in families.items()),key=lambda kv:(-len(kv[1]),kv[0])))
    result=[]
    while queues and len(result)<limit:
        family,q=queues.popleft(); result.append(q.popleft())
        if q: queues.append((family,q))
    return result

def capped(group):
    # 产品岗在完整目录中数量充足，但容易被大集团的开发岗位挤出50条展示上限。
    # 先按JD完整度保留明确的产品经理/管理/规划/运营岗位，再用岗位族分层补齐。
    ranked_product=sorted((j for j in group if PRODUCT_TITLE.search(j.get('title',''))),
                          key=lambda j:(-quality(j),j.get('title',''),j.get('job_id','')))
    unique_product=[]; duplicates=[]; seen=set()
    for j in ranked_product:
        key=(j.get('title',''),j.get('company',''),tuple(j.get('locations',[])))
        (duplicates if key in seen else unique_product).append(j);seen.add(key)
    product=(unique_product+duplicates)[:PRODUCT_QUOTA]
    chosen_ids={j.get('job_id') for j in product}
    remainder=[j for j in group if j.get('job_id') not in chosen_ids]
    return product+stratified(remainder,CAP-len(product))

def main():
    source=json.loads(SOURCE.read_text()); groups=defaultdict(list)
    for j in source['jobs']:groups[j['parent_group']].append(j)
    jobs=[]; selection=[]
    for name in sorted(groups):
        chosen=capped(groups[name]); jobs.extend(chosen)
        selection.append({'parent_group':name,'available_relevant':len(groups[name]),'selected':len(chosen),'cap':CAP,
                          'truncated':len(groups[name])>CAP,'families':sorted({x.get('job_family','其他方向') for x in chosen})})
    out={'catalog_version':'1.2','purpose':'User-facing catalog and expanded corpus','selection_policy':'product_reserved_then_stratified_quality_cap_50_per_parent_group',
         'jobs':jobs,'coverage':{'job_count':len(jobs),'parent_group_count':len(groups),'cap_per_parent_group':CAP,'selection':selection}}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)); CORPUS.write_text(json.dumps(jobs,ensure_ascii=False,indent=2))
    config=json.loads((ROOT/'data/evaluation/retrieval-config-v1.1.json').read_text())
    (ROOT/'prototype/jobs-data.js').write_text('window.OFFERLAB_DATA = '+json.dumps({'jobs':jobs,'retrievalConfig':config},ensure_ascii=False,separators=(',',':'))+';\n')
    print(json.dumps({'records':len(jobs),'groups':len(groups),'max_group':max(len([j for j in jobs if j['parent_group']==g]) for g in groups)},ensure_ascii=False))
if __name__=='__main__':main()
