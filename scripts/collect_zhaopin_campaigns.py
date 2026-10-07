#!/usr/bin/env python3
"""Unbounded full-campaign collector for official Zhaopin-hosted SOE sites."""
import json, ssl, urllib.request
from datetime import date
from pathlib import Path
from collect_unicom_full_catalog import API, normalize

ROOT=Path(__file__).resolve().parents[1]

def fetch(cfg,page):
    payload={"pageIndex":page,"pageSize":1000,"orgNumbers":[cfg['org_number']],"jobSource":2,
             "orgDepartmentIds":[],"workRegionIds":"","jobTypes":"","priorityMajors":"","customTags":[]}
    req=urllib.request.Request(API,data=json.dumps(payload).encode(),headers={
        'Content-Type':'application/json','Origin':cfg['origin'],'Referer':cfg['referer'],'User-Agent':'Mozilla/5.0 JobLab research collector'})
    with urllib.request.urlopen(req,context=ssl._create_unverified_context(),timeout=60) as r:return json.load(r)

def main():
    configs=json.loads((ROOT/'data/sources/zhaopin-official-campaigns-v1.0.json').read_text())['campaigns']; summary=[]
    for cfg in configs:
        if cfg['key']=='unicom' and (ROOT/'data/catalog/china-unicom-2027-relevant-jobs-v1.0.json').exists():
            d=json.loads((ROOT/'data/catalog/china-unicom-2027-relevant-jobs-v1.0.json').read_text())
            summary.append({'key':'unicom','source_total':d['source_total'],'selected_total':d['selected_total'],'reused':True}); continue
        first=fetch(cfg,1); info=first['data']['pageInfo']; records=list(first['data']['jobList'])
        for page in range(2,info['totalPage']+1): records.extend(fetch(cfg,page)['data']['jobList'])
        raw={'source':cfg['referer'],'collected_at':date.today().isoformat(),'reported_total':info['totalNum'],'records':records}
        raw_path=ROOT/f"data/sources/raw/{cfg['key']}-official-jobs.json"; raw_path.parent.mkdir(parents=True,exist_ok=True)
        raw_path.write_text(json.dumps(raw,ensure_ascii=False,indent=2))
        jobs=[j for item in records if (j:=normalize(item,cfg['parent_group'],cfg['key'],cfg['campaign']))]
        jobs=list({j['job_id']:j for j in jobs}.values())
        out={'catalog_version':'1.0','scope':cfg['campaign'],'source_total':len(records),'selected_total':len(jobs),'jobs':jobs}
        out_path=ROOT/f"data/catalog/{cfg['key']}-relevant-jobs-v1.0.json"; out_path.parent.mkdir(parents=True,exist_ok=True)
        out_path.write_text(json.dumps(out,ensure_ascii=False,indent=2))
        summary.append({'key':cfg['key'],'source_total':len(records),'selected_total':len(jobs),'reused':False})
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
