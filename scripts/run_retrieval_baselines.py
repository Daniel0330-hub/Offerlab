#!/usr/bin/env python3
"""Run three transparent retrieval baselines on the OfferLab development set."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "data/evaluation/development-set-v0.1.json"
QUERIES = ROOT / "data/evaluation/retrieval-queries-v0.1.json"
OUTPUT = ROOT / "data/evaluation/retrieval-results-v0.1.json"


def text(items: list[dict], *keys: str) -> str:
    return " ".join(str(item.get(key, "")) for item in items for key in keys).lower()


def coverage(terms: list[str], corpus: str) -> float:
    if not terms:
        return 0.0
    return sum(term.lower() in corpus for term in terms) / len(terms)


def corpora(job: dict) -> dict[str, str]:
    return {
        "title": job["title"].lower(),
        "responsibility": text(job["responsibilities"], "normalized_label", "evidence_span"),
        "skill": text(job["skills"], "raw_name", "normalized_name", "evidence_span"),
        "domain": text(job["base_requirements"], "value", "evidence_span"),
    }


def scores(job: dict, terms: list[str]) -> dict[str, float]:
    c = corpora(job)
    title = coverage(terms, c["title"])
    skill = coverage(terms, c["skill"])
    responsibility = coverage(terms, c["responsibility"])
    domain = coverage(terms, c["domain"])
    return {
        "title_only": title,
        "title_skill": 0.4 * title + 0.6 * skill,
        "offerlab_hybrid": 0.4 * responsibility + 0.35 * skill + 0.15 * domain + 0.1 * title,
    }


def recall_at_k(ranking: list[str], relevant: set[str], k: int = 5) -> float:
    return len(set(ranking[:k]) & relevant) / len(relevant) if relevant else 0.0


def main() -> None:
    jobs = json.loads(JOBS.read_text(encoding="utf-8"))
    queries = json.loads(QUERIES.read_text(encoding="utf-8"))
    result = {"dataset": JOBS.name, "queries": [], "summary": {}}
    methods = ["title_only", "title_skill", "offerlab_hybrid"]
    totals = {method: [] for method in methods}

    for query in queries:
        ranked = {method: [] for method in methods}
        for job in jobs:
            for method, score in scores(job, query["terms"]).items():
                ranked[method].append((job["job_id"], round(score, 4)))
        relevant = set(query["relevant_job_ids"])
        query_result = {"query_id": query["query_id"], "query": query["query"], "methods": {}}
        for method in methods:
            ordered = [item for item in sorted(ranked[method], key=lambda item: (-item[1], item[0])) if item[1] > 0]
            ids = [item[0] for item in ordered]
            recall = round(recall_at_k(ids, relevant), 4)
            totals[method].append(recall)
            query_result["methods"][method] = {"recall_at_5": recall, "top_5": ordered[:5]}
        result["queries"].append(query_result)

    for method in methods:
        values = totals[method]
        result["summary"][method] = {"mean_recall_at_5": round(sum(values) / len(values), 4)}
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for method in methods:
        print(method, result["summary"][method]["mean_recall_at_5"])


if __name__ == "__main__":
    main()
