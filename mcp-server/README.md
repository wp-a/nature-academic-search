# Academic Paper Search MCP Server

面向 Codex 与 Claude Code 的兼容入口。对外仍只暴露四个工具，默认论文检索覆盖 CrossRef、PubMed、
arXiv、OpenAlex、Europe PMC；Semantic Scholar 为显式搜索/富化源，ClinicalTrials.gov 为独立 trial 源。

## 工具

| 工具 | 功能 |
|---|---|
| `search_papers` | 多源 publication 搜索，或以 `entity_type="trial"` 搜索试验注册 |
| `get_paper_by_id` | 解析 DOI、PMID、PMCID、arXiv、OpenAlex、Semantic Scholar URL、NCT ID |
| `get_citation` | 格式化论文引用；拒绝把 NCT 注册伪装成论文 |
| `lookup_mesh` | 查询 PubMed MeSH 描述词 |

旧调用 `sources=["crossref", "pubmed", "arxiv"]` 保持原样，不会自动扩展。

## 配置

```bash
export PUBMED_EMAIL=researcher@example.com
export NCBI_API_KEY=
export OPENALEX_API_KEY=
export SEMANTIC_SCHOLAR_API_KEY=
```

API key 均为可选；超时和空 key 也可在 `config.toml` 配置。不要把真实凭据提交到仓库。

本项目未连接 Google Scholar、Web of Science、Scopus、Embase、CNKI、万方。

## 验证

```bash
nature-academic-search preflight
python -m pytest mcp-server/tests
```
