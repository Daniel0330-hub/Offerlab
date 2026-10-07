#!/usr/bin/env python3
"""Tune and evaluate profile-to-JD matching on real corpus records."""

import itertools, json, math, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JOBS=json.loads((ROOT/'data/catalog/job-candidate-catalog-v1.1.json').read_text())['jobs']
CASES=json.loads((ROOT/'data/evaluation/profile-job-cases-v1.0.json').read_text())
OUT=ROOT/'data/evaluation/profile-job-matching-results-v1.0.json'
CONFIG=ROOT/'data/evaluation/profile-matching-config-v1.0.json'

SYN=[{'ai','人工智能','算法','机器学习','深度学习','大模型'},{'产品','需求','需求分析','用户研究','解决方案'},{'开发','研发','软件开发','系统开发'},{'运维','运行维护','故障处理'},{'安全','网络安全','信息安全','攻防'},{'数据分析','统计分析','经营分析'},{'数据平台','大数据平台','数据库','数据开发'}]
def text(j):
 return ' '.join([j.get('title',''),j.get('job_family','')]+[str(x.get(k,'')) for x in j.get('responsibilities',[]) for k in ('normalized_label','evidence_span')]+[str(x.get(k,'')) for x in j.get('skills',[]) for k in ('raw_name','normalized_name','evidence_span')]+[str(x.get(k,'')) for x in j.get('base_requirements',[]) for k in ('value','evidence_span')]).lower()
TEXT={j['job_id']:text(j) for j in JOBS}
def forms(term):
 t=term.lower(); out={t}
 for g in SYN:
  if t in g: out|={x.lower() for x in g}
 return out
def cov(terms,hay): return sum(any(x in hay for x in forms(t)) for t in terms)/len(terms) if terms else 0
def components(p,j):
 hay=TEXT[j['job_id']]; title=j['title'].lower(); duties=' '.join(x.get('evidence_span','') for x in j.get('responsibilities',[])).lower(); skills=' '.join(x.get('evidence_span','')+' '+x.get('normalized_name','') for x in j.get('skills',[])).lower(); domain=' '.join(str(x.get('evidence_span',''))+' '+str(x.get('value','')) for x in j.get('base_requirements',[])).lower()
 direction=.75*cov(p['directions'],duties+' '+title)+.25*cov(p['directions'],domain)
 skill=.65*cov(p['skills'],skills+' '+duties)+.35*cov(p['skills'],title)
 exp_terms=[x for x in re.split(r'[、,，;；\s]+',p['experience']) if len(x)>=2]
 experience=cov(exp_terms,duties+' '+skills)
 major=cov(p['majors'],domain+' '+duties+' '+title)
 location=1 if any(a in ' '.join(j.get('locations',[])) for a in p['locations']) else 0
 return direction,skill,experience,major,location
def relevant(p,j): return j.get('job_family') in p['relevant_families'] and any(s.lower() in TEXT[j['job_id']] for s in p['relevant_signals'])
def rank(p,w): return sorted(JOBS,key=lambda j:sum(a*b for a,b in zip(components(p,j),w)),reverse=True)
def metrics(cases,w,k=10):
 recalls=[];ndcgs=[];rr=[]
 for p in cases:
  gold={j['job_id'] for j in JOBS if relevant(p,j)}; ranked=rank(p,w)[:k]; hits=[1 if j['job_id'] in gold else 0 for j in ranked]
  recalls.append(sum(hits)/min(k,len(gold)) if gold else 0)
  dcg=sum(h/math.log2(i+2) for i,h in enumerate(hits)); ideal=sum(1/math.log2(i+2) for i in range(min(k,len(gold))))
  ndcgs.append(dcg/ideal if ideal else 0); rr.append(next((1/(i+1) for i,h in enumerate(hits) if h),0))
 return {'recall_at_10':sum(recalls)/len(recalls),'ndcg_at_10':sum(ndcgs)/len(ndcgs),'mrr_at_10':sum(rr)/len(rr)}

candidates=[]
for d in (.25,.30,.35,.40):
 for s in (.25,.30,.35,.40):
  for e in (.10,.15):
   for m in (.10,.15,.20):
    l=round(1-d-s-e-m,2)
    if l in (0,.05,.10):
     w=(d,s,e,m,l); met=metrics(CASES['development'],w);candidates.append((met['ndcg_at_10'],met['recall_at_10'],w,met))
best=max(candidates,key=lambda x:(x[0],x[1])); w=best[2]
dev=best[3]; test=metrics(CASES['test'],w)
# Sensitivity: changing a profile from data analysis to software development should materially change top 10.
a=CASES['development'][0];b=CASES['development'][2]
ta={j['job_id'] for j in rank(a,w)[:10]};tb={j['job_id'] for j in rank(b,w)[:10]};overlap=len(ta&tb)/10
payload={'version':'1.0','corpus_jobs':len(JOBS),'development_profiles':len(CASES['development']),'test_profiles':len(CASES['test']),'weights':dict(zip(['directions','skills','experience','majors','locations'],w)),'development_metrics':dev,'test_metrics':test,'profile_change_top10_overlap':overlap,'profile_change_pass':overlap<=0.5,'limitations':['相关性标签由岗位族和人工核心信号共同定义，仍需真实用户标注复核','当前语料仅覆盖18家集团','简历文件实验版只直接解析TXT/MD/JSON']}
OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');CONFIG.write_text(json.dumps({'version':'1.0','weights':payload['weights'],'tuned_on':'profile-job-cases-v1.0 development','frozen_test':'profile-job-cases-v1.0 test'},ensure_ascii=False,indent=2)+'\n');print(json.dumps(payload,ensure_ascii=False,indent=2))
