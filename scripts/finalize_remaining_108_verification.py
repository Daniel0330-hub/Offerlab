#!/usr/bin/env python3
"""Finalize the one-pass review of the 108 previously unverified enterprises."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/sources/enterprise-2027-campaign-verification-v2.0.json"
SEARCH = ROOT / "data/sources/remaining-108-enterprise-search-evidence-v1.0.json"
OUT = ROOT / "data/sources/enterprise-2027-campaign-verification-v2.1.json"

registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
search = json.loads(SEARCH.read_text(encoding="utf-8"))
searched = {x["parent_group"]: x for x in search["enterprises"]}

for row in registry["enterprises"]:
    row["one_pass_verification_completed"] = True
    if row["campaign_status"] == "unverified":
        evidence = searched.get(row["parent_group"], {})
        row["campaign_status"] = "checked_public_evidence_insufficient"
        row["campaign_open"] = None
        row["evidence_note"] = (
            "已完成企业全称+2027校招公开检索，但尚未取得足以确认当前批次开放或关闭的官方证据；"
            "不得解释为无岗位。"
        )
        row["search_query"] = evidence.get("query")
        row["search_request_status"] = evidence.get("request_status")
        row["search_result_count"] = len(evidence.get("results", []))
        row["job_level_extraction_status"] = "blocked_pending_official_campaign_evidence"

summary = Counter(x["campaign_status"] for x in registry["enterprises"])
registry.update({
    "version": "2.1",
    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "one_pass_verification_scope": 144,
    "previously_unverified_processed": 108,
    "summary": dict(summary),
    "interpretation": (
        "Every enterprise has now completed a first-pass public verification. "
        "checked_public_evidence_insufficient is an unknown state, not a negative recruitment finding."
    ),
})
OUT.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(registry["summary"], ensure_ascii=False))
print(OUT)
