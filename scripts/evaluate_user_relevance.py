#!/usr/bin/env python3
"""汇总原型导出的三级相关性标注，计算 NDCG@10、Precision@10 与标签分布。"""
import argparse, json, math
from pathlib import Path

def dcg(labels):
    return sum((2 ** value - 1) / math.log2(rank + 2) for rank, value in enumerate(labels))

parser = argparse.ArgumentParser()
parser.add_argument("files", nargs="+", type=Path)
parser.add_argument("--output", type=Path, default=Path("data/evaluation/user-relevance-results-v1.0.json"))
args = parser.parse_args()
runs = []
for path in args.files:
    payload = json.loads(path.read_text())
    records = payload["records"]
    labels = [int(r["label"]) for r in records[:10]]
    ideal = sorted(labels, reverse=True)
    denominator = dcg(ideal)
    runs.append({
        "file": str(path), "count": len(labels),
        "ndcg_at_10": round(dcg(labels) / denominator, 4) if denominator else None,
        "precision_at_10": round(sum(v > 0 for v in labels) / len(labels), 4),
        "highly_relevant_at_10": sum(v == 2 for v in labels),
        "label_distribution": {str(v): labels.count(v) for v in (0, 1, 2)}
    })
valid_ndcg = [r["ndcg_at_10"] for r in runs if r["ndcg_at_10"] is not None]
report = {"version":"1.0","run_count":len(runs),"scope":"真实用户三级相关性标注",
          "macro_average":{"ndcg_at_10":round(sum(valid_ndcg)/len(valid_ndcg),4) if valid_ndcg else None,
                           "precision_at_10":round(sum(r["precision_at_10"] for r in runs)/len(runs),4),
                           "highly_relevant_at_10":round(sum(r["highly_relevant_at_10"] for r in runs)/len(runs),2)},
          "runs":runs}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False, indent=2))
