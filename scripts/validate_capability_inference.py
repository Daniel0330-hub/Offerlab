#!/usr/bin/env python3
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data/evaluation/capability-inference-cases-v1.0.json"
OUTPUT = ROOT / "data/evaluation/capability-inference-results-v1.0.json"

RULES = [
    (r"\bsql\b", ["数据查询", "基础数据分析", "数据库基础"]),
    (r"\bpython\b", ["编程基础", "数据处理", "自动化脚本"]),
    (r"pandas|numpy|数据清洗", ["数据清洗", "数据处理", "基础数据分析"]),
    (r"scikit-learn|sklearn|机器学习", ["机器学习", "模型训练与评估"]),
    (r"统计学|应用统计", ["统计分析", "统计建模", "数据分析"]),
    (r"精算", ["风险分析", "统计建模", "数据分析"]),
    (r"大数据|数据科学", ["数据分析", "数据工程基础", "数据平台基础"]),
    (r"人工智能|智能科学", ["人工智能基础", "机器学习基础", "模型训练基础"]),
    (r"计算机|软件工程", ["编程基础", "软件开发基础", "系统设计基础"]),
    (r"信息管理|管理科学与工程", ["需求分析", "数据分析", "业务流程理解"]),
    (r"需求调研|用户访谈|需求分析", ["需求分析", "用户研究", "产品方案"]),
    (r"axure|figma|原型", ["原型设计", "产品表达"]),
    (r"java|spring", ["Java开发", "后端开发基础"]),
    (r"c\+\+|\bcpp\b", ["C++开发", "系统编程基础"]),
    (r"c语言|c language", ["C语言开发", "系统编程基础"]),
    (r"linux|运维|故障处理", ["系统运维基础", "故障定位"]),
    (r"网络安全|信息安全|渗透", ["网络安全基础", "安全测试"]),
]

def infer(case):
    hay = " ".join(case["majors"] + case["skills"] + [case["experience"]])
    result = []
    for pattern, abilities in RULES:
        if re.search(pattern, hay, re.I):
            result.extend(abilities)
    return list(dict.fromkeys(result))

payload = json.loads(CASES.read_text())
results = []
for case in payload["cases"]:
    actual = infer(case)
    missing = [x for x in case["expected"] if x not in actual]
    violations = [x for x in case["forbidden"] if x in actual]
    results.append({"id":case["id"],"passed":not missing and not violations,"actual":actual,"missing":missing,"forbidden_hits":violations})

report = {
    "version":"1.0",
    "case_count":len(results),
    "passed":sum(x["passed"] for x in results),
    "accuracy":sum(x["passed"] for x in results)/len(results),
    "scope":"规则契约测试；不代表真实用户推荐准确率",
    "results":results,
}
OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: report[k] for k in ("case_count","passed","accuracy")}, ensure_ascii=False))
