---
name: nature-academic-search
description: >-
  Use when users ask to 找文献、做文献检索、查论文、查临床试验、核验引用、去重文献、设计
  PubMed/MeSH 检索式、解析 DOI/PMID/PMCID/arXiv/OpenAlex/Semantic Scholar/NCT ID，
  或导出 RIS、BibTeX、NBIB、ENW；also use for multi-source academic search,
  citation verification, trial registration search, and reference management.
---

# Academic Paper Search

使用捆绑的 MCP 服务组织可复现检索。把记录当作待核验的证据，不凭空补齐论文、引用或试验信息。

## 任务路由

| 用户目标 | 工具或路径 | 完成标准 |
|---|---|---|
| 找文献、文献检索、综述初筛 | `search_papers` | 按来源检索、去重并披露部分失败 |
| 查临床试验注册 | `search_papers` + `entity_type="trial"` | 返回 trial 记录，不与论文合并 |
| 核验标识符 | `get_paper_by_id` | 对照题名、作者/申办方、年份和标识符 |
| 生成论文引用 | `get_citation` | 只格式化已解析论文；NCT 注册不生成论文引用 |
| 构建 PubMed 检索式 | `lookup_mesh` | 先确认 MeSH，再组合自由词 |
| 批量导出引用文件 | 包 CLI | 读取[引用文件流程](references/citation-files.md) |

客户端可能给工具名添加 MCP 前缀；按名称后缀识别，工具总数仍为四个。

## 来源角色

- 默认论文源：`crossref`、`pubmed`、`arxiv`、`openalex`、`europe_pmc`。
- 显式论文源/补充富化：`semantic_scholar`；仅用 DOI、PMID、arXiv 等强标识符富化。
- 试验注册源：`clinicaltrials_gov`；只用于 `entity_type="trial"`，不是论文数据库。

按任务选源、过滤和凭据规则见[来源分层](references/source-tiers.md)。未连接 Google Scholar、
Web of Science、Scopus、Embase、CNKI、万方，不得声称检索过这些数据库。

## 执行流程

1. 明确主题、日期、文献类型、结果数、是否接受预印本，以及目标是论文还是试验注册。
2. 论文检索默认调用五源；只有用户要求或确有强标识符时才显式搜索/富化 Semantic Scholar。
3. 检查 `sources_queried`、`sources_succeeded`、`sources_skipped`、`errors`、
   `raw_result_count`、`result_count`。实际工具输出才证明某来源被查询。
4. 对拟引用、标识符冲突或元数据可疑记录调用 `get_paper_by_id`。
5. 标记 `verified`、`mismatch`、`not_found` 或 `manual_needed`，冲突逐字段说明。
6. 分开报告正式论文、预印本、trial 和未解决记录。trial 永不按题名与 publication 合并。
7. 单条引用使用 `get_citation`；批量导出前排除或单列未核验记录。

详细查询构建、部分成功和核验规则见[检索工作流](references/search-workflows.md)。

## 结果契约

报告原始/修订查询、检索日期与截止日期、纳入规则、请求来源、`sources_queried`、
`sources_succeeded`、`sources_skipped`、`errors`、去重前后数量、实体类型、标识符、
`sources`/`source_records`、冲突和核验状态。引用次数必须保留 `citation_counts` 与
`citation_count_source`，不得合成无来源的“总引用数”。

每次成功的 `search_papers` 还返回 `search_run`：其中的 `run_id`、UTC 时间、请求参数、
去重前后数量和 `result_fingerprint` 用于保存可复现的 `run.json`。每条最终记录带稳定的
`record_id`；它不是来源标识符的替代品，而是跨次检索比较记录的本地键。

需要缩小检索范围时，给 `search_papers` 传入统一的 `filters` 对象：`date_from`、`date_to`
（`YYYY-MM-DD`）、`language`、`author`、`document_type`（字符串或列表）和 `identifiers`。
系统会为 CrossRef、PubMed、OpenAlex、Europe PMC、arXiv 生成源原生查询；不能由源可靠表达的
字段由本地严格过滤，未知字段或反向日期直接报错。传入 `ranking="relevance"`，或传入 filters
后省略 ranking，会启用固定 `score_version` 的本地相关性排序，并在记录中写入
`ranking_score` / `ranking_reasons`；它只表示检索相关性，不表示证据质量。`ranking="none"`
保留过滤后的来源顺序。完整的字段翻译与边界见[检索工作流](references/search-workflows.md)。

需要核验已有引用时，把题名、作者、年份、期刊或标识符放入 `get_paper_by_id` 的可选
`expected` 对象。工具会返回字段级 `verified`、`mismatch`、`not_found` 或 `manual_needed`。
没有传 `expected` 时，不能把搜索结果自动称为已核验；`mismatch` 和 `manual_needed` 不得
静默进入已核验引用集合。

## 证据规则

- 不编造元数据、摘要、引用次数、标识符、开放获取状态、全文结论或试验结果。
- 优先按强标识符合并；弱题名匹配必须限定同一 `entity_type` 并保留冲突。
- 不把预印本描述为同行评审论文，不把 trial 注册描述为已发表研究。
- 无结果时不静默放宽查询；来源失败时保留成功结果并说明缺口。
