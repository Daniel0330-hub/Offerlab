#!/usr/bin/env python3
"""Compare low-cost retrieval variants on development data only."""
from __future__ import annotations
import json, math, re
from collections import Counter
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
TRAIN=ROOT/'data/evaluation/train-set-v1.0.json'; DEV=ROOT/'data/evaluation/development-set-v1.1.json'; QUERY_FILES=[ROOT/'data/evaluation/retrieval-queries-v1.1.json',ROOT/'data/evaluation/retrieval-queries-paraphrase-v1.1.json']; OUT=ROOT/'data/evaluation/development-tuning-results-v1.1.json'

SYNONYM_GROUPS=[
 {'ai','人工智能','智能算法','机器学习','深度学习','大模型'}, {'大模型','llm','语言模型','生成式ai'}, {'智能体','agent','多智能体'},
 {'需求','用户需求','客户需求','需求调研','需求分析','需求沟通'}, {'方案','解决方案','产品方案','技术方案'}, {'交付','实施','落地','上线','验收'},
 {'运维','运营维护','运行维护','巡检','故障处理'}, {'网络安全','信息安全','安全','攻防','渗透测试'}, {'数据治理','数据质量','元数据','数据标准'},
 {'数据中台','大数据平台','数据平台'}, {'算法','模型','机器学习','深度学习'}, {'部署','工程化','产品化','落地'}, {'项目','项目管理','项目实施'},
 {'计算机视觉','图像识别','视觉算法','cv'}, {'研发','开发','研制'},
 {'新媒体','内容运营','社交媒体','全媒体'}, {'私域','会员运营','用户运营','社群运营'},
 {'用户分层','用户画像','读者标签'}, {'舆情监测','热点挖掘','账号诊断'},
 {'音视频','媒体制作','视频剪辑','后期制作'}, {'数据库','行业数据库','数据整理'},
 {'物联网','aiot','智能终端','智能设备'}, {'系统运维','信息系统运维','运行维护'},
 {'rag','知识库','知识库问答','检索增强'}, {'任务编排','任务规划','agent','智能体'},
]

def flat_value(v): return ' '.join(map(str,v)) if isinstance(v,list) else str(v)
def job_fields(j):
 def txt(items,*keys):return ' '.join(flat_value(x.get(k,'')) for x in items for k in keys).lower()
 return {'title':j['title'].lower(),'responsibility':txt(j['responsibilities'],'normalized_label','evidence_span'),'skill':txt(j['skills'],'raw_name','normalized_name','evidence_span'),'domain':txt(j['base_requirements'],'value','evidence_span')}
def expand(term):
 t=term.lower(); out={t}
 for g in SYNONYM_GROUPS:
  low={x.lower() for x in g}
  if t in low: out|=low
 return out
def coverage(terms,corpus,syn=False):return sum(any(x in corpus for x in (expand(t) if syn else {t.lower()})) for t in terms)/len(terms)
def lexical(j,terms,syn=False):
 c=job_fields(j);t=coverage(terms,c['title'],syn);s=coverage(terms,c['skill'],syn);r=coverage(terms,c['responsibility'],syn);d=coverage(terms,c['domain'],syn)
 return .4*r+.35*s+.15*d+.1*t
def fulltext(j):
 c=job_fields(j);return ' '.join(c.values())
def grams(text):
 text=re.sub(r'\s+','',text.lower()); chinese=''.join(re.findall(r'[\u4e00-\u9fff]',text)); tokens=[]
 for n in (2,3,4):tokens += [chinese[i:i+n] for i in range(max(0,len(chinese)-n+1))]
 tokens += re.findall(r'[a-z][a-z0-9+#./-]*',text)
 return Counter(tokens)
def idf_from_train(train):
 docs=[set(grams(fulltext(j))) for j in train];df=Counter(x for d in docs for x in d);n=len(docs)
 return {x:math.log((n+1)/(v+1))+1 for x,v in df.items()},n
def vector(counter,idf,n):
 return {x:(1+math.log(v))*(idf.get(x,math.log((n+1)/1)+1)) for x,v in counter.items()}
def cosine(a,b):
 common=set(a)&set(b);num=sum(a[x]*b[x] for x in common);da=math.sqrt(sum(v*v for v in a.values()));db=math.sqrt(sum(v*v for v in b.values()));return num/(da*db) if da and db else 0
def recall(ids,rel,k):return len(set(ids[:k])&rel)/len(rel) if rel else 0
def ndcg(ids,rel,k):
 dcg=sum((x in rel)/math.log2(i+2) for i,x in enumerate(ids[:k]));ideal=sum(1/math.log2(i+2) for i in range(min(k,len(rel))));return dcg/ideal if ideal else 0

def main():
 train=json.loads(TRAIN.read_text());dev=json.loads(DEV.read_text());queries=sum((json.loads(p.read_text()) for p in QUERY_FILES),[]);idf,n=idf_from_train(train)
 methods=['offerlab_hybrid','synonym_hybrid','char_tfidf','ensemble_70_30','ensemble_50_50','ensemble_30_70','two_stage_30_70'];tot={m:{'r5':[],'r10':[],'n5':[]} for m in methods};out={'dataset':DEV.name,'training_source':TRAIN.name,'test_set_used':False,'synonym_groups':[sorted(g) for g in SYNONYM_GROUPS],'queries':[],'summary':{}}
 docvec={j['job_id']:vector(grams(fulltext(j)),idf,n) for j in dev}
 for q in queries:
  qv=vector(grams(q['query']),idf,n); ranked={m:[] for m in methods}
  for j in dev:
   base=lexical(j,q['terms']);syn=lexical(j,q['terms'],True);vec=cosine(qv,docvec[j['job_id']]);scores={'offerlab_hybrid':base,'synonym_hybrid':syn,'char_tfidf':vec,'ensemble_70_30':.7*syn+.3*vec,'ensemble_50_50':.5*syn+.5*vec,'ensemble_30_70':.3*syn+.7*vec}
   for m,s in scores.items():ranked[m].append((j['job_id'],round(s,6)))
  candidate_ids={x[0] for x in sorted(ranked['char_tfidf'],key=lambda z:(-z[1],z[0]))[:10]}
  ranked['two_stage_30_70']=[x for x in ranked['ensemble_30_70'] if x[0] in candidate_ids]
  rel=set(q['relevant_job_ids']);qr={'query_id':q['query_id'],'methods':{}}
  for m in methods:
   ordered=[x for x in sorted(ranked[m],key=lambda z:(-z[1],z[0])) if x[1]>0];ids=[x[0] for x in ordered];vals={'recall_at_5':round(recall(ids,rel,5),4),'recall_at_10':round(recall(ids,rel,10),4),'ndcg_at_5':round(ndcg(ids,rel,5),4),'top_5':ordered[:5]};qr['methods'][m]=vals
   for key,short in [('recall_at_5','r5'),('recall_at_10','r10'),('ndcg_at_5','n5')]:tot[m][short].append(vals[key])
  out['queries'].append(qr)
 for m,v in tot.items():out['summary'][m]={'mean_recall_at_5':round(float(np.mean(v['r5'])),4),'mean_recall_at_10':round(float(np.mean(v['r10'])),4),'mean_ndcg_at_5':round(float(np.mean(v['n5'])),4)}
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out['summary'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
