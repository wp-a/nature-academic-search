# 检索工作流

## 1. 先定义实体与范围

先确认研究概念、日期范围、文献类型、结果数量、语言和是否接受预印本。再确认目标实体：

- 论文与预印本：`entity_type="publication"`（默认）。
- ClinicalTrials.gov 试验注册：`entity_type="trial"`。

两种实体分开检索、分开报告，禁止只凭相同题名合并。

## 2. 构造查询

1. 把问题拆成人群/系统、干预或暴露、比较、结局、方法和排除项。
2. 为每个概念建立同义词组。
3. 生物医学主题先用 `lookup_mesh` 核验 MeSH，再组合题名/摘要自由词。
4. 保存人类可读的原查询。PubMed 字段语法不能原样复制给其他来源。
5. 只在用户要求或范围需要时添加日期、类型和语言过滤。

### 2.1 统一过滤与排序

`search_papers` 接受统一的 `filters` 对象：

```json
{
  "date_from": "2022-01-01",
  "date_to": "2024-12-31",
  "language": "en",
  "author": "Jane Doe",
  "document_type": ["journal-article"],
  "identifiers": ["10.1000/example"]
}
```

系统会把日期、作者、语言和文献类型翻译到各源的原生表达：CrossRef 使用 publication
date、author 和 type；PubMed 使用 Date/Author/Language/Publication Type 字段；OpenAlex
使用 publication date、language、author.search 和 type；Europe PMC 使用 FIRST_PDATE、
LANGUAGE、AUTHOR、PUB_TYPE；arXiv 使用已有的 submittedDate 范围。源不支持或返回字段不足时，
本地过滤仍会严格执行；缺失必要字段的记录不会假装命中。`identifiers` 始终在合并后按强标识符
过滤。

传入 `ranking="relevance"` 会使用固定 `score_version` 的本地算法：题名、摘要、主题词的
权重固定，精确标识符命中优先，最后按 `record_id` 稳定打破平分。传入 filters 而省略 ranking
默认启用该排序；`ranking="none"` 保留过滤后的来源顺序。`ranking_score` 仅代表检索相关性，
不得当作证据质量或引用真实性。`search_run.filters`、`search_run.ranking` 和
`search_run.source_translation` 应与 `run.json` 一起保存。

## 3. 选择来源

论文检索省略 `sources` 时默认查询 `crossref`、`pubmed`、`arxiv`、`openalex`、
`europe_pmc`。范围明确时可显式传入子集；显式三源调用保持三源，不会静默扩展。

`semantic_scholar` 有两种使用方式：

- 显式搜索：`sources=["semantic_scholar"]`；
- 去重后富化：`enrich=["semantic_scholar"]`。

富化只使用 DOI、PMID、arXiv 等强标识符。没有强 ID 的记录进入 `sources_skipped`，不做题名推测。

试验注册使用 `search_papers(..., entity_type="trial")`，默认只查询 `clinicaltrials_gov`。
publication 与 trial 源混用会被拒绝。

## 4. 检查部分成功

每次调用都检查：

- `sources_queried`：实际尝试的来源；
- `sources_succeeded`：有效响应，包括零结果；
- `sources_skipped`：未执行的富化及原因；
- `errors`：请求失败来源；
- `raw_result_count` / `result_count`：去重前后数量；
- `source_meta`：来源级速率、成本或版本元数据。

保留成功记录，只重试失败来源。不要因为代码中存在适配器，就声称该来源在本次被查询。

每次成功运行还会返回 `search_run`。保存完整 JSON 响应作为 `run.json`，至少保留
`run_id`、UTC 时间、请求来源、去重前后数量和 `result_fingerprint`。每条最终记录的
`record_id` 用于跨次运行比较，不替代 DOI、PMID 或来源 URL。

## 5. 去重与冲突

先按同一 `entity_type` 内的 DOI、PMID、PMCID、arXiv、OpenAlex、Semantic Scholar 或 NCT ID
合并，再使用标准化题名与年份作为弱回退。保留 `sources`、`source_records` 和 `conflicts`；
不得用一个来源的冲突值静默覆盖另一个来源。

引用次数保留 `citation_counts` 和 `citation_count_source`。不同来源计数不相加；排序时必须注明采用的来源。

## 6. 核验与引用

对进入论文、建议或导出的记录：

1. 用 `get_paper_by_id` 解析 DOI、PMID、PMCID、arXiv、OpenAlex 或 Semantic Scholar ID。
2. 比较题名、首位作者、期刊/平台、年份和标识符。
3. 标记 `verified`、`mismatch`、`not_found` 或 `manual_needed`。
4. 有 DOI 时 `get_citation` 优先使用 CrossRef 格式化；无 DOI 时返回基础引用并标明 `metadata_source`。
5. NCT 是试验注册，不生成论文引用；其关联 PMID 需作为论文另行解析。

`get_paper_by_id` 可以接收 `expected` 元数据并返回字段级状态。只有 `verified` 记录才能
默认进入已核验引用集合；`mismatch`、`not_found` 和 `manual_needed` 必须保留在单独的
待处理清单中。

## 7. 结果报告

报告原始及修订查询、检索日期和截止日期、纳入/排除规则、来源状态、唯一结果、标识符、
来源追踪、指标来源与核验状态。分开列出正式论文、预印本、trial 和未解决记录。

本项目未连接 Google Scholar、Web of Science、Scopus、Embase、CNKI、万方；需要这些数据库时明确提示人工或机构检索。
