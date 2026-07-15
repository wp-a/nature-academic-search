<div align="center">

# Nature Academic Search

**让 Codex / Claude Code 完成可复现的文献检索、核验与引用导出。**

不止返回几个论文标题：同时检索 PubMed、CrossRef 和 arXiv，合并重复记录，核验 DOI / PMID / arXiv ID，区分正式论文与预印本，并把来源失败如实写进结果。

[![CI](https://github.com/wp-a/nature-academic-search/actions/workflows/ci.yml/badge.svg)](https://github.com/wp-a/nature-academic-search/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/nature-academic-search.svg)](https://pypi.org/project/nature-academic-search/) [![Python](https://img.shields.io/pypi/pyversions/nature-academic-search.svg)](https://pypi.org/project/nature-academic-search/) [![License](https://img.shields.io/github/license/wp-a/nature-academic-search.svg)](LICENSE) [![GitHub stars](https://img.shields.io/github/stars/wp-a/nature-academic-search?style=social)](https://github.com/wp-a/nature-academic-search/stargazers)

[快速开始](#30-秒开始) · [工作流](#它如何工作) · [使用场景](#直接这样问) · [能力边界](#能力边界)

</div>

## 直接这样问

安装后，在 Codex 或 Claude Code 中输入：

> 使用 `$nature-academic-search` 查找 2022 年以来 GLP-1 受体激动剂与抑郁风险的文献。
> 同时检索 PubMed、CrossRef 和 arXiv，去重后核验 DOI / PMID，区分正式论文和预印本，
> 最后导出 RIS。某个来源失败时继续，并明确说明缺口。

你得到的不是无法追溯的论文清单，而是一份带查询、来源、核验状态和失败记录的结果。以下是结构示意，
不代表一次真实检索的统计数据：

```yaml
query: "GLP-1 receptor agonists AND depression risk"
searched_sources: [pubmed, crossref, arxiv]
search_date: YYYY-MM-DD
raw_result_count: <去重前数量>
result_count: <唯一记录数量>
groups:
  peer_reviewed: <正式论文>
  preprints: <预印本>
  unresolved: <待人工核验>
verification: [verified, mismatch, not_found, manual_needed]
source_errors: []
export: references/results.ris
```

## 30 秒开始

### Codex 插件

```bash
codex plugin marketplace add wp-a/nature-academic-search
codex plugin add nature-academic-search@wp-a-academic-tools
```

### Claude Code 插件

```bash
claude plugin marketplace add wp-a/nature-academic-search
claude plugin install nature-academic-search@wp-a-academic-tools
```

启动客户端前设置 PubMed 联系邮箱；NCBI API Key 可选：

```bash
export PUBMED_EMAIL=researcher@example.com
export NCBI_API_KEY=optional-key
```

### CLI 与自动安装器

```bash
uv tool install nature-academic-search
nature-academic-search install --client both --email researcher@example.com
nature-academic-search preflight
```

也可使用 `pipx install nature-academic-search`。从仓库安装并保留旧命令兼容：

```bash
bash install.sh researcher@example.com
```

完整参数、`--dry-run` 和安装验证见[安装说明](docs/installation.md)。

## 它如何工作

**检索 → 去重 → 核验 → 导出**

1. **定义范围**：记录研究主题、日期、文献类型、结果数量和是否接受预印本。
2. **按库检索**：PubMed、CrossRef、arXiv 使用各自适合的查询，不混用数据库语法。
3. **合并去重**：优先匹配 DOI，其次 PMID / arXiv ID，再比较标准化题名与年份。
4. **逐条核验**：对照题名、作者、来源、年份和标识符；冲突不靠猜测修复。
5. **分类交付**：分开正式论文、预印本和待核验记录，导出 RIS、BibTeX、NBIB 或 ENW。

任一来源超时或返回错误时，其他来源的成功结果仍会保留；最终回复会列出失败来源及其可能造成的缺口。

## 为什么是“核验优先”

| 常见检索输出 | Nature Academic Search |
|---|---|
| 只给标题和链接 | 同时保留查询、检索日期、标识符与来源追踪 |
| 多库结果重复出现 | 按 DOI、PMID、arXiv ID、题名与年份合并 |
| DOI 或作者冲突被静默覆盖 | 标记 `mismatch` 或 `manual_needed`，逐项说明 |
| 预印本与正式版本混在一起 | 分组报告并保留版本关系 |
| 单库故障导致整次任务失败 | 返回部分成功结果并披露 `errors` |
| 引用格式靠模型补全 | 从已解析记录生成引用或引用文件 |

这套约束适合需要把结果放进论文、开题报告或参考文献管理器的用户，也能降低 AI 生成“看起来合理、
实际不存在”的引用风险。

## 数据源能力

| 来源 | 最适合做什么 | 可核验标识符 | 明确不做什么 |
|---|---|---|---|
| PubMed | 生物医学检索、MeSH、期刊索引 | PMID、记录中的 DOI | 不提供所有论文全文 |
| CrossRef | 出版商元数据、DOI 解析、引用格式 | DOI | 不是完整学科数据库 |
| arXiv | 预印本检索、版本与发表线索 | arXiv ID、记录中的 DOI | 不代表同行评审状态 |

## 适合的科研任务

- **选题调研**：“找近五年肿瘤免疫治疗耐药机制的论文，按正式论文和预印本分组。”
- **MeSH 策略**：“先核验生成式 AI 与医学教育的 MeSH，再构建 PubMed 检索式。”
- **引用核验**：“检查这些 DOI / PMID 是否对应给定题名，逐项报告冲突。”
- **版本追踪**：“判断这些 arXiv 预印本是否已有正式发表版本。”
- **文献导出**：“把已核验记录去重后导出为 RIS，同时单列未解决引用。”

它适合综述前期检索与引用整理，但不会替代正式系统综述所需的数据库订阅、双人筛选、偏倚评估或
学科馆员复核。

## MCP 工具

四个工具名保持稳定；客户端可能添加 MCP 命名空间前缀。

| Tool | 用途 |
|---|---|
| `search_papers` | 检索一个或多个来源，合并重复记录并返回来源错误 |
| `get_paper_by_id` | 解析并核验 DOI、PMID 或 arXiv ID |
| `get_citation` | 为一条已解析记录生成指定格式引用 |
| `lookup_mesh` | 查询 PubMed MeSH 描述词以构建检索式 |

## CLI

```bash
nature-academic-search --help
nature-academic-search serve
nature-academic-search preflight
nature-academic-search citation --pmid 28344011 --format ris
nature-academic-search citation --input refs.txt --format bib --output references/
```

## 能力边界

- 当前只连接 **PubMed、CrossRef 和 arXiv**。没有连接 Google Scholar、Semantic Scholar、
  Web of Science、Scopus、Embase 或 CNKI 时，不会声称检索过它们。
- 当前以元数据、标识符、引用和检索策略为核心，不承诺自动获得付费全文。
- 上游 API 可能限流、超时或暂时不可用；工具会保留成功来源并披露失败。
- 引用进入正式稿件前仍应由作者核对原文、出版社页面和期刊要求。
- `PUBMED_EMAIL` 用于遵守 NCBI 请求规范；项目不会要求把 PyPI Token 写入客户端配置。

## 开发与维护

```bash
python -m pip install -e ".[test]"
python -m ruff check src tests
python -m pytest
python -m pytest mcp-server/tests
python -m build
twine check dist/*
```

项目支持 Python 3.10–3.13，并通过 GitHub Actions 测试包行为、旧 MCP 合约和发行构建。
发布与依赖维护流程见[维护手册](docs/maintenance.md)。

## 参与项目

发现查询适配、元数据冲突或安装问题时，请提交 [Issue](https://github.com/wp-a/nature-academic-search/issues)。
贡献代码前请保留四个 MCP 工具名和结果契约，并为解析、去重或安装行为添加回归测试。

如果这个项目能让你的文献检索更可追溯，欢迎点一个
[Star](https://github.com/wp-a/nature-academic-search)；它会帮助更多中文科研用户找到这套工作流。

## License

[MIT](LICENSE)
