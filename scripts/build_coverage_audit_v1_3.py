#!/usr/bin/env python3
"""Merge campaign verification v2 into the coverage audit."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
old = json.loads((ROOT / "data/sources/full-catalog-coverage-audit-v1.2.json").read_text(encoding="utf-8"))
verification = json.loads((ROOT / "data/sources/enterprise-2027-campaign-verification-v2.0.json").read_text(encoding="utf-8"))
by_name = {r["parent_group"]: r for r in verification["enterprises"]}

rows = []
for row in old["enterprises"]:
    v = by_name[row["parent_group"]]
    merged = dict(row)
    merged.update({
        "campaign_status_v2": v["campaign_status"],
        "campaign_open_v2": v["campaign_open"],
        "campaign_evidence_url_v2": v["official_evidence_url"],
        "campaign_evidence_type_v2": v["evidence_type"],
        "job_level_extraction_status_v2": v["job_level_extraction_status"],
        "verification_note_v2": v["evidence_note"],
    })
    rows.append(merged)

out = {
    "version": "1.3",
    "updated_at": "2026-10-07",
    "correction": "v1.2 corpus coverage and URL reachability must not be interpreted as campaign availability.",
    "policy": old["policy"],
    "summary": {
        **old["summary"],
        "campaign_open_or_full_sweep_verified": sum(r["campaign_status"] in {"campaign_open_verified", "full_sweep_completed"} for r in verification["enterprises"]),
        "official_site_verified_campaign_pending": verification["summary"].get("official_site_verified_campaign_pending", 0),
        "campaign_unverified": verification["summary"].get("unverified", 0),
        "warning": "groups_in_corpus is not the count of employers with open recruitment.",
    },
    "enterprises": rows,
}
(ROOT / "data/sources/full-catalog-coverage-audit-v1.3.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(out["summary"], ensure_ascii=False, indent=2))
