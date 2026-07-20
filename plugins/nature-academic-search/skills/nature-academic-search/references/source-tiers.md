# 来源角色、覆盖与可靠性

来源按“默认论文源、显式补充源、独立 trial 源”路由。层级表示职责，不表示某一来源绝对更准确；
最终判断必须回到记录标识符、来源追踪和原始页面。

## 默认论文源

| source 参数 | 主要用途 | 强标识符/特征 | 边界 |
|---|---|---|---|
| `crossref` | DOI、出版商元数据、格式化引用 | DOI | 覆盖不等于完整学科检索 |
| `pubmed` | 生物医学索引、PMID、MeSH | PMID、记录 DOI | 不代表可获得全文 |
| `arxiv` | 预印本、版本线索 | arXiv ID | 预印本不等于同行评审论文 |
| `openalex` | 跨学科发现、开放获取与引用指标 | OpenAlex ID、DOI/PMID | 引用次数仅代表 OpenAlex 口径 |
| `europe_pmc` | 生物医学补充、PMCID、开放全文线索 | PMID、PMCID、DOI | 与 PubMed 重叠但字段不完全相同 |

`search_papers` 在 `entity_type="publication"` 且省略 `sources` 时调用以上五源。显式传入旧的
`["crossref", "pubmed", "arxiv"]` 时只查询这三源，不自动扩展。

## 显式补充源

| source 参数 | 使用方式 | 约束 |
|---|---|---|
| `semantic_scholar` | 显式 `sources` 搜索，或 `enrich=["semantic_scholar"]` | 富化只使用 DOI、PMID、arXiv 等强标识符；缺少强 ID 时跳过，不做题名猜测 |

Semantic Scholar API key 可选，但无 key 时速率和可用性更受限。预检缺少 key 会将该凭据检查标为
`SKIP`；不能把“适配器存在”写成“本次已检索”。

## 独立 trial 源

| source 参数 | 实体类型 | 主要字段 |
|---|---|---|
| `clinicaltrials_gov` | `trial` | NCT ID、状态、条件、干预、申办方、入组数、地点、日期 |

调用 trial 搜索时使用 `entity_type="trial"`。ClinicalTrials.gov 返回的是试验注册，不是论文；
`get_citation` 不会为 NCT 注册伪造论文引用。关联 PMID 只作为 `linked_publications` 线索，需另行核验。

## 来源状态

- `sources_queried`：确实尝试发送请求的来源。
- `sources_succeeded`：返回有效响应的来源，包括零结果。
- `sources_skipped`：未执行的富化或记录级跳过及原因。
- `errors`：已尝试但失败的来源；失败不删除其他来源结果。
- `source_meta`：来源级速率、成本或数据版本等可用元数据。

配置文件、环境变量或注册表只能说明“可用/已配置”；实际工具输出才证明某来源在本次被查询。

## 指标与溯源

合并记录保留 `sources` 和 `source_records`。引用次数保留 `citation_counts` 映射，并用
`citation_count_source` 标明兼容字段 `citation_count` 的来源。不同数据库的计数口径不得相加，
也不得描述成统一、实时或绝对值。

## 未连接来源

本项目未连接 Google Scholar、Web of Science、Scopus、Embase、CNKI、万方。用户需要这些来源时，
明确说明缺口，并建议使用机构订阅或人工检索；不要生成虚构工具调用或声称已覆盖。
