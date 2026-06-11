# Unified Academic Search MCP Server

统一的学术搜索 MCP 服务器，整合 CrossRef、PubMed、arXiv 三个数据源。

## 工具

| 工具 | 功能 |
|------|------|
| `search_papers` | 统一搜索，支持多数据源并发 |
| `get_paper_by_id` | 按 DOI/PMID/arXiv ID 获取详情 |
| `get_citation` | 格式化引用 (apa/nature/ieee 等) |
| `lookup_mesh` | MeSH 词表查询 |

## 配置

环境变量:
- `PUBMED_EMAIL` - 必填，NCBI 要求
- `NCBI_API_KEY` - 可选，提升速率限制

配置文件: `config.toml`

## 使用

Claude Code 会自动加载此服务器。工具通过 `academic-search` skill 调用。
