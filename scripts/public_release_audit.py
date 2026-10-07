#!/usr/bin/env python3
"""Audit OfferLab files before a public GitHub release."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".js", ".html", ".css", ".json", ".jsonl", ".txt"}
SKIP_PARTS = {".git", "work", "__pycache__"}
OWNED_SCAN_ROOTS = (ROOT / "README.md", ROOT / "ROADMAP.md", ROOT / "docs", ROOT / "prototype", ROOT / "scripts")


def iter_files(root: Path):
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if path.is_file() and not set(path.relative_to(ROOT).parts) & SKIP_PARTS:
            yield path


def check_json() -> list[str]:
    errors: list[str] = []
    for path in ROOT.rglob("*.json"):
        if set(path.relative_to(ROOT).parts) & SKIP_PARTS:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"JSON解析失败: {path.relative_to(ROOT)}: {exc}")
    return errors


def check_markdown_links() -> list[str]:
    errors: list[str] = []
    link_re = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
    for path in ROOT.rglob("*.md"):
        if set(path.relative_to(ROOT).parts) & SKIP_PARTS:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for raw_target in link_re.findall(text):
            target = raw_target.strip().strip("<>").split("#", 1)[0]
            if not target or re.match(r"^(https?://|mailto:|codex:)", target):
                continue
            if "<your-repository-url>" in target:
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"Markdown链接不存在: {path.relative_to(ROOT)} -> {raw_target}")
    return errors


def check_sensitive_literals() -> list[str]:
    errors: list[str] = []
    patterns = {
        "本机绝对路径": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
        "OpenAI样式密钥": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
        "疑似硬编码凭证": re.compile(
            r"(?i)\b(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]"
        ),
    }
    for root in OWNED_SCAN_ROOTS:
        for path in iter_files(root):
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for label, pattern in patterns.items():
                for match in pattern.finditer(text):
                    line = text.count("\n", 0, match.start()) + 1
                    errors.append(f"{label}: {path.relative_to(ROOT)}:{line}")
    return errors


def check_ignored_local_files() -> list[str]:
    errors: list[str] = []
    for candidate in ("work", ".DS_Store", ".env"):
        result = subprocess.run(
            ["git", "check-ignore", "-q", candidate], cwd=ROOT, check=False
        )
        if result.returncode != 0:
            errors.append(f"未被.gitignore覆盖: {candidate}")
    return errors


def main() -> int:
    checks = {
        "JSON": check_json(),
        "Markdown链接": check_markdown_links(),
        "敏感信息": check_sensitive_literals(),
        "本地文件忽略": check_ignored_local_files(),
    }
    failed = False
    for name, errors in checks.items():
        if errors:
            failed = True
            print(f"[FAIL] {name}: {len(errors)}")
            for error in errors[:30]:
                print(f"  - {error}")
        else:
            print(f"[PASS] {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
