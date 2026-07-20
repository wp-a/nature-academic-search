# Workflow 2：引用核验

**目的：** 核验 `.docx`、`.tex`、`.bib` 或 `.txt` 中的参考文献。

## 步骤

1. 按 [Citation Parser](../citation-parser.md) 提取 DOI、PMID、PMCID、arXiv ID 和候选题名。
2. 有强标识符时调用 `get_paper_by_id`；无标识符时用 `search_papers` 找候选，再人工比较。
3. 比较题名、作者、期刊、年份和标识符。
4. 标记 `verified`、`mismatch`、`not_found` 或 `manual_needed`。
5. 报告总数、各状态数量、解析来源、标识符和逐字段冲突。
6. 只有已解析论文可调用 `get_citation`；NCT 试验注册不生成论文引用。

需要 Semantic Scholar 复核时必须显式搜索，或对已有强 ID 记录使用 enrichment。来源失败时保留其他核验结果并披露 `errors`。

本项目未连接 Google Scholar、Web of Science、Scopus、Embase、CNKI、万方，不能把未执行的数据库写入核验范围。
