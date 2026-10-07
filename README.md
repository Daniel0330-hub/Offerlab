# OfferLab

OfferLab 是一个面向应届生的央国企校招岗位发现与比较实验项目。用户填写专业、技能、项目经历、目标方向和意向地点后，系统会从已收集的岗位中筛选候选岗位，并根据岗位 JD 展示资格、优势、技能缺口和原文证据。

在线体验：<https://daniel0330-hub.github.io/Offerlab/>

## 已实现功能

- 能力画像：记录毕业年份、学历、专业、技能、项目经历、目标方向和工作地点；
- 简历导入：支持 TXT、Markdown 和 JSON 文本的本地解析；
- 能力识别：识别 Python、SQL、Java、C、C++ 等技能，并从专业和项目经历推断可迁移能力；
- 岗位推荐：根据目标方向、技能、项目、专业和地点对岗位进行筛选和排序；
- 资格判断：区分毕业年份、学历、专业等基础资格与具体技能要求；
- JD 详情：展示推荐理由、职责、技能要求、能力优势、待补技能和原始岗位链接；
- 岗位比较：支持同时比较 2–3 个岗位；
- 推荐评测：支持对 Top 10 岗位进行 2/1/0 三级相关性标注并导出 JSON。

## 当前数据

- 原型展示目录：259 条岗位，覆盖 18 家央企集团，每集团最多 50 条；
- 已完成官方全量扫描：6 家集团，共读取 5,216 条原始岗位；
- 首轮真实用户评测：3 名用户、30 条相关性判断；
- P3 的 Precision@10 从 v0.1 的 20% 提升到 v0.3 的 80%；
- v0.3 P3 NDCG@10 为 94.60%；
- 能力推断测试为 10/10。

当前岗位是截至 2026 年 10 月的实验快照，不代表所有岗位仍在开放，也不代表所有央国企已经完成全量采集。

## 匹配方法

系统使用字符 2–4 gram TF-IDF、同义词、字段权重、资格规则和能力映射完成匹配。岗位名称只作为一个信号，职责、技能、专业和资格字段会共同参与筛选。

画像与 JD 的匹配分为：

1. 基础资格判断；
2. 目标方向匹配；
3. 明确技能匹配；
4. 专业与项目经历产生的可迁移能力；
5. 意向地点约束；
6. 优势、缺口和 JD 证据生成。

## 本地运行

```bash
python3 -m http.server 8000 --directory prototype
```

浏览器打开 <http://127.0.0.1:8000>。也可以直接打开 `prototype/index.html`。

## 检查与评测

```bash
# 能力推断测试
python3 scripts/validate_capability_inference.py

# 汇总原型导出的相关性标注
python3 scripts/evaluate_user_relevance.py P01.json P02.json \
  --output data/evaluation/user-relevance-results-local.json

# 上传前检查JSON、文档链接、敏感信息和忽略规则
python3 scripts/public_release_audit.py
```

## 目录

```text
prototype/                  本地原型
data/catalog/               原型使用的岗位目录
data/evaluation/            开发集、测试集和用户标注结果
data/sources/               岗位来源、采集快照和企业核验记录
docs/01-user-research/      用户研究
docs/02-product-definition/ 产品定义与竞品分析
docs/03-design/             PRD、指标和数据结构
docs/04-ai-design/          匹配方案、规则和Schema
docs/05-validation/         数据采集与评测报告
docs/06-iteration/          版本迭代记录
scripts/                    采集、处理和评测脚本
```

项目介绍见 [PROJECT_DESCRIPTION.md](docs/PROJECT_DESCRIPTION.md)，完整过程见 [PROJECT_LOG.md](docs/PROJECT_LOG.md)。

## 限制

- 部分招聘网站需要专用接口适配器，当前企业覆盖并不完整；
- 展示目录受每集团 50 条上限影响；
- 当前真实用户样本较少，v0.3 重点复测来自一个 AI 产品方向画像；
- 专业相关性、岗位资格和技能抽取仍可能存在误判；
- 项目不自动投递，也不预测录取概率。
