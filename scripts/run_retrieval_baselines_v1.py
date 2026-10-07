#!/usr/bin/env python3
"""Run transparent retrieval baselines on the group-held-out development set."""
from __future__ import annotations
import json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JOBS=ROOT/'data/evaluation/development-set-v1.0.json'
QUERIES=ROOT/'data/evaluation/retrieval-queries-v1.0.json'
OUTPUT=ROOT/'data/evaluation/retrieval-results-v1.0.json'

def text(items,*keys):return ' '.join(str(item.get(k,'')) for item in items for k in keys).lower()
def coverage(terms,corpus):return sum(t.lower() in corpus for t in terms)/len(terms) if terms else 0.0
def corpora(job):return {'title':job['title'].lower(),'responsibility':text(job['responsibilities'],'normalized_label','evidence_span'),'skill':text(job['skills'],'raw_name','normalized_name','evidence_span'),'domain':text(job['base_requirements'],'value','evidence_span')}
def scores(job,terms):
 c=corpora(job);t=coverage(terms,c['title']);s=coverage(terms,c['skill']);r=coverage(terms,c['responsibility']);d=coverage(terms,c['domain'])
 return {'title_only':t,'title_skill':.4*t+.6*s,'offerlab_hybrid':.4*r+.35*s+.15*d+.1*t}
def recall(ranking,relevant,k):return len(set(ranking[:k])&relevant)/len(relevant) if relevant else 0
def ndcg(ranking,relevant,k):
 dcg=sum((1 if x in relevant else 0)/math.log2(i+2) for i,x in enumerate(ranking[:k])); ideal=sum(1/math.log2(i+2) for i in range(min(k,len(relevant))))
 return dcg/ideal if ideal else 0
def main():
 jobs=json.loads(JOBS.read_text());queries=json.loads(QUERIES.read_text());methods=['title_only','title_skill','offerlab_hybrid']; totals={m:{'r5':[],'r10':[],'n5':[]} for m in methods};out={'dataset':JOBS.name,'queries':[],'summary':{}}
 for q in queries:
  ranked={m:[] for m in methods}
  for job in jobs:
   for m,score in scores(job,q['terms']).items():ranked[m].append((job['job_id'],round(score,4)))
  relevant=set(q['relevant_job_ids']); qr={'query_id':q['query_id'],'query':q['query'],'relevant_count':len(relevant),'methods':{}}
  for m in methods:
   ordered=[x for x in sorted(ranked[m],key=lambda x:(-x[1],x[0])) if x[1]>0];ids=[x[0] for x in ordered]
   vals={'recall_at_5':round(recall(ids,relevant,5),4),'recall_at_10':round(recall(ids,relevant,10),4),'ndcg_at_5':round(ndcg(ids,relevant,5),4),'top_5':ordered[:5]}
   qr['methods'][m]=vals;totals[m]['r5'].append(vals['recall_at_5']);totals[m]['r10'].append(vals['recall_at_10']);totals[m]['n5'].append(vals['ndcg_at_5'])
  out['queries'].append(qr)
 for m,v in totals.items():out['summary'][m]={'mean_recall_at_5':round(sum(v['r5'])/len(v['r5']),4),'mean_recall_at_10':round(sum(v['r10'])/len(v['r10']),4),'mean_ndcg_at_5':round(sum(v['n5'])/len(v['n5']),4)}
 OUTPUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 for m,v in out['summary'].items():print(m,v)
if __name__=='__main__':main()
