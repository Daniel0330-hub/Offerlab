#!/usr/bin/env python3
"""Validate OfferLab structured job datasets without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_FIELDS = {
    "job_id",
    "title",
    "company",
    "parent_group",
    "locations",
    "recruitment_type",
    "graduation_years",
    "responsibilities",
    "skills",
    "base_requirements",
    "other_explicit_conditions",
    "source",
}
SKILL_LEVELS = {"required", "expected", "preferred", "exposure", "unknown"}
RECRUITMENT_TYPES = {"campus", "experienced", "internship", "unknown"}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"无法读取 JSON：{exc}"]
    if not isinstance(rows, list):
        return ["根节点必须是岗位数组"]

    seen: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"row[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: 必须是对象")
            continue
        job_id = row.get("job_id", prefix)
        missing = REQUIRED_FIELDS - row.keys()
        if missing:
            errors.append(f"{job_id}: 缺少字段 {sorted(missing)}")
        if job_id in seen:
            errors.append(f"{job_id}: job_id 重复")
        seen.add(job_id)
        if row.get("recruitment_type") not in RECRUITMENT_TYPES:
            errors.append(f"{job_id}: recruitment_type 非法")
        if not isinstance(row.get("locations"), list) or not row.get("locations"):
            errors.append(f"{job_id}: locations 必须是非空数组")
        if not isinstance(row.get("graduation_years"), list) or not row.get("graduation_years"):
            errors.append(f"{job_id}: graduation_years 必须是非空数组")
        if not isinstance(row.get("parent_group"), str) or not row.get("parent_group", "").strip():
            errors.append(f"{job_id}: parent_group 必须是非空字符串")

        for field in ("responsibilities", "other_explicit_conditions"):
            for item in row.get(field, []):
                if not item.get("evidence_span"):
                    errors.append(f"{job_id}: {field} 存在空证据")
        for item in row.get("skills", []):
            if item.get("level") not in SKILL_LEVELS:
                errors.append(f"{job_id}: 技能级别非法 {item.get('level')}")
            if not item.get("evidence_span"):
                errors.append(f"{job_id}: 技能存在空证据")
        for item in row.get("base_requirements", []):
            if not item.get("evidence_span"):
                errors.append(f"{job_id}: 基础条件存在空证据")

        source = row.get("source", {})
        parsed = urlparse(source.get("url", ""))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{job_id}: source.url 不是有效 HTTP(S) URL")
        try:
            date.fromisoformat(source.get("collected_at", ""))
        except ValueError:
            errors.append(f"{job_id}: collected_at 不是 YYYY-MM-DD")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    errors = validate(args.dataset)
    if errors:
        print(f"FAIL: {len(errors)} 个问题")
        for error in errors:
            print(f"- {error}")
        return 1
    rows = json.loads(args.dataset.read_text(encoding="utf-8"))
    print(f"PASS: {len(rows)} 条岗位通过数据质量检查")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
