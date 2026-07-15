---
name: nature-academic-search
description: >-
  Use when users ask to 找文献、做文献检索、查论文、核验引用、去重文献、设计 PubMed/MeSH
  检索式、解析 DOI/PMID/arXiv ID，或导出 RIS、BibTeX、NBIB、ENW；also use for
  multi-source academic search, citation verification, and reference management across PubMed,
  CrossRef, and arXiv.
---

# Academic Paper Search

使用捆绑的 MCP 服务组织可复现检索。把每条记录当作待核验的证据，不把搜索结果当作可凭空补全的引用。

## 任务路由

| 用户目标 | 工具或路径 | 完成标准 |
|---|---|---|
| 找文献、文献检索、综述初筛 | `search_papers` | 跨指定来源检索、去重并披露失败 |
| 核验 DOI、PMID、arXiv ID | `get_paper_by_id` | 对照题名、作者、来源、年份和标识符 |
| 生成单条引用 | `get_citation` | 只格式化已解析的记录 |
| 构建 PubMed 检索式 | `lookup_mesh` | 先确认 MeSH，再组合自由词 |
| 批量导出引用文件 | 包 CLI | 读取[引用文件流程](references/citation-files.md) |

客户端可能给工具名添加 MCP 前缀；按上表的名称后缀识别。

## 来源边界

- PubMed：生物医学索引、PMID、MeSH。
- CrossRef：出版商元数据、DOI 解析。
- arXiv：预印本及其版本信息。

不要声称检索了 Google Scholar、Semantic Scholar、Web of Science、Scopus、Embase、CNKI
或其他未连接来源。不要绕过现有工具假装执行原始 API。工具不可用时说明限制；除非用户另行提供可用工具，
否则停止对应来源，不影响已成功来源。

## 执行流程

1. 明确主题、日期范围、文献类型、结果数量和是否接受预印本。仅在缺项会改变结果时提问。
2. 按来源职责调用 `search_papers`；不要把 PubMed 语法原样复制到其他数据库。
3. 检查 `errors`、`raw_result_count`、`result_count` 和每条记录的 `sources`。保留部分成功结果。
4. 对拟引用、标识符冲突或元数据可疑的记录调用 `get_paper_by_id`。
5. 按题名、作者、来源、年份和标识符判定：
   - `verified`：关键字段一致；
   - `mismatch`：字段冲突，逐项列出；
   - `not_found`：指定来源未返回记录；
   - `manual_needed`：信息不足，禁止猜测。
6. 分开报告正式论文、预印本和未解决记录。正式版本与预印本相关时保留两者关系。
7. 单条引用使用 `get_citation`；批量导出前排除或单列未核验记录。

## 结果契约

每次检索至少返回：原始查询、实际检索来源、检索日期与截止日期、纳入规则、去重前后数量、结果及
DOI/PMID/arXiv ID、每条记录的来源追踪、正式论文/预印本分类、核验状态、来源错误和导出格式。
查询被放宽或改写时，同时展示原查询与修订查询。

## 中文示例

> 找 2022 年以来 GLP-1 受体激动剂与抑郁风险的文献，同时查 PubMed、CrossRef 和 arXiv；
> 去重、核验 DOI/PMID、区分预印本，并导出 RIS。任一来源失败时继续并说明。

## 证据规则

- 不编造元数据、摘要、引用次数、标识符、开放获取状态或全文结论。
- 优先按 DOI 合并；其次核验 PMID 或 arXiv ID，再使用标准化题名和年份。
- 不把预印本描述为同行评审论文，不把来源特定的引用次数描述为绝对值。
- 不静默扩大无结果查询，不导出未解决记录作为已核验引用。

需要设计检索式、选择来源、排序或核验细节时，读取[检索工作流](references/search-workflows.md)。
