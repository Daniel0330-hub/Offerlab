# 校招岗位数据结构 v0.1

> 本版本已由 `job-data-schema-v0.2.md` 替代。v0.2 新增招聘项目、集团有限志愿、比较集合和用户决定结构。

## 设计目标

统一六家央企不同招聘系统中的岗位字段，同时保留原始信息和证据来源。结构化字段用于筛选与比较，原始文本用于核验，二者不能互相替代。

## 核心实体

### Company

| 字段 | 类型 | 说明 |
|---|---|---|
| `company_id` | string | 集团或公司唯一标识 |
| `company_name` | string | 集团名称 |
| `organization_name` | string | 实际招聘的分子公司/单位 |
| `business_segment` | string/null | 省公司、专业公司、油田、炼化、销售、科研等 |

### JobPosting

| 字段 | 类型 | 说明 |
|---|---|---|
| `job_id` | string | 内部唯一标识 |
| `source_job_id` | string/null | 来源系统岗位编号 |
| `raw_title` | string | 官网原始岗位名称 |
| `normalized_job_family` | string/null | 归一化岗位族，须保留生成依据 |
| `recruitment_type` | enum | campus/intern/social/unknown |
| `recruitment_project` | string/null | 如 2027 年秋季校园招聘 |
| `graduation_cohorts` | array | 面向届次；无法确认则为空并标记待核实 |
| `education_levels` | array | 本科、硕士、博士等 |
| `accepted_majors_raw` | string/null | 官网专业要求原文 |
| `accepted_major_groups` | array | 归一化专业组 |
| `locations` | array | 工作地点 |
| `headcount` | integer/null | 招聘人数 |
| `responsibilities_raw` | string | 原始职责 |
| `requirements_raw` | string | 原始任职要求 |
| `responsibility_themes` | array | 归一化职责主题 |
| `skill_requirements` | array | 明确要求的技能 |
| `language_requirements` | array | 英语等级等要求 |
| `other_hard_requirements` | array | 政治面貌、证书等条件 |
| `application_limit_rule` | string/null | 投递单位/岗位数量限制 |
| `published_at` | datetime/null | 发布时间 |
| `deadline_at` | datetime/null | 截止时间 |
| `source_url` | string | 官方详情或投递入口 |
| `source_domain` | string | 来源域名 |
| `last_verified_at` | datetime | 最后核验时间 |
| `raw_snapshot` | text | 原始页面文本或结构化快照 |

### EligibilityAssessment

| 字段 | 类型 | 说明 |
|---|---|---|
| `job_id` | string | 对应岗位 |
| `user_id` | string | 对应用户 |
| `cohort_status` | enum | pass/fail/unknown |
| `education_status` | enum | pass/fail/unknown |
| `major_status` | enum | pass/fail/unknown |
| `language_status` | enum | pass/fail/unknown |
| `location_status` | enum | pass/fail/unknown |
| `overall_status` | enum | eligible/ineligible/needs_review |
| `evidence` | array | 每项判断对应的 JD 原文 |

### RelevanceAssessment

只有资格状态不是 `ineligible` 时才生成。

| 字段 | 类型 | 说明 |
|---|---|---|
| `job_id` | string | 对应岗位 |
| `user_id` | string | 对应用户 |
| `triggered_by` | array | 专业、课程、项目、技能、偏好或主动搜索词 |
| `matched_evidence` | array | 用户经历与岗位要求的对应证据 |
| `evidence_gaps` | array | 用户尚未证明的能力 |
| `uncertainties` | array | 无法从现有信息判断的事项 |

## 关键约束

1. `raw_title` 不得被归一化名称覆盖。
2. `accepted_majors_raw` 必须保存原文，专业归一化仅用于辅助筛选。
3. 缺失字段使用 `null/unknown`，不得由模型擅自补全。
4. 所有资格判断必须附带原始证据。
5. 来源失效或超过设定核验期限时，岗位显示“需要重新核验”。
6. 资格筛选与相关性排序分开计算。
