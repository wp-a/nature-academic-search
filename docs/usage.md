# CLI 与 MCP 使用指南

[返回首页](../README.md) · [安装与配置](installation.md) · [批量工作流](../references/search-workflows.md#23-声明式科研工作流)

## 工具与命令

### 四个 MCP 工具

客户端可能添加工具名前缀。以下为服务端名称：

| 工具 | 用途 | 关键参数 |
|---|---|---|
| `search_papers` | 多源检索、去重、过滤与相关性排序 | `query`、`sources`、`rows`、`filters`、`ranking`、`entity_type`、`enrich` |
| `get_paper_by_id` | 解析标识符；可选字段核验和引文图谱 | `id`、`id_type`、`expected`、`include_relations`、`relation`、`depth`、`relation_sources` |
| `get_citation` | 生成单条格式化引用 | `id`、`id_type`、`style`，如 `apa`、`nature`、`vancouver` |
| `lookup_mesh` | 查询 MeSH 规范主题词 | `term` |

支持 DOI、PMID、PMCID、arXiv、OpenAlex、Semantic Scholar 和 NCT 等标识符；
原始 Semantic Scholar ID 应显式指定 `id_type="semantic_scholar"`。
NCT 用于试验查询，不生成论文引用。图谱通过 `get_paper_by_id` 返回，不需要额外安装工具。

<details>
<summary><strong>MCP 参数示例：日期过滤、字段核验、引文图谱</strong></summary>

以下是传给相应 MCP 工具的 JSON 参数，不是终端命令。

**按日期检索并排序 — `search_papers`：**

```json
{
  "query": "generative AI medical education",
  "sources": ["crossref", "pubmed", "europe_pmc"],
  "rows": 5,
  "filters": {"date_from": "2022-01-01", "date_to": "2026-09-09"},
  "ranking": "relevance"
}
```

`rows` 是**每个来源**的返回上限，检索范围为 1–50；去重、过滤后的总数可能更少。
省略 `sources` 使用默认五源，显式指定时只查询所选来源。
`filters` 还支持 `language`、`author`、`document_type`、`identifiers`；缺失必要字段的记录可能被过滤掉。
相关性排序是本地规则评分，会写入 `ranking_score`、`ranking_reasons` 和 `score_version`。

**核对真实引用 — `get_paper_by_id`：**

```json
{
  "id": "10.1038/nature14539",
  "expected": {"title": "Deep learning", "year": 2015, "journal": "Nature"}
}
```

只提供 `id` 时是元数据查询；提供 `expected` 才增加 `verification`。
只核对传入的字段，不能把“题名匹配”表述为“整条引用已全部核验”。

**获取一跳关系 — `get_paper_by_id`：**

```json
{
  "id": "10.1038/nature14539",
  "include_relations": true,
  "relation": "both",
  "depth": 1,
  "rows": 10,
  "relation_sources": ["openalex", "crossref", "pubmed", "europe_pmc"]
}
```

图谱的 `rows` 是每个来源、每个方向的邻居上限（1–100）；`depth` 支持 1 或 2。
还受节点和边预算限制，判断是否完整请检查 `truncated`、`truncation_reason`、`depth_completed`。

</details>

### CLI 示例

**连通性和引用转换**

```bash
nature-academic-search --help
nature-academic-search preflight
nature-academic-search citation --pmid 28344011 --format ris --output references/
nature-academic-search citation --input refs.txt --format bib --output references/
```

`refs.txt` 每行使用带类型前缀的标识符，例如：

```text
DOI:10.1038/nature14539
PMID:28344011
ARXIV:1706.03762
```

没有类型前缀的行会被当作 PubMed 自由文本查询，而非标识符直接解析。
`citation --output` 指定的是**目录**，批量命令会生成各条记录的引用文件。
支持 `nbib`、`ris`、`bib`、`enw`；下载或格式转换不会自动对你原先的引用做 `expected` 核验。
给其他 MCP 客户端接入时，启动命令为 `nature-academic-search-mcp`，也可用 `nature-academic-search serve`（stdio）。

**PyPI `0.3.1` 及更新版本**

```bash
nature-academic-search search "generative AI medical education" \
  --sources crossref,pubmed --rows 5 > search-results.json

nature-academic-search verify 10.1038/nature14539 \
  --expected-title "Deep learning" --expected-year 2015 --expected-journal "Nature" \
  > verification.json

nature-academic-search search "lung cancer neoadjuvant immunotherapy" \
  --entity-type trial --rows 5 > trials.json
```

CLI `search` 默认 `--ranking relevance`。日期等 `filters` 和引文图谱参数目前通过 MCP / workflow 配置，
没有对应的 `search --filters` 或 `verify --include-relations` 选项。
脚本调用后仍需检查 JSON 中的 `errors` 和 `verification.status`，退出码为 0 不代表所有来源成功或引用匹配。

当前源码版的 `workflow run` 在部分来源失败时返回 `completed_with_errors`，仍会处理成功来源的结果。
全部来源失败时返回 `failed`、退出码 1，并保留诊断文件。重用输出目录时，以最新 `run.json` 的
`artifacts` 为准，它只列出本次运行产物。

## 如何读懂结果

### 检索结果

| 字段 | 如何理解 |
|---|---|
| `sources_queried` / `sources_succeeded` | 实际尝试的来源 / 成功响应的来源；成功也可能返回 0 条 |
| `sources_skipped` / `errors` | 跳过的操作及原因 / 请求失败详情；未选择的来源不一定出现在 skipped 中 |
| `raw_result_count` / `result_count` | 本次取回的原始记录数 / 去重、过滤后的交付数；不是完整文献库规模 |
| `record_id` | 记录的稳定标识，优先由 DOI、PMID 等强标识符构造 |
| `sources` / `source_records` / `conflicts` | 合并记录的来源、逐源记录和字段冲突 |
| `search_run` | 查询、UTC 时间、范围、来源状态、过滤与排序信息 |
| `result_fingerprint` | 基于记录 ID 的结果集合指纹；不能替代原始 JSON 存档 |

保存完整响应，尤其是 `search_run` 和 `errors`。多源失败时仍可能返回部分记录；
“拿到了结果”与“五个源全部成功”是两种情况。

### 引用核验

| `verification.status` | 表示什么 | 下一步 |
|---|---|---|
| `verified` | 本次提供的 `expected` 字段与解析元数据匹配 | 保留核验字段与来源；引用科学结论前还需读原文 |
| `mismatch` | 至少一个字段不一致 | 查看 `fields` 中的预期值和实际值，检查错引或版本差异 |
| `not_found` | 标识符查询明确报告未找到记录 | 检查标识符、原始出处和其他来源 |
| `manual_needed` | 缺少字段、字段不可核对，或流程尚需人工处理 | 补充信息并人工复查 |

网络失败可能直接返回 `error`，不能解释成论文不存在。
核验比较的是书目信息，不判断研究质量，也不证明论文支持某句话。

## 数据源如何分工

| 来源 | 代码中的名称 | 启用方式 | 主要用途与关系覆盖 |
|---|---|---|---|
| CrossRef | `crossref` | 默认论文源 | DOI、出版元数据、引用格式；提供 `references` |
| PubMed | `pubmed` | 默认论文源 | 生物医学、PMID、MeSH；ELink 提供可用的双向引用关系 |
| arXiv | `arxiv` | 默认论文源 | 预印本及版本线索；当前不提供引用边 |
| OpenAlex | `openalex` | 默认论文源 | 跨学科发现、开放获取信息；`references` / `cited_by` |
| Europe PMC | `europe_pmc` | 默认论文源 | PMID / PMCID、生物医学记录；当前适配器提供 `references` |
| Semantic Scholar | `semantic_scholar` | 显式搜索、`enrich` 或图谱 | 补充元数据、来源化引用计数和双向关系 |
| ClinicalTrials.gov | `clinicaltrials_gov` | `entity_type="trial"` | NCT、招募状态、干预、申办方及关联论文线索 |

**未连接 Google Scholar、Web of Science、Scopus、Embase、CNKI、万方。**
数据库收录范围及关系覆盖不同；缺少接口或没有返回引用边，不表示该论文从未被引用。
不同来源的 `citation_counts` 不相加为“全网引用数”。

## 更多提示词

### 上下游引文追踪

```text
使用 nature-academic-search 解析 DOI 10.1038/nature14539。
调用 get_paper_by_id，设置 include_relations=true、relation=both、depth=1、rows=10。
分别解释它引用了哪些论文、哪些论文引用了它，保留每条边的 observed_by；
报告失败来源、缺少的关系方向和截断原因，将 citation_graph 保存为 graph.json。
```

得到：结构化 `nodes` / `edges`。`references` 指“它引用了谁”，`cited_by` 指“谁引用了它”；
边始终采用 **citing → cited** 方向。工具返回 JSON，图形展示需要客户端或其他可视化工具另行生成。

### 综述整理

```text
使用 nature-academic-search，为“数字疗法对抑郁症的随机对照试验”拟定检索计划。
记录检索式、数据库、日期、纳入排除标准，等我确认后再检索。
对候选逐条调用 get_paper_by_id 并传 expected 核验，只将 verified 记录导出为 RIS；
把冲突、未找到和人工待处理记录单独列出。初筛建议不代表最终纳入决定。
若使用 CLI workflow，需要筛选时启用 screen；无需模型初筛时省略 screen，直接导出核验通过记录。
```

得到：计划、候选集、核验清单和引用文件。CLI 的具体行为见[批量工作流](../references/search-workflows.md#23-声明式科研工作流)。

### 临床试验关联

```text
使用 nature-academic-search，以英文关键词检索肺癌新辅助免疫治疗相关试验。
调用 search_papers(entity_type="trial")，按 NCT ID 整理试验状态、干预和申办方，
再根据返回状态标出正在招募的记录。若包含 linked publications，单独核验其 PMID / DOI；
试验注册和已发表论文分开列出，不把注册状态当作疗效结果。
```

得到：ClinicalTrials.gov 注册记录，以及需要另行解析的关联论文线索。
