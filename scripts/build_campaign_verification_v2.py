#!/usr/bin/env python3
"""Build a campaign-level verification registry without treating crawl gaps as no jobs."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data/sources/full-catalog-coverage-audit-v1.2.json"
OUT = ROOT / "data/sources/enterprise-2027-campaign-verification-v2.0.json"


# Evidence checked on 2026-10-07. Official evidence is preferred. University career
# pages are kept as corroborating evidence and are explicitly labelled as such.
VERIFIED = {
    "中国一重集团有限公司": ("campaign_open_verified", "https://www.cfhi.com/", "current_campaign_evidence", "2027届校园招聘简章及招聘活动已确认"),
    "中国东方电气集团有限公司": ("campaign_open_verified", "https://career.dongfang.com/", "current_campaign_evidence", "2027届校招覆盖20余家单位、400余岗位"),
    "中国东方航空集团有限公司": ("campaign_open_verified", "https://job.ceair.com/", "official_recruitment_site", "2027全球校园招聘已确认，覆盖近百职位"),
    "中国东方资产管理股份有限公司": ("campaign_open_verified", "https://coamc.zhiye.com/campus", "official_campaign_site", "2027年度校园招聘公告与校招门户已确认"),
    "中国中信金融资产管理股份有限公司": ("campaign_open_verified", "https://www.famc.citic/rczp/zpxx/index.shtml", "official_campaign_announcement", "官网人才招聘栏目发布2027校园招聘公告"),
    "中国中化控股有限责任公司": ("campaign_open_verified", "http://sinochem.hotjob.cn/", "official_campaign_site", "2027校园招聘已确认，公开信息显示招聘2097人"),
    "中国中煤能源集团有限公司": ("campaign_open_verified", "https://zhaopin.chinacoal.com/", "current_campaign_evidence", "中国中煤2027届秋季校园招聘已启动"),
    "中国五矿集团有限公司": ("campaign_open_verified", "https://zhaopin.minmetals.com.cn/", "official_recruitment_site", "2027校招及所属单位岗位已确认"),
    "中国交通建设集团有限公司": ("campaign_open_verified", "https://zhaopin.ccccltd.cn/", "current_campaign_evidence", "集团组织2027届专场招聘，70余家所属单位参加"),
    "中国人寿保险（集团）公司": ("campaign_open_verified", "https://chinalife.zhiye.com/", "official_recruitment_site", "核心成员单位2027年度校园招聘已确认"),
    "中国人民保险集团股份有限公司": ("campaign_open_verified", "http://picc.zhiye.com/", "official_campaign_site", "集团2027届校园招聘已确认，含IT、精算、统计等方向"),
    "中国农业发展银行": ("campaign_open_verified", "https://www.adbc.com.cn/n354735/n355043/c722284/content.html", "official_campaign_announcement", "官网2027年度校园招聘公告已发布"),
    "中国农业银行股份有限公司": ("campaign_open_verified", "https://career.abchina.com.cn/", "official_recruitment_site", "2027年度校园招聘已启动"),
    "中国石油化工集团有限公司": ("campaign_open_verified", "https://job.sinopec.com", "official_recruitment_site", "2027校招及岗位入口已确认"),
    "中国石油天然气集团有限公司": ("campaign_open_verified", "https://zhaopin.cnpc.com.cn/", "official_recruitment_site", "2027校招入口已确认，岗位级抓取待补"),
    "国家电网有限公司": ("campaign_open_verified", "https://zhaopin.sgcc.com.cn", "official_recruitment_site", "2027招聘平台及多单位公告已确认"),
    "中国电信集团有限公司": ("campaign_open_verified", "https://job.chinatelecom.com.cn/wt/TELE/web/index", "official_recruitment_site", "官网明确2027校招、54家招聘单位及九类岗位"),
    "国家能源投资集团有限责任公司": ("campaign_open_verified", "https://zhaopin.chnenergy.com.cn/annc/showgg?id=6a152f40-7fe5-460e-ad37-0024acafd8c9", "official_campaign_announcement", "官网2027统招公告已确认，覆盖80余家子分公司"),
    "中国华能集团有限公司": ("campaign_open_verified", "https://zhaopin.chng.com.cn/CampusRecruit?aId=2000255", "official_recruitment_site", "官网2027校招入口及多单位岗位已确认"),
    "中国大唐集团有限公司": ("campaign_open_verified", "https://www.china-cdto.com/dthwtz/xwzx/jtxw/2026/9/I1552059660066881536.html", "official_campaign_announcement", "官网2027毕业生招聘公告已确认"),
    "中国华电集团有限公司": ("campaign_open_verified", "https://www.chd.com.cn/site/2/2026-09-14/b7dffff921ca499c90f84509cd272310.html", "official_campaign_announcement", "官网2027校园招聘公告已确认"),
    "中国核工业集团有限公司": ("campaign_open_verified", "https://cnnc.zhiye.com/campus/jobs", "official_recruitment_site", "2027校招入口已确认，岗位级抓取待补"),
    "中国航空工业集团有限公司": ("campaign_open_verified", "https://catic.zhiye.com/campus", "official_recruitment_site", "旗下中航国际2027校招岗位已确认"),
    "中国电子科技集团有限公司": ("campaign_open_verified", "https://cetccq.cetc.com.cn/zgdk/1593022/1592495/index.html", "official_campaign_announcement", "官网列出中国电科2027校园招聘启动公告"),
    "中国电子信息产业集团有限公司": ("campaign_open_verified", "https://campus.cec.com.cn/", "official_recruitment_site", "2027校招入口已确认"),
    "中国移动通信集团有限公司": ("campaign_open_verified", "https://job.10086.cn/touch/personal/job/?lid=101", "official_recruitment_site", "官网列出北京、四川、海南、山西等2027校招"),
    "中国铁塔股份有限公司": ("campaign_open_verified", "https://www.china-tower.com/Index/lists/catid/10.html", "official_campaign_announcement", "官网2027年秋季校园招聘已于2026-09-24启动"),
    "东风汽车集团有限公司": ("campaign_open_verified", "https://etp.dfmc.com.cn/jyxx/004002/004002001/20260828/617e734b-452e-4e20-ada2-90728fbe040d.html", "official_group_evidence", "集团官网采购公告确认2027届校园招聘项目；具体岗位入口待完整接入"),
    "中国建筑集团有限公司": ("campaign_open_verified", "https://hr.cscec.com/", "official_recruitment_site", "多家所属单位2027校招已启动，统一网申平台已确认"),
    "中国工商银行股份有限公司": ("campaign_open_verified", "https://job.icbc.com.cn/", "official_recruitment_site", "官网列出总行及集团2027年度校园招聘"),
    "中国银行股份有限公司": ("campaign_open_verified", "https://www.boc.cn/aboutboc/bi4/202609/t20260903_25689311.html", "official_campaign_announcement", "官网2027全球校园招聘已于2026-09-03发布"),
    "中国建设银行股份有限公司": ("campaign_open_verified", "https://job.ccb.com/cn/job/anno_list.html?isImpAnno=1", "official_recruitment_site", "官网列出总部、直属机构、分支机构及子公司2027校招"),
    "中国长江三峡集团有限公司": ("official_site_verified_campaign_pending", "https://www.ctg.com.cn/sxjt/rlzy71/rlzydt/index.html", "official_recruitment_site", "官网招聘栏目可达；截至核验时页面最新为2026届，不能据此判定无2027岗位"),
    "中国海洋石油集团有限公司": ("official_site_verified_campaign_pending", "https://www.cnooc.com.cn/zyzx/", "official_recruitment_site", "集团官网校园招聘入口可达；2027批次仍需从招聘系统核验"),
    "中国南方电网有限责任公司": ("official_site_verified_campaign_pending", "https://zhaopin.csg.cn/", "official_recruitment_site", "官方招聘平台可达；2027批次岗位级证据待补"),
    "中国铁道建筑集团有限公司": ("campaign_open_verified", "https://crchi.zhiye.com/", "official_subsidiary_recruitment_site", "所属铁建重工官网当前显示10个校园招聘职位"),
    "中国中车集团有限公司": ("campaign_open_verified", "https://www.crrcgc.cc/ckgf/128_7635/128_7706/index.html", "official_subsidiary_campaign_announcement", "所属中车长客官网2027校园招聘公告已发布"),
    "中国宝武钢铁集团有限公司": ("campaign_open_verified", "https://baowugroup-zhaopin.51job.com/", "official_recruitment_site", "集团招聘平台可达，旗下宝钢股份2027国宝生计划已启动"),
    "中粮集团有限公司": ("campaign_open_verified", "https://campus.51job.com/cofco", "official_campaign_site", "中粮集团2027届官方网申平台已开放"),
    "中国航空发动机集团有限公司": ("campaign_open_verified", "https://www.aecc.cn/?PC=PC", "official_campaign_announcement", "集团官网公告栏显示2027届校园招聘已于2026-07-30启动"),
    "中国兵器工业集团有限公司": ("campaign_open_verified", "https://zgbq2027.iguopin.com/", "official_joint_campaign_site", "中国兵器工业与兵器装备2027联合校招站已上线"),
    "中国兵器装备集团有限公司": ("campaign_open_verified", "https://zgbq2027.iguopin.com/", "official_joint_campaign_site", "中国兵器工业与兵器装备2027联合校招站已上线"),
    "中国航天科技集团有限公司": ("campaign_open_verified", "https://www.spacetalent.com.cn/", "official_recruitment_site", "2027届校园招聘已启动，岗位级入口为中国航天人才网"),
}


def main() -> None:
    source = json.loads(AUDIT.read_text(encoding="utf-8"))
    rows = []
    for old in source["enterprises"]:
        name = old["parent_group"]
        if name in VERIFIED:
            status, url, evidence_type, note = VERIFIED[name]
            campaign = status == "campaign_open_verified"
        elif old.get("status") == "full_sweep_completed":
            status = "full_sweep_completed"
            url = old.get("official_recruitment_url")
            evidence_type = "official_job_snapshot"
            note = "已完成岗位级全量扫描并保留原始快照"
            campaign = True
        else:
            status = "unverified"
            url = old.get("official_recruitment_url")
            evidence_type = None
            note = "尚未取得足够的2027官方证据；该状态不表示没有开放岗位"
            campaign = None

        rows.append({
            "parent_group": name,
            "campaign_status": status,
            "campaign_open": campaign,
            "official_evidence_url": url,
            "evidence_type": evidence_type,
            "evidence_note": note,
            "job_level_extraction_status": (
                "completed" if status == "full_sweep_completed" else
                "pending_full_extraction" if status == "campaign_open_verified" else
                "pending_verification"
            ),
            "included_in_current_corpus": old.get("included_in_capped_corpus", 0),
            "verified_at": "2026-10-07",
        })

    counts = Counter(r["campaign_status"] for r in rows)
    out = {
        "version": "2.0",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "scope_count": len(rows),
        "methodology": {
            "campaign_verification": "Official recruitment site or current 2027 announcement confirms recruitment activity.",
            "job_extraction": "Tracked separately; campaign confirmation does not imply complete job-level ingestion.",
            "negative_rule": "Missing URL, access failure, or no search result must never be labelled as no open jobs.",
        },
        "summary": dict(counts),
        "enterprises": rows,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["summary"], ensure_ascii=False))
    print(OUT)


if __name__ == "__main__":
    main()
