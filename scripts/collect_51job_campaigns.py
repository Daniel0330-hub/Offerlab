#!/usr/bin/env python3
"""Collect all relevant jobs from official 51job-hosted SOE campaigns without per-company caps."""
import concurrent.futures, hashlib, html, json, os, re, ssl, urllib.parse, urllib.request
from datetime import date
from pathlib import Path
from collect_unicom_full_catalog import family_for, clean_lines, extract_skills

ROOT=Path(__file__).resolve().parents[1]
SECRET=os.environ.get('JOB51_COAPI_SECRET','')
CTX=ssl._create_unverified_context()

def call(endpoint,params,referer):
    if not SECRET:
        raise RuntimeError('JOB51_COAPI_SECRET is required for optional 51job collection; the checked-in demo does not need it.')
    raw=json.dumps(params,separators=(',',':'),ensure_ascii=False); idx=1
    sign=hashlib.md5(('coapi'+raw+SECRET[idx:idx+15]).encode()).hexdigest()
    url='https://coapi.51job.com/'+endpoint+'?'+urllib.parse.urlencode({'key':idx,'sign':sign,'params':raw})
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 JobLab research collector','Referer':referer})
    text=urllib.request.urlopen(req,context=CTX,timeout=45).read().decode('utf-8','replace')
    return json.loads(text[text.index('(')+1:text.rindex(')')])['resultbody']

def normalize(row,detail,cfg):
    info=detail.get('jobinfo','') or ''
    family,reasons=family_for(row.get('jobname',''),info)
    if not family:return None
    lines=clean_lines(info); duties=[x for x in lines if not re.search(r'学历|专业|任职|要求',x)] or lines
    reqs=[x for x in lines if re.search(r'学历|专业|任职|要求',x)]
    base=[{'criterion':'graduation_year','operator':'equals','value':2027,'requirement_level':'required','evidence_span':cfg['campaign']}]
    degree=row.get('degreefrom')
    if degree and degree!='不限':
        value='硕士研究生' if '硕士' in degree else '博士研究生' if '博士' in degree else degree
        base.append({'criterion':'degree','operator':'minimum','value':value,'requirement_level':'required','evidence_span':'学历要求：'+degree})
    return {'job_id':f"{cfg['key']}-51job-{row['jobid']}",'title':row.get('jobname',''),'company':row.get('coname') or cfg['parent_group'],
      'parent_group':cfg['parent_group'],'locations':[row.get('jobareaname') or '地点未明确'],'recruitment_type':'campus','graduation_years':[2027],
      'job_family':family,'responsibilities':[{'normalized_label':x[:18],'evidence_span':x} for x in duties[:10]],
      'skills':extract_skills(duties,reqs),'base_requirements':base,'other_explicit_conditions':[],
      'source':{'url':f"https://xyz.51job.com/external/apply.aspx?jobid={row['jobid']}&ctmid={cfg['ctmid']}",'collected_at':date.today().isoformat(),'job_number':row['jobid'],'official_campaign':cfg['campaign']},
      'catalog_selection':{'method':'title_first_taxonomy_v1','matched_signals':reasons}}

def main():
    configs=json.loads((ROOT/'data/sources/51job-official-campaigns-v1.0.json').read_text())['campaigns']; summary=[]
    for cfg in configs:
        rows=call('job_list.php',{'ctmid':cfg['ctmid'],'pagesize':10000,'coid':'','keyword':'','jobarea':''},cfg['referer'])['joblist']
        # Fetch every detail so generic titles can still be classified from JD evidence.
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            details=list(ex.map(lambda r:call('job_detail.php',{'jobid':r['jobid']},cfg['referer']),rows))
        raw={'source':cfg['referer'],'collected_at':date.today().isoformat(),'reported_total':len(rows),'records':[{'list':r,'detail':d} for r,d in zip(rows,details)]}
        p=ROOT/f"data/sources/raw/{cfg['key']}-official-jobs.json";p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(raw,ensure_ascii=False,indent=2))
        jobs=[j for r,d in zip(rows,details) if (j:=normalize(r,d,cfg))]
        out={'catalog_version':'1.0','scope':cfg['campaign'],'source_total':len(rows),'selected_total':len(jobs),'jobs':jobs}
        (ROOT/f"data/catalog/{cfg['key']}-relevant-jobs-v1.0.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
        summary.append({'key':cfg['key'],'source_total':len(rows),'selected_total':len(jobs)})
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
