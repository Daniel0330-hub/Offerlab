#!/usr/bin/env python3
"""Run the v1.1 retrieval configuration once on the frozen test set."""
from __future__ import annotations

import json
from pathlib import Path

from tune_retrieval_on_development import (
    cosine, coverage, expand, flat_value, fulltext, grams, idf_from_train,
    job_fields, lexical, ndcg, recall, vector,
)

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/evaluation/train-set-v1.0.json"
TEST = ROOT / "data/evaluation/test-set-v1.0.json"
QUERY_FILES = [
    ROOT / "data/evaluation/test-queries-v1.0.json",
    ROOT / "data/evaluation/test-queries-paraphrase-v1.0.json",
]
CONFIG = ROOT / "data/evaluation/retrieval-config-v1.1.json"
OUT = ROOT / "data/evaluation/frozen-test-results-v1.0.json"


def mean(values):
    return round(sum(values) / len(values), 4)


def main():
    if OUT.exists():
        raise SystemExit(f"REFUSED: frozen result already exists: {OUT}")
    train = json.loads(TRAIN.read_text())
    test = json.loads(TEST.read_text())
    queries = sum((json.loads(path.read_text()) for path in QUERY_FILES), [])
    config = json.loads(CONFIG.read_text())
    idf, n_docs = idf_from_train(train)
    doc_vectors = {job["job_id"]: vector(grams(fulltext(job)), idf, n_docs) for job in test}
    metrics = {name: {"r5": [], "r10": [], "n5": []} for name in ("offerlab_hybrid", "char_tfidf", "frozen_two_stage")}
    output = {
        "run_at": "2026-10-06",
        "configuration": CONFIG.name,
        "dataset": TEST.name,
        "query_files": [path.name for path in QUERY_FILES],
        "configuration_modified_after_test": False,
        "queries": [],
        "summary": {},
    }
    for query in queries:
        qvec = vector(grams(query["query"]), idf, n_docs)
        scored = []
        for job in test:
            base = lexical(job, query["terms"], False)
            syn = lexical(job, query["terms"], True)
            vec = cosine(qvec, doc_vectors[job["job_id"]])
            scored.append({"job_id": job["job_id"], "base": base, "vec": vec, "final": 0.3 * syn + 0.7 * vec})
        base_rank = sorted(scored, key=lambda x: (-x["base"], x["job_id"]))
        vector_rank = sorted(scored, key=lambda x: (-x["vec"], x["job_id"]))
        candidates = {x["job_id"] for x in vector_rank[:10]}
        final_rank = sorted((x for x in scored if x["job_id"] in candidates), key=lambda x: (-x["final"], x["job_id"]))
        relevant = set(query["relevant_job_ids"])
        qr = {"query_id": query["query_id"], "query": query["query"], "relevant_job_ids": query["relevant_job_ids"], "methods": {}}
        for name, ranking, score_key in (
            ("offerlab_hybrid", base_rank, "base"),
            ("char_tfidf", vector_rank, "vec"),
            ("frozen_two_stage", final_rank, "final"),
        ):
            positive = [x for x in ranking if x[score_key] > 0]
            ids = [x["job_id"] for x in positive]
            values = {
                "recall_at_5": round(recall(ids, relevant, 5), 4),
                "recall_at_10": round(recall(ids, relevant, 10), 4),
                "ndcg_at_5": round(ndcg(ids, relevant, 5), 4),
                "top_5": [[x["job_id"], round(x[score_key], 6)] for x in positive[:5]],
            }
            qr["methods"][name] = values
            metrics[name]["r5"].append(values["recall_at_5"])
            metrics[name]["r10"].append(values["recall_at_10"])
            metrics[name]["n5"].append(values["ndcg_at_5"])
        output["queries"].append(qr)
    for name, values in metrics.items():
        output["summary"][name] = {
            "mean_recall_at_5": mean(values["r5"]),
            "mean_recall_at_10": mean(values["r10"]),
            "mean_ndcg_at_5": mean(values["n5"]),
        }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(output["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
