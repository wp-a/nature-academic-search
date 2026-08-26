---
name: nature-academic-search
description: >-
  Use when users ask to 找文献、做文献检索、查论文、查临床试验、核验引用、去重文献、设计
  PubMed/MeSH 检索式、追踪上下游引文、解析 DOI/PMID/PMCID/arXiv/OpenAlex/Semantic Scholar/NCT ID，
  或导出 RIS、BibTeX、NBIB、ENW；also use for multi-source academic search,
  citation verification, citation graphs, trial registration search, and research workflows.
---

# Academic Paper Search

## 什么时候触发

用户提到找文献、文献检索、引用核验、引文图谱、MeSH、PubMed、预印本、临床试验、RIS/BibTeX
或 DOI/PMID/PMCID/arXiv/OpenAlex/Semantic Scholar/NCT 时触发本 skill。目标是论文时使用
`entity_type="publication"`；目标是注册试验时使用 `entity_type="trial"`，两者不能按题名合并。

## 任务路由

以下工具路由以实际工具输出为准；适配器存在不代表本次已经查询。

| 用户目标 | 入口 | 执行要求 |
|---|---|---|
| 找文献、综述前期检索 | `search_papers` | 按源检索、去重，报告 `sources_queried` / `sources_succeeded` / `sources_skipped` / `errors` |
| 核验已有引用 | `get_paper_by_id` + `expected` | 输出字段级 `verified`、`mismatch`、`not_found` 或 `manual_needed` |
| 追踪上下游引文 | `get_paper_by_id(include_relations=true)` | 默认 `depth=1`；需要二跳时显式 `depth=2`，保留图谱边和来源缺口 |
| 构建 PubMed 检索式 | `lookup_mesh` | 先核对 MeSH 词和 ID，再组合自由词；不要凭空猜主题词 |
| 生成单条引用 | `get_citation` | 只格式化已解析论文；NCT 注册不生成论文引用 |
| 批量导出或自动化 | CLI `citation` / `workflow` | 保留 `run.json`、核验状态和人工待处理清单 |

客户端可能给工具名添加 MCP 前缀；工具总数仍为四个，不新增专用图谱工具。

## 来源与边界

- 默认论文源：`crossref`、`pubmed`、`arxiv`、`openalex`、`europe_pmc`。
- `semantic_scholar` 用于显式搜索、`enrich` 或图谱；富化优先使用 DOI、PMID、arXiv 等强标识符。
- OpenAlex 提供跨学科 references / cited_by；PubMed ELink 提供生物医学双向关系。
- Crossref 与 Europe PMC 主要提供 references；arXiv 目前只作为节点和版本线索。
- `clinicaltrials_gov` 只服务 `entity_type="trial"`，不是论文数据库。
- 未连接 Google Scholar、Web of Science、Scopus、Embase、CNKI、万方，不得声称覆盖这些来源。

源失败、限流、缺少强标识符或不支持某方向时，保留成功结果并记录缺口；不能把未查询到解释成没有关系。

## 引文图谱契约

调用 `get_paper_by_id` 时可以传：

```json
{
  "include_relations": true,
  "relation": "both",
  "depth": 1,
  "rows": 20,
  "relation_sources": ["openalex", "crossref", "pubmed", "europe_pmc", "semantic_scholar"]
}
```

`relation` 是 `references`、`cited_by` 或 `both`。输出 `citation_graph` 必须保留：

- `nodes`：合并后的 publication 节点和来源记录；
- `edges`：统一为 citing → cited，含 `relation` 与 `observed_by`；
- `sources_queried`、`sources_succeeded`、`sources_skipped`、`errors`；
- `truncated`、`truncation_reason`、`depth_completed`。

`references` 表示种子指向被引用节点，`cited_by` 表示引用者指向种子。图谱是关系导航和审计数据，
不是证据质量、因果关系、影响力或研究结论评分。

## 标准执行顺序

1. 明确主题、人群/系统、干预、结局、日期、文献类型、预印本政策和实体类型。
2. 生物医学问题先用 `lookup_mesh` 核验主题词，再组合题名/摘要自由词。
3. 调用 `search_papers`；保存原查询、日期、请求源、结果数量和 `search_run`。
4. 按 DOI、PMID、PMCID、arXiv、OpenAlex、Semantic Scholar 或 NCT 强标识符去重；弱题名匹配保留冲突。
5. 对拟引用记录调用 `get_paper_by_id` + `expected`，逐项核对题名、首位作者、年份、期刊和标识符。
6. 需要时追加一跳引文图谱；二跳、`rows` 和源列表必须有明确研究目的和预算。
7. 按 verified、mismatch、not_found、manual_needed、preprint、trial 分组交付；未核验记录不能静默导出。
8. 批量任务使用 workflow，先生成 `plan.json`，获得批准后再检索，并保存 `run.json`、`results.json`、
   `verification.json`、`screening.csv`、`references.ris` 和可选 `graph.json`。

## WPIRONMAN 中转

WPIRONMAN 是可选的 OpenAI-compatible 模型入口，适合 workflow 的 plan、摘要级 screen 或规则整理；
它不是论文来源、数据库、引用验证器，也不替代 Crossref、PubMed、OpenAlex、Europe PMC 或 Semantic Scholar。

```bash
export ACADEMIC_SEARCH_LLM_BASE_URL=https://api.wpironman.top/v1
export ACADEMIC_SEARCH_LLM_API_KEY=你的中转密钥
export ACADEMIC_SEARCH_LLM_MODEL=你的模型名
export ACADEMIC_SEARCH_LLM_PROTOCOL=responses_http
```

默认只发送标题、摘要、标识符和获准元数据；全文必须显式设置 `privacy.allow_full_text: true`。
密钥不得进入日志、manifest 或 prompt artifact。中转超时、限流或返回坏 JSON 时，最多重试一次，
随后将模型步骤标记为 `skipped`，学术检索、核验和导出继续。

## 结果契约

每次成功的 `search_papers` 返回 `search_run`，至少保存 `run_id`、UTC 时间、请求参数、去重前后数量和
`result_fingerprint`。每条记录保留稳定 `record_id`、`sources`、`source_records`、`conflicts`、
`citation_counts` 和 `citation_count_source`。不得合成没有来源的“总引用数”。

统一 `filters` 支持日期、语言、作者、文献类型和强标识符；`ranking` 可设为 `relevance` 或 `none`。
相关性排序会写入 `ranking_score`、`ranking_reasons` 和 `score_version`，只表示检索相关性，不表示证据质量。

详细查询构建、来源分层、引用文件和工作流见：

- [检索工作流](references/search-workflows.md)
- [来源分层](references/source-tiers.md)
- [引用文件](references/citation-files.md)

## 证据规则

- 不编造元数据、摘要、引用次数、标识符、开放获取状态、全文结论或试验结果。
- 不把预印本描述为同行评审论文，不把 trial 注册描述为已发表研究。
- 不因为来源适配器存在就声称它本次已查询；以实际 `sources_queried` 为准。
- 不把引用数量、图谱度数或模型排序当作证据质量或因果证据。
