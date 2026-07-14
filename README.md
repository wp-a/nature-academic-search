# Nature Academic Search

[![CI](https://github.com/wp-a/nature-academic-search/actions/workflows/ci.yml/badge.svg)](https://github.com/wp-a/nature-academic-search/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/nature-academic-search.svg)](https://pypi.org/project/nature-academic-search/)
[![Python](https://img.shields.io/pypi/pyversions/nature-academic-search.svg)](https://pypi.org/project/nature-academic-search/)

面向 Codex 和 Claude Code 的学术检索技能与 MCP 服务。统一搜索 PubMed、
CrossRef 和 arXiv，解析 DOI/PMID/arXiv ID，构建 MeSH 检索式，并导出
RIS、BibTeX、NBIB 或 ENW。

## 主要能力

- 多源并发检索，按 DOI、PMID、arXiv ID、标题与年份去重
- 保留来源追踪和单数据源失败信息
- DOI、PMID、arXiv ID 自动识别与元数据核验
- APA、Nature、IEEE、Vancouver 等引用格式
- PubMed MeSH 词表查询
- Codex 与 Claude Code 插件和安装器

## PyPI 安装

推荐使用隔离工具环境：

```bash
uv tool install nature-academic-search
nature-academic-search install --client both --email researcher@example.com
```

也可使用 `pipx install nature-academic-search`。不要使用全局 `pip install`。

从仓库安装并保留旧命令兼容：

```bash
bash install.sh researcher@example.com
```

## 插件安装

Codex：

```bash
codex plugin marketplace add wp-a/nature-academic-search
codex plugin add nature-academic-search@wp-a-academic-tools
```

Claude Code：

```bash
claude plugin marketplace add wp-a/nature-academic-search
claude plugin install nature-academic-search@wp-a-academic-tools
```

插件通过 `uvx` 启动固定版本的 PyPI MCP 服务。启动客户端前设置
`PUBMED_EMAIL`；`NCBI_API_KEY` 可选。

```bash
export PUBMED_EMAIL=researcher@example.com
export NCBI_API_KEY=optional-key
```

详见 [安装说明](docs/installation.md)。

## CLI

```bash
nature-academic-search --help
nature-academic-search serve
nature-academic-search preflight
nature-academic-search citation --pmid 28344011 --format ris
nature-academic-search citation --input refs.txt --format bib --output references/
```

MCP 保留四个稳定工具名：

| Tool | Purpose |
|---|---|
| `search_papers` | Search one or more sources and deduplicate results |
| `get_paper_by_id` | Resolve DOI, PMID, or arXiv metadata |
| `get_citation` | Format one verified citation |
| `lookup_mesh` | Find PubMed MeSH descriptors |

## 开发

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m pytest mcp-server/tests
python -m build
twine check dist/*
```

发布与维护流程见 [维护手册](docs/maintenance.md)。

## License

MIT
