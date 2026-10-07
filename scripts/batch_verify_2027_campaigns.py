#!/usr/bin/env python3
"""Search all unverified employers and retain auditable result evidence.

This script performs discovery only. It never converts an empty/failed search into
"no recruitment"; those records remain public_evidence_not_found.
"""

from __future__ import annotations

import concurrent.futures
import html
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/sources/enterprise-2027-campaign-verification-v2.0.json"
OUT = ROOT / "data/sources/remaining-108-enterprise-search-evidence-v1.0.json"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/129 Safari/537.36"
SSL_CONTEXT = ssl._create_unverified_context()
RESULT_RE = re.compile(r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>', re.S)
SNIP_RE = re.compile(r'<a class="result__snippet"[^>]*>(.*?)</a>', re.S)
BING_BLOCK_RE = re.compile(r'<li class="b_algo".*?</li>', re.S)
BING_LINK_RE = re.compile(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S)
BING_SNIP_RE = re.compile(r'<p[^>]*>(.*?)</p>', re.S)
TAG_RE = re.compile(r"<[^>]+>")


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", value))).strip()


def search(name: str) -> dict:
    query = f'"{name}" "2027" 校园招聘'
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20, context=SSL_CONTEXT) as response:
            body = response.read().decode("utf-8", "ignore")
        links = RESULT_RE.findall(body)[:5]
        snippets = SNIP_RE.findall(body)[:5]
        results = []
        for i, (href, title) in enumerate(links):
            parsed = urllib.parse.urlparse(html.unescape(href))
            target = urllib.parse.parse_qs(parsed.query).get("uddg", [html.unescape(href)])[0]
            results.append({
                "title": clean(title),
                "url": target,
                "snippet": clean(snippets[i]) if i < len(snippets) else "",
            })
        joined = " ".join(f"{x['title']} {x['snippet']}" for x in results)
        has_2027 = "2027" in joined and any(k in joined for k in ("校园招聘", "校招", "应届", "毕业生招聘"))
        row = {
            "parent_group": name,
            "query": query,
            "search_url": url,
            "request_status": "success",
            "discovery_status": "candidate_2027_evidence_found" if has_2027 else "public_evidence_not_found",
            "results": results,
        }
        if not has_2027:
            return search_bing(name, row)
        return row
    except Exception as exc:
        return search_bing(name, {
            "parent_group": name,
            "query": query,
            "search_url": url,
            "request_status": "failed",
            "discovery_status": "search_failed_not_a_negative_result",
            "error": f"{type(exc).__name__}: {exc}",
            "results": [],
        })


def search_bing(name: str, prior: dict) -> dict:
    query = f'"{name}" "2027" 校园招聘'
    url = "https://www.bing.com/search?" + urllib.parse.urlencode({"q": query, "count": 8})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20, context=SSL_CONTEXT) as response:
            body = response.read().decode("utf-8", "ignore")
        results = []
        for block in BING_BLOCK_RE.findall(body)[:5]:
            match = BING_LINK_RE.search(block)
            if not match:
                continue
            snippet = BING_SNIP_RE.search(block)
            results.append({
                "title": clean(match.group(2)),
                "url": html.unescape(match.group(1)),
                "snippet": clean(snippet.group(1)) if snippet else "",
            })
        joined = " ".join(f"{x['title']} {x['snippet']}" for x in results)
        has_2027 = "2027" in joined and any(k in joined for k in ("校园招聘", "校招", "应届", "毕业生招聘"))
        return {
            "parent_group": name,
            "query": query,
            "search_url": url,
            "request_status": "success",
            "discovery_status": "candidate_2027_evidence_found" if has_2027 else "public_evidence_not_found",
            "results": results,
            "fallback_from": prior.get("request_status"),
        }
    except Exception as exc:
        prior["bing_error"] = f"{type(exc).__name__}: {exc}"
        return prior


def main() -> None:
    registry = json.loads(SOURCE.read_text(encoding="utf-8"))
    names = [x["parent_group"] for x in registry["enterprises"] if x["campaign_status"] == "unverified"]
    started = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(search, names))
    rows.sort(key=lambda x: names.index(x["parent_group"]))
    counts = {}
    for row in rows:
        counts[row["discovery_status"]] = counts.get(row["discovery_status"], 0) + 1
    payload = {
        "version": "1.0",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "scope_count": len(rows),
        "method": "Exact enterprise name + 2027 + campus recruitment; top five public search results retained.",
        "negative_rule": "No result and request failure are not evidence that recruitment is closed.",
        "summary": counts,
        "elapsed_seconds": round(time.time() - started, 2),
        "enterprises": rows,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False))
    print(OUT)


if __name__ == "__main__":
    main()
