# 校招岗位数据结构 v0.2

> 历史版本：已由 `job-data-schema-v0.3.md` 取代。

## 设计目标

支持资格逐项举证、岗位横向比较和集团有限志愿判断。所有归一化字段均保留原始文本和来源。

## UserProfile

| 字段 | 类型 | 说明 |
|---|---|---|
| `user_id` | string | 脱敏用户标识 |
| `graduation_cohort` | integer | 毕业届次 |
| `education_level` | enum | bachelor/master/doctor |
| `graduate_major` | string | 最高学历专业原文 |
| `undergraduate_major` | string/null | 本科专业原文 |
| `language_scores` | array | TOEFL、CET 等原始成绩，不自动换算 |
| `preferred_locations` | array | 目标地点 |
| `rotation_accepted` | boolean/null | 是否接受轮岗 |
| `skills` | array | 用户技能 |
| `target_job_families` | array | 目标岗位族 |
| `preferences` | object | 地点、职责等主观偏好 |

## CompanyAndOrganization

| 字段 | 类型 | 说明 |
|---|---|---|
| `group_id` | string | 集团标识 |
| `group_name` | string | 集团名称 |
| `organization_id` | string | 实际招聘单位标识 |
| `organization_name` | string | 分子公司/单位名称 |
| `business_segment` | string/null | 省公司、专业公司、油田、炼化、科研等 |

## RecruitmentCampaign

| 字段 | 类型 | 说明 |
|---|---|---|
| `campaign_id` | string | 招聘项目标识 |
| `campaign_name` | string | 如 2027 年秋季校园招聘 |
| `recruitment_type` | enum | campus/intern/social/unknown |
| `graduation_cohorts` | array | 面向届次 |
| `application_limit_type` | enum | per_group/per_organization/per_campaign/unknown/none |
| `max_applications` | integer/null | 最大志愿数量 |
| `max_organizations` | integer/null | 最大单位数量 |
| `slot_lock_behavior` | enum | locked_until_result/editable/unknown/not_applicable |
| `application_rule_raw` | text/null | 官网规则原文 |
| `application_rule_source_url` | string/null | 规则来源 |
| `application_rule_verified_at` | datetime/null | 规则核验时间 |

## JobPosting

| 字段 | 类型 | 说明 |
|---|---|---|
| `job_id` | string | 内部唯一标识 |
| `source_job_id` | string/null | 来源系统岗位编号 |
| `group_id` | string | 所属集团 |
| `organization_id` | string | 招聘单位 |
| `campaign_id` | string | 招聘项目 |
| `raw_title` | string | 官网原始岗位名称 |
| `normalized_job_family` | string/null | 归一化岗位族 |
| `locations` | array | 工作地点 |
| `education_levels` | array | 学历要求 |
| `accepted_majors_raw` | text/null | 专业要求原文 |
| `accepted_major_groups` | array | 辅助筛选用专业组 |
| `responsibilities_raw` | text | 原始职责 |
| `requirements_raw` | text | 原始要求 |
| `responsibility_themes` | array | 归一化职责主题 |
| `skill_requirements` | array | 明确技能 |
| `language_requirements` | array | 英语等要求 |
| `other_hard_requirements` | array | 其他硬性条件 |
| `headcount` | integer/null | 招聘人数 |
| `published_at` | datetime/null | 发布时间 |
| `deadline_at` | datetime/null | 截止时间 |
| `source_url` | string | 官方详情/投递入口 |
| `source_domain` | string | 来源域名 |
| `last_verified_at` | datetime | 最后核验时间 |
| `source_status` | enum | active/expired/broken/needs_recheck |
| `raw_snapshot` | text | 原始页面文本快照 |

## CriterionAssessment

每个岗位与用户的每项资格生成一条记录。

| 字段 | 类型 | 说明 |
|---|---|---|
| `assessment_id` | string | 唯一标识 |
| `job_id` | string | 岗位 |
| `user_id` | string | 用户 |
| `criterion` | enum | recruitment_type/cohort/education/major/language/location/other |
| `status` | enum | pass/fail/unknown/not_applicable |
| `mandatory` | boolean | 是否为强制条件 |
| `job_evidence_text` | text/null | JD 原文证据 |
| `user_evidence_text` | text/null | 用户证据 |
| `explanation` | text | 简短解释 |
| `rule_id` | string/null | 命中的确定性规则 |
| `needs_human_review` | boolean | 是否需人工核实 |

## EligibilitySummary

| 字段 | 类型 | 说明 |
|---|---|---|
| `job_id` | string | 岗位 |
| `user_id` | string | 用户 |
| `overall_status` | enum | eligible/ineligible/needs_review |
| `failed_criteria` | array | 明确不符合项 |
| `unknown_criteria` | array | 待核实项 |
| `generated_at` | datetime | 生成时间 |

## RelevanceAssessment

| 字段 | 类型 | 说明 |
|---|---|---|
| `job_id` | string | 岗位 |
| `user_id` | string | 用户 |
| `triggered_by` | array | 专业、技能、项目、偏好或搜索词 |
| `matched_evidence` | array | 用户证据 |
| `evidence_gaps` | array | 尚未证明的能力 |
| `uncertainties` | array | 无法判断事项 |
| `summary` | text | 不含录取概率的解释 |

## ComparisonSet

| 字段 | 类型 | 说明 |
|---|---|---|
| `comparison_id` | string | 比较集合 |
| `user_id` | string | 用户 |
| `job_ids` | array | 2–3 个岗位 |
| `slot_usage_by_group` | object | 各集团当前选择与上限 |
| `created_at` | datetime | 创建时间 |

## UserDecision

| 字段 | 类型 | 说明 |
|---|---|---|
| `user_id` | string | 用户 |
| `job_id` | string | 岗位 |
| `decision` | enum | priority/backup/skip/undecided |
| `reason_codes` | array | 地点、职责、资格、企业等理由 |
| `reason_text` | text/null | 用户补充理由 |
| `updated_at` | datetime | 更新时间 |

## 关键约束

1. 原始岗位名、专业原文和 JD 快照不得被归一化结果覆盖；
2. 缺失信息使用 `null/unknown`，不得由模型补全；
3. 所有确定资格状态必须有原文证据；
4. 硬性资格与相关性分开存储；
5. 志愿规则未知时不得假设无限投递；
6. 用户决定不修改系统资格结果，系统建议也不覆盖用户决定；
7. 失效来源必须标记并停止作为确定依据。
