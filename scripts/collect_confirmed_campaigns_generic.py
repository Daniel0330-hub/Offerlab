#!/usr/bin/env python3
"""Best-effort generic collector for confirmed campaigns lacking a platform adapter.

The collector preserves every fetched page and only turns pages with job-role signals
and a relevant product/data/AI/development/operations family into catalog records.
SPA/API-only sites are reported as adapter_required rather than zero jobs.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import html
import json
import re
import ssl
import urllib.parse
import urllib.request
from collections import deque
from datetime import date, datetime
from pathlib import Path

from collect_unicom_full_catalog import clean_lines, extract_skills, family_for

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/sources/enterprise-2027-campaign-verification-v2.1.json"
OUT = ROOT / "data/sources/confirmed-46-acquisition-audit-v1.0.json"
CTX = ssl._create_unverified_context()
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/129 Safari/537.36 JobLab/1.0"
TAG = re.compile(r"<[^>]+>")
HREF = re.compile(r"href\s*=\s*['\"]([^'\"#]+)", re.I)
TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
JOB_LINK = re.compile(r"job|position|detail|campus|xiaoyuan|zhaopin|recruit|career|apply|announcement|anno", re.I)
ROLE = re.compile(r"产品|数据|算法|人工智能|AI|开发|软件|系统|运维|云|安全|测试|研发|信息技术|数字化|统计|模型", re.I)
JOB_CONTEXT = re.compile(r"岗位职责|任职要求|职位描述|招聘岗位|专业要求|工作职责|职位要求|学历要求")
PLATFORM_KEYS = {"中国联合网络通信集团有限公司", "中国船舶集团有限公司", "国家开发银行", "中国信息通信科技集团有限公司", "中国航天科工集团有限公司", "中国电气装备集团有限公司"}


def key_for(name: str) -> str:
    return hashlib.sha1(name.encode()).hexdigest()[:12]


def fetch(url: str) -> tuple[int, str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, context=CTX, timeout=25) as response:
        body = response.read(3_000_000)
        content_type = response.headers.get("Content-Type", "")
        charset = response.headers.get_content_charset() or "utf-8"
        try:
            text = body.decode(charset, "replace")
        except LookupError:
            text = body.decode("utf-8", "replace")
        return response.status, response.geturl(), text if "html" in content_type or "text" in content_type else ""


def page_text(body: str) -> str:
    body = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", body, flags=re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", body))).strip()


def crawl(seed: str, max_pages: int = 40) -> tuple[list[dict], list[dict]]:
    base_host = urllib.parse.urlparse(seed).netloc
    queue = deque([seed])
    seen, pages, errors = set(), [], []
    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        try:
            status, final_url, body = fetch(url)
            text = page_text(body)
            title_match = TITLE.search(body)
            title = page_text(title_match.group(1)) if title_match else ""
            pages.append({"url": final_url, "http_status": status, "title": title, "text": text[:200000], "html_bytes": len(body.encode('utf-8'))})
            for href in HREF.findall(body):
                target = urllib.parse.urljoin(final_url, html.unescape(href))
                parsed = urllib.parse.urlparse(target)
                if parsed.scheme in {"http", "https"} and parsed.netloc == base_host and JOB_LINK.search(target) and target not in seen:
                    queue.append(target)
        except Exception as exc:
            errors.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
    return pages, errors


def normalize_page(name: str, page: dict) -> dict | None:
    text = page["text"]
    title = page["title"] or text[:80]
    if not ROLE.search(title + " " + text[:4000]) or not JOB_CONTEXT.search(text):
        return None
    family, reasons = family_for(title, text)
    if not family:
        return None
    lines = [x for x in clean_lines(text) if 6 <= len(x) <= 260]
    reqs = [x for x in lines if re.search(r"学历|专业|任职|要求|技能|熟悉|掌握", x)]
    duties = [x for x in lines if re.search(r"负责|参与|开展|建设|开发|设计|分析|运营|维护|研究", x)]
    if not duties:
        duties = lines[:8]
    locations = sorted(set(re.findall(r"(?:北京|上海|天津|重庆|广州|深圳|武汉|成都|西安|南京|杭州|合肥|济南|青岛|长沙|郑州|沈阳|哈尔滨|福州|厦门|昆明|南宁|海口|石家庄|太原|长春|兰州|乌鲁木齐|贵阳|南昌|苏州|无锡|宁波)", text[:10000]))) or ["地点未明确"]
    return {
        "job_id": f"generic-{key_for(name + page['url'])}",
        "title": title[:120],
        "company": name,
        "parent_group": name,
        "locations": locations[:8],
        "recruitment_type": "campus",
        "graduation_years": [2027],
        "job_family": family,
        "responsibilities": [{"normalized_label": x[:18], "evidence_span": x} for x in duties[:10]],
        "skills": extract_skills(duties, reqs),
        "base_requirements": [{"criterion": "graduation_year", "operator": "equals", "value": 2027, "requirement_level": "required", "evidence_span": "2027校园招聘"}],
        "other_explicit_conditions": reqs[:8],
        "source": {"url": page["url"], "collected_at": date.today().isoformat(), "official_campaign": "2027校园招聘"},
        "catalog_selection": {"method": "generic_official_page_extraction_v1", "matched_signals": reasons},
    }


def collect(row: dict) -> dict:
    name, seed = row["parent_group"], row.get("official_evidence_url")
    if name in PLATFORM_KEYS:
        return {"parent_group": name, "status": "completed_platform_adapter", "seed_url": seed}
    if not seed:
        return {"parent_group": name, "status": "adapter_required_missing_seed", "seed_url": None, "pages_fetched": 0, "selected_jobs": 0}
    pages, errors = crawl(seed)
    raw_path = ROOT / f"data/sources/raw/generic-{key_for(name)}-official-pages.json"
    raw_path.write_text(json.dumps({"parent_group": name, "seed_url": seed, "collected_at": date.today().isoformat(), "pages": pages, "errors": errors}, ensure_ascii=False, indent=2))
    jobs = [job for page in pages if (job := normalize_page(name, page))]
    jobs = list({x["source"]["url"]: x for x in jobs}.values())
    catalog_path = ROOT / f"data/catalog/generic-{key_for(name)}-relevant-jobs-v1.0.json"
    catalog_path.write_text(json.dumps({"catalog_version": "1.0", "scope": f"{name} 2027校园招聘", "source_total": len(pages), "selected_total": len(jobs), "jobs": jobs}, ensure_ascii=False, indent=2))
    if jobs:
        status = "completed_generic_static"
    elif pages:
        status = "adapter_required_dynamic_or_no_job_pages"
    else:
        status = "access_failed"
    return {"parent_group": name, "status": status, "seed_url": seed, "pages_fetched": len(pages), "errors": len(errors), "selected_jobs": len(jobs), "raw_path": str(raw_path.relative_to(ROOT)), "catalog_path": str(catalog_path.relative_to(ROOT))}


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = [x for x in registry["enterprises"] if x["campaign_status"] in {"campaign_open_verified", "full_sweep_completed"}]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(collect, rows))
    results.sort(key=lambda x: x["parent_group"])
    summary = {}
    for r in results:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    payload = {"version": "1.0", "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"), "scope_count": len(rows), "summary": summary, "enterprises": results}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    print(json.dumps({"pages": sum(x.get("pages_fetched", 0) for x in results), "selected_jobs": sum(x.get("selected_jobs", 0) for x in results)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
