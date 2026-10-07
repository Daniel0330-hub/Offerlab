#!/usr/bin/env python3
"""Build the expanded enterprise candidate list supplied by the user."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INDUSTRIAL = """中国核工业集团有限公司
中国航天科技集团有限公司
中国航天科工集团有限公司
中国航空工业集团有限公司
中国船舶集团有限公司
中国兵器工业集团有限公司
中国兵器装备集团有限公司
中国电子科技集团有限公司
中国航空发动机集团有限公司
中国融通资产管理集团有限公司
中国石油天然气集团有限公司
中国石油化工集团有限公司
中国海洋石油集团有限公司
国家石油天然气管网集团有限公司
国家电网有限公司
中国南方电网有限责任公司
中国华能集团有限公司
中国大唐集团有限公司
中国华电集团有限公司
国家电力投资集团有限公司
中国长江三峡集团有限公司
中国广核集团有限公司
中国雅江集团有限公司
国家能源投资集团有限责任公司
中国电信集团有限公司
中国联合网络通信集团有限公司
中国移动通信集团有限公司
中国卫星网络集团有限公司
中国电子信息产业集团有限公司
中国第一汽车集团有限公司
东风汽车集团有限公司
中国机械工业集团有限公司
哈尔滨电气集团有限公司
东方电气集团有限公司
中国中车集团有限公司
中国通用技术（集团）控股有限责任公司
中国建筑科学研究院有限公司
中国有研科技集团有限公司
中国宝武钢铁集团有限公司
鞍钢集团有限公司
中国铝业集团有限公司
中国五矿集团有限公司
中国稀土集团有限公司
中国钢研科技集团有限公司
矿冶科技集团有限公司
中国建筑集团有限公司
中国中铁股份有限公司
中国铁建股份有限公司
中国交通建设集团有限公司
中国能源建设集团有限公司
中国电力建设股份有限公司
中国化学工程集团有限公司
招商局集团有限公司
中国远洋海运集团有限公司
中国国际航空集团有限公司
中国东方航空集团有限公司
中国南方航空集团有限公司
中国物流集团有限公司
中国中粮集团有限公司
中国储备粮管理集团有限公司
华润（集团）有限公司
中国旅游集团有限公司
中国投资有限责任公司
中国国新控股有限责任公司
中国节能环保集团有限公司
中国诚通控股集团有限公司
中国中化控股有限责任公司
中国建材集团有限公司
中国医药集团有限公司
中国保利集团有限公司
中国新兴际华集团有限公司
中国黄金集团有限公司
中国中煤能源集团有限公司
中国煤炭科工集团有限公司
中国盐业集团有限公司
中国商用飞机有限责任公司
中国信息通信科技集团有限公司
中国铁塔股份有限公司
中国航天信息股份有限公司
中国电子科技网络信息安全有限公司
中国有色矿业集团有限公司
中国国际技术智力合作集团有限公司
中国建筑材料科学研究总院有限公司
中国铁路物资集团有限公司
中国林业集团有限公司
中国农垦集团有限公司
中国中纺集团有限公司
中国工艺集团有限公司
中国轻工业品进出口集团有限公司
中国海外控股集团有限公司
中国中信集团有限公司
中国光大集团股份公司
中国保利科技有限公司
中国新时代控股集团有限公司
中国华录集团有限公司
中国西电集团有限公司
中国电气装备集团有限公司
中国安能建设集团有限公司
中国矿产资源集团有限公司
中国检验认证（集团）有限公司""".splitlines()

FINANCIAL = """国家开发银行
中国进出口银行
中国农业发展银行
中国工商银行股份有限公司
中国农业银行股份有限公司
中国银行股份有限公司
中国建设银行股份有限公司
交通银行股份有限公司
中国人民保险集团股份有限公司
中国人寿保险（集团）公司
中国太平保险集团有限责任公司
中国出口信用保险公司
中国中信金融资产管理股份有限公司
中国长城资产管理股份有限公司
中国东方资产管理股份有限公司
中国信达资产管理股份有限公司
中央国债登记结算有限责任公司
中国农业再保险股份有限公司
中国政企合作投资基金股份有限公司
国家融资担保基金有限责任公司
国家农业信贷担保联盟有限责任公司
中国再保险（集团）股份有限公司
中国建银投资有限责任公司
中国银河金融控股有限责任公司""".splitlines()

CULTURAL = ["中国出版集团有限公司", "中国对外文化集团有限公司", "中国广播电视网络集团有限公司"]
SPECIAL = ["中国国家铁路集团有限公司", "中国烟草总公司"]

# Candidate-name -> canonical name already present in the original 99-company scope.
ALIASES = {
    "东方电气集团有限公司": "中国东方电气集团有限公司",
    "中国中铁股份有限公司": "中国铁路工程集团有限公司",
    "中国铁建股份有限公司": "中国铁道建筑集团有限公司",
    "中国电力建设股份有限公司": "中国电力建设集团有限公司",
    "中国国际航空集团有限公司": "中国航空集团有限公司",
    "中国中粮集团有限公司": "中粮集团有限公司",
    "中国旅游集团有限公司": "中国旅游集团有限公司[香港中旅（集团）有限公司]",
    "中国新兴际华集团有限公司": "新兴际华集团有限公司",
    "中国保利科技有限公司": "中国保利集团有限公司",
}


def main():
    original = json.loads((ROOT / "data/sources/central-soe-universe-v0.1.json").read_text())
    known = {x["name"] for x in original["enterprises"]}
    rows = []
    for category, names in [
        ("industrial_central_enterprise", INDUSTRIAL),
        ("financial_central_enterprise", FINANCIAL),
        ("cultural_central_enterprise", CULTURAL),
        ("special_central_enterprise", SPECIAL),
    ]:
        for rank, name in enumerate(names, 1):
            canonical = ALIASES.get(name, name)
            relation = "already_in_original_scope" if canonical in known else "new_candidate"
            rows.append({
                "category": category,
                "rank_in_category": rank,
                "name_as_provided": name,
                "canonical_name": canonical,
                "scope_relation": relation,
                "alias_or_subsidiary_of": canonical if canonical != name else None,
                "screening_status": "covered_by_original_audit" if relation == "already_in_original_scope" else "pending_review",
            })
    out = {
        "version": "v0.1",
        "captured_at": "2026-10-06",
        "source_type": "user_provided_reference_images",
        "source_note": "The screenshots define the candidate universe only. Job inclusion still requires an official 2027 campus source and complete single-job JD evidence.",
        "counts": {
            "provided_rows": len(rows),
            "already_in_original_scope_or_alias": sum(r["scope_relation"] == "already_in_original_scope" for r in rows),
            "new_candidates": sum(r["scope_relation"] == "new_candidate" for r in rows),
        },
        "records": rows,
    }
    target = ROOT / "data/sources/expanded-central-enterprise-candidates-v0.1.json"
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(out["counts"], ensure_ascii=False))
    print("NEW")
    for r in rows:
        if r["scope_relation"] == "new_candidate":
            print(r["category"], r["rank_in_category"], r["name_as_provided"])


if __name__ == "__main__":
    main()
