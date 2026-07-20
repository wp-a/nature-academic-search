# Workflow 5：参考文献集合管理

## 发现相关论文

1. 用 `get_paper_by_id` 核验种子论文。
2. 从题名、摘要和关键词构造可读查询，调用 `search_papers`。
3. 需要引用图谱补充时显式使用 Semantic Scholar；不要把 citation count 当作相关性证明。
4. 按强标识符去重，保留 `sources`、`source_records`、`conflicts`。
5. 报告查询、日期、来源状态和纳入原因。

## 生成与清理引用文件

1. 单条论文可用 `get_citation`；批量记录使用 `nature-academic-search citation`。
2. 以 DOI、PMID、PMCID 或 arXiv ID 核验后再导出。
3. BibTeX 按规范字段验证，去重 citation key；参见
   [BibTeX Format](../ris-bibtex-format.md#bibtex-format)。
4. 未解决记录单列为 `manual_needed`，不得混入已核验集合。

## 全文边界

MCP 工具提供元数据、开放获取线索和来源 URL，不承诺下载付费全文。Europe PMC 的开放全文 URL
也必须在实际记录标明可用时才能使用。

本项目未连接 Google Scholar、Web of Science、Scopus、Embase、CNKI、万方；相关集合需由用户从机构数据库导出后再去重核验。
