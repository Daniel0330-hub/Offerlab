# 校招岗位与匹配数据结构 v0.3

## CandidateProfile

- `graduation_year`、`degree`、`majors`、`target_locations`、`accepts_rotation`；
- `target_domains`：目标职责或业务方向；
- `skills[]`：`name`、`normalized_name`、`level`、`evidence`；
- `experiences[]`：项目、实习或研究经历。

## JobPosting

- 基础字段：`job_id`、`company`、`recruitment_program`、`title`、`location`；
- `normalized_job_family[]`：归一岗位族，可多选；
- `responsibilities_raw`、`requirements_raw`：JD 原文；
- `responsibilities[]`：结构化职责及证据；
- `skill_requirements[]`：`name`、`normalized_name`、`level`、`evidence_span`；
- `base_requirements[]`：届次、学历、专业等基础条件；
- `other_explicit_conditions[]`：语言证书等其他明示条件；
- `source_url`、`collected_at`。

技能要求级别使用 `required/expected/preferred/exposure`。

## RetrievalResult

- `base_filter_status`：`pass/fail/unknown`；
- `responsibility_score`、`skill_score`、`domain_score`、`title_score`；
- `retrieval_score`：按实验权重合成；
- `matched_responsibilities[]`、`matched_skills[]`：命中项及原文；
- `retrieval_reason[]`：面向用户的召回原因。

初始实验权重为职责 40%、技能 35%、专业/领域 15%、名称 10%。

## QualificationAssessment

- `base_checks[]`：基础资格判断；
- `skill_checks[]`：技能覆盖判断；
- `other_condition_checks[]`：其他明确条件；
- `overall_status`：`eligible/risky/ineligible/unknown`；
- `warnings[]`：风险和信息不足。

每项判断必须包含 `status`、`job_evidence`、`candidate_evidence` 和 `reason`，不得只保存综合分。

## ComparisonSet 与 UserDecision

- `ComparisonSet`：`comparison_id`、`candidate_id`、`job_ids`（2–3 个）、`created_at`；
- `UserDecision`：`job_id`、`decision`（apply/backup/drop）、`reason`、`decided_at`。
