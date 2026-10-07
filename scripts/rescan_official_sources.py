#!/usr/bin/env python3
"""Revisit every known official recruitment URL and record reproducible access evidence."""
import concurrent.futures, json, re, ssl, urllib.request
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/'data/sources/full-catalog-coverage-audit-v1.1.json'
OUT=ROOT/'data/sources/full-catalog-rescan-v1.2.json'
CTX=ssl._create_unverified_context()

def check(row):
    url=row.get('official_recruitment_url')
    result=dict(row); result['rescanned_at']=datetime.now().astimezone().isoformat(timespec='seconds')
    if not url:
        result.update({'rescan_result':'no_official_url_in_registry','http_status':None,'mentions_2027':None}); return result
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 JobLab source audit'})
        with urllib.request.urlopen(req,context=CTX,timeout=30) as r:
            body=r.read(2_000_000).decode('utf-8','ignore'); status=r.status; final=r.geturl()
        result.update({'rescan_result':'reachable','http_status':status,'final_url':final,
                       'mentions_2027':bool(re.search(r'2027|2027届|二〇二七',body)),
                       'page_bytes_checked':len(body.encode())})
    except Exception as e:
        result.update({'rescan_result':'access_failed','http_status':None,'mentions_2027':None,'error':type(e).__name__+': '+str(e)[:240]})
    return result

def main():
    src=json.loads(IN.read_text()); rows=src['enterprises']
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex: checked=list(ex.map(check,rows))
    summary={k:sum(x['rescan_result']==k for x in checked) for k in sorted(set(x['rescan_result'] for x in checked))}
    out={'version':'1.2','scope_count':len(checked),'policy':'All known official URLs revisited; missing URLs remain explicit and are not treated as no jobs.','summary':summary,'enterprises':checked}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
