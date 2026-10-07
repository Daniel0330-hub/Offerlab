#!/usr/bin/env python3
"""Collect and normalize the full relevant-job catalog from China Unicom's official campus site."""

from __future__ import annotations

import argparse
import html
import json
import re
import ssl
import urllib.request
from datetime import date
from pathlib import Path


API = "https://fe.zhaopin.com/grace/api/dsc/search-job-list"
ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data/sources/raw/china-unicom-2027-official-jobs.json"
CATALOG_PATH = ROOT / "data/catalog/china-unicom-2027-relevant-jobs-v1.0.json"

FAMILY_RULES = [
    ("AI与算法", [r"人工智能", r"\bAI\b", r"算法", r"大模型", r"智能体", r"机器学习", r"深度学习", r"计算机视觉"]),
    ("产品与解决方案", [r"产品经理", r"产品管理", r"产品运营", r"产品规划", r"产品研发", r"产品创新", r"解决方案", r"行业方案", r"售前"]),
    ("数据分析与治理", [r"数据分析", r"数据运营", r"数据治理", r"数据研发", r"数据开发", r"大数据", r"经营分析", r"数据赋能", r"数据科学", r"商业分析"]),
    ("软件与平台开发", [r"软件开发", r"应用开发", r"系统开发", r"平台开发", r"前端", r"后端", r"全栈", r"Java", r"Python", r"研发工程师", r"软件工程师", r"信息科技"]),
    ("运维、云与安全", [r"系统运维", r"平台运维", r"网络运维", r"运维工程师", r"DevOps", r"云计算", r"云平台", r"网络安全", r"信息安全", r"算力运营", r"网络数字化"]),
    ("测试与质量", [r"测试开发", r"软件测试", r"质量工程"]),
]

EXCLUDE_ONLY = re.compile(r"人力|党务|党建|纪检|财务|会计|审计|法务|法律|采购|文秘|行政|工会|薪酬|渠道经理|客户经理|营销经理|销售经理")
TECH_SIGNALS = re.compile(r"Python|Java|SQL|C\+\+|数据库|软件|算法|模型|数据|开发|编程|云计算|平台|系统|网络安全|信息安全|人工智能|大模型|智能体", re.I)


def fetch_page(page: int) -> dict:
    payload = json.dumps({
        "pageIndex": page, "pageSize": 1000, "orgNumbers": ["105347"],
        "jobSource": 2, "orgDepartmentIds": [], "workRegionIds": "",
        "jobTypes": "", "priorityMajors": "", "customTags": "",
        "campusParentDepartmentIds": ""
    }).encode()
    req = urllib.request.Request(API, data=payload, headers={
        "Content-Type": "application/json",
        "Origin": "https://zglt.zhaopin.com",
        "Referer": "https://zglt.zhaopin.com/scjobs/index.html",
        "User-Agent": "Mozilla/5.0 JobLab research collector"
    })
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
        return json.load(response)


def clean_lines(raw: str) -> list[str]:
    text = re.sub(r"<br\s*/?>", "\n", raw or "", flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\r", "\n")
    return [re.sub(r"^[\s\d、.．)）(（-]+", "", x).strip() for x in text.split("\n") if x.strip()]


def sections(raw: str) -> tuple[list[str], list[str]]:
    lines = clean_lines(raw)
    duties, requirements, mode = [], [], "duties"
    for line in lines:
        if "任职要求" in line or "岗位要求" in line or "任职资格" in line:
            mode = "requirements"; continue
        if "岗位职责" in line or "工作职责" in line:
            mode = "duties"; continue
        (requirements if mode == "requirements" else duties).append(line)
    return duties, requirements


def family_for(title: str, detail: str) -> tuple[str | None, list[str]]:
    matches = []
    for family, patterns in FAMILY_RULES:
        title_hits = [p for p in patterns if re.search(p, title, re.I)]
        if title_hits:
            matches.append((family, title_hits))
    # Generic development/operations titles require a technical signal in the JD.
    if not matches and re.search(r"开发|研发|项目实施|项目交付", title) and TECH_SIGNALS.search(detail):
        family = "软件与平台开发" if re.search(r"开发|研发", title) else "运维、云与安全"
        matches.append((family, ["技术JD信号"]))
    if not matches:
        return None, []
    # Exclusion only wins when no high-intent product/data/AI/software phrase is present.
    high_intent = re.search(r"产品经理|解决方案|数据分析|数据治理|数据开发|人工智能|\bAI\b|算法|软件开发|系统开发|平台开发|测试开发", title, re.I)
    if EXCLUDE_ONLY.search(title) and not high_intent:
        return None, []
    return matches[0][0], matches[0][1]


def extract_major(requirements: list[str]) -> list[str]:
    for line in requirements:
        if "专业" in line:
            value = re.split(r"专业要求[:：]?", line, maxsplit=1)[-1]
            parts = [x.strip(" 等相关专业及") for x in re.split(r"[、,，；;/]", value) if x.strip()]
            return parts[:12]
    return []


def extract_skills(duties: list[str], requirements: list[str]) -> list[dict]:
    text = "；".join(duties + requirements)
    rules = [
        ("Python", r"Python"), ("Java", r"Java"), ("SQL", r"\bSQL\b"),
        ("C/C++", r"C\+\+|C语言"), ("数据分析", r"数据分析|经营分析"),
        ("数据治理", r"数据治理|数据质量"), ("产品设计", r"产品设计|产品规划|需求分析"),
        ("解决方案", r"解决方案|行业方案"), ("人工智能", r"人工智能|\bAI\b"),
        ("大模型", r"大模型|LLM"), ("机器学习", r"机器学习|深度学习"),
        ("软件开发", r"软件开发|系统开发|应用开发|平台开发"),
        ("数据库", r"数据库|MySQL|Oracle"), ("云计算", r"云计算|云平台"),
        ("网络安全", r"网络安全|信息安全"), ("项目管理", r"项目管理|项目实施|项目交付"),
    ]
    out = []
    for name, pattern in rules:
        m = re.search(pattern, text, re.I)
        if m:
            evidence = next((x for x in duties + requirements if re.search(pattern, x, re.I)), m.group(0))
            out.append({"raw_name": m.group(0), "normalized_name": name, "level": "expected", "evidence_span": evidence})
    return out[:10]


def normalize(item: dict, parent_group: str = "中国联合网络通信集团有限公司",
              id_prefix: str = "unicom", campaign: str = "中国联通2027校园招聘") -> dict | None:
    company, job = item["company"], item["job"]
    title, detail = job.get("title", "").strip(), job.get("detail", "")
    family, reasons = family_for(title, detail)
    if not family:
        return None
    duties, requirements = sections(detail)
    majors = extract_major(requirements)
    base = [{"criterion": "graduation_year", "operator": "equals", "value": 2027,
             "requirement_level": "required", "evidence_span": campaign}]
    degree = job.get("minEducationName")
    if degree and degree != "不限":
        degree = "硕士研究生" if "硕士" in degree else "博士研究生" if "博士" in degree else degree
        base.append({"criterion": "degree", "operator": "minimum", "value": degree,
                     "requirement_level": "required", "evidence_span": f"学历要求：{job.get('minEducationName')}"})
    if majors:
        base.append({"criterion": "major", "operator": "includes", "value": majors,
                     "requirement_level": "required", "evidence_span": next(x for x in requirements if "专业" in x)})
    city = job.get("cityName") or job.get("address") or "地点未明确"
    return {
        "job_id": f"{id_prefix}-{job['jobNumber'].lower()}", "title": title,
        "company": company.get("campusOrgName") or company.get("slaveDisplayOrgName") or "中国联通",
        "parent_group": parent_group, "locations": [city],
        "recruitment_type": "campus", "graduation_years": [2027], "job_family": family,
        "responsibilities": [{"normalized_label": x[:18], "evidence_span": x} for x in duties[:10]],
        "skills": extract_skills(duties, requirements), "base_requirements": base,
        "other_explicit_conditions": [],
        "source": {"url": job.get("url"), "collected_at": date.today().isoformat(),
                   "job_number": job.get("jobNumber"), "official_campaign": campaign},
        "catalog_selection": {"method": "title_first_taxonomy_v1", "matched_signals": reasons}
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-cache", action="store_true")
    args = parser.parse_args()
    if args.from_cache:
        raw = json.loads(RAW_PATH.read_text())
    else:
        pages, jobs = [], []
        first = fetch_page(1); pages.append(first); jobs.extend(first["data"]["jobList"])
        for page in range(2, first["data"]["pageInfo"]["totalPage"] + 1):
            result = fetch_page(page); pages.append(result); jobs.extend(result["data"]["jobList"])
        raw = {"source": "China Unicom official campus recruitment site", "api": API,
               "collected_at": date.today().isoformat(), "reported_total": first["data"]["pageInfo"]["totalNum"],
               "records": jobs}
        RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
        RAW_PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2))
    selected = [x for item in raw["records"] if (x := normalize(item))]
    # Stable source-id deduplication.
    selected = list({x["job_id"]: x for x in selected}.values())
    catalog = {"catalog_version": "1.0", "scope": "China Unicom 2027 relevant campus jobs",
               "source_total": len(raw["records"]), "selected_total": len(selected), "jobs": selected}
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2))
    by_family = {}
    for item in selected: by_family[item["job_family"]] = by_family.get(item["job_family"], 0) + 1
    print(json.dumps({"source_total": len(raw["records"]), "selected_total": len(selected), "by_family": by_family}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
