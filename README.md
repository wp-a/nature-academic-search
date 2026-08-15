<div align="center">

# Academic Paper Search

**让 Codex / Claude Code 完成可复现的文献检索、核验与引用导出。**

安装标识仍为 `nature-academic-search`，现有命令与配置无需迁移。

默认并行检索 CrossRef、PubMed、arXiv、OpenAlex 和 Europe PMC；需要时显式调用 Semantic Scholar
搜索或富化，并把 ClinicalTrials.gov 试验注册与论文严格分开。

[![CI](https://github.com/wp-a/nature-academic-search/actions/workflows/ci.yml/badge.svg)](https://github.com/wp-a/nature-academic-search/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/nature-academic-search.svg)](https://pypi.org/project/nature-academic-search/) [![Python](https://img.shields.io/pypi/pyversions/nature-academic-search.svg)](https://pypi.org/project/nature-academic-search/) [![License](https://img.shields.io/github/license/wp-a/nature-academic-search.svg)](LICENSE) [![GitHub stars](https://img.shields.io/github/stars/wp-a/nature-academic-search?style=social)](https://github.com/wp-a/nature-academic-search/stargazers)

[真实案例](#三个可复制的中文场景) · [快速开始](#30-秒开始) · [数据源](#数据源如何分工) · [能力边界](#能力边界)

<a href="docs/examples/topic-scoping.md">
  <img src="docs/assets/academic-search-topic-scoping.png" width="1000" alt="Academic Paper Search 2026-07-31 多源开题检索真实结果">
</a>

<sub>本次真实结果 · 2026-07-31：四个来源成功，PubMed 429 被明确披露；点击查看完整记录与边界。</sub>

第三方收录：[TensorBlock MCP Server Directory](https://tensorblock.co/mcp/servers/github-wp-a-nature-academic-search-24b4493d) · [合并记录](https://github.com/TensorBlock/awesome-mcp-servers/pull/1492)

</div>

## 直接这样问

安装后，在 Codex 或 Claude Code 中输入：

> 使用 `$nature-academic-search` 查找 2022 年以来 GLP-1 受体激动剂与抑郁风险的论文。
> 使用默认五个论文源，去重后核验 DOI / PMID / PMCID，区分正式论文和预印本；
> 对有强标识符的记录用 Semantic Scholar 补充引用指标，最后导出 RIS。某个来源失败时继续并说明。

查询试验注册时明确指定实体类型：

> 使用 `$nature-academic-search` 调用 `search_papers`，以 `entity_type="trial"` 查找正在招募的
> 肺癌新辅助免疫治疗试验；按 NCT ID 去重，不要把试验注册当成已发表论文。

返回结果会证明哪些来源实际执行，而不是只展示一张无法追溯的标题清单：

```yaml
query: "GLP-1 receptor agonists AND depression risk"
entity_type: publication
sources_queried: [crossref, pubmed, arxiv, openalex, europe_pmc]
sources_succeeded: [crossref, pubmed, arxiv, openalex, europe_pmc]
sources_skipped: []
errors: null
raw_result_count: <去重前数量>
result_count: <唯一记录数量>
results:
  - title: <题名>
    sources: [pubmed, europe_pmc]
    source_records: [<来源记录>]
    citation_counts: {openalex: <来源计数>, semantic_scholar: <来源计数>}
    citation_count_source: openalex
```

## 三个可复制的中文场景

### 开题检索

```text
使用 $nature-academic-search 为“生成式 AI 在医学教育中的应用与风险”做开题检索。
先记录检索日期和纳入范围，再使用默认论文源检索；按 DOI、PMID、PMCID、arXiv
和 OpenAlex ID 去重。把正式论文、预印本和未解决记录分开，逐源报告成功、失败与
限流状态。不要把本次初筛描述成系统综述，也不要根据引用次数判断证据质量。
```

[查看 2026-07-31 实测记录](docs/examples/topic-scoping.md)

### AI 幻觉引用核验

```text
使用 $nature-academic-search 核验下面的参考文献。先从 DOI / PMID / PMCID / arXiv ID
取回原始元数据，再逐项比较题名、作者、年份和期刊。输出 verified、mismatch、
not_found 或 manual_needed，并解释冲突；不要用搜索结果自动补成一条看似完整的引用。

待核验引用：在这里粘贴引用
```

[查看 DOI 与题名冲突实测](docs/examples/citation-verification.md)

### PubMed / MeSH 检索

> `lookup_mesh` 的 ESummary 解析修复目前位于 `main`。PyPI `0.2.0` 与插件固定版本尚未包含该修复；要复现下面的 MeSH 案例，请先从当前源码安装：

```bash
git clone https://github.com/wp-a/nature-academic-search.git
cd nature-academic-search
bash install.sh --client both --email researcher@example.com
```

```text
使用 $nature-academic-search 为“生成式 AI 与医学教育”构建 PubMed 起始检索式。
先分别调用 lookup_mesh 核对 Artificial Intelligence、Generative Artificial Intelligence
和 Education, Medical 的规范主题词与 MeSH ID；再把 MeSH 与题名/摘要自由词分组组合。
输出每个主题词的核验结果、最终检索式和仍需人工调整的边界，不要把关键词直接猜成 MeSH。
```

[查看 NCBI MeSH 实测记录](docs/examples/pubmed-mesh.md)

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

### CLI 与自动安装器

```bash
uv tool install nature-academic-search
export PUBMED_EMAIL=researcher@example.com
nature-academic-search install --client both --email researcher@example.com
nature-academic-search preflight
```

也可使用 `pipx install nature-academic-search`。从仓库安装并保留旧命令兼容：

```bash
bash install.sh researcher@example.com
```

`NCBI_API_KEY`、`OPENALEX_API_KEY`、`SEMANTIC_SCHOLAR_API_KEY` 均为可选项。没有 Semantic Scholar
key 时预检会标记 `SKIP`，不会回显任何凭据。完整说明见[安装文档](docs/installation.md)。

## 数据源如何分工

| 来源 | 调用方式 | 最适合做什么 | 边界 |
|---|---|---|---|
| CrossRef | 默认论文源 | DOI、出版商元数据、格式化引用 | 不是完整学科数据库 |
| PubMed | 默认论文源 | 生物医学索引、PMID、MeSH | 不保证全文可得 |
| arXiv | 默认论文源 | 预印本与版本线索 | 不代表同行评审状态 |
| OpenAlex | 默认论文源 | 跨学科发现、OA 与来源化引用指标 | 指标只代表 OpenAlex 口径 |
| Europe PMC | 默认论文源 | PMID/PMCID、生物医学与开放全文线索 | 与 PubMed 有重叠 |
| Semantic Scholar | 显式搜索或 `enrich` | 补充元数据和引用/参考文献指标 | 富化只用强标识符 |
| ClinicalTrials.gov | `entity_type="trial"` | NCT 注册、状态、干预、申办方和入组信息 | 试验注册不是论文 |

默认 publication 搜索调用前五源。显式传入旧三源列表时仍只调用 CrossRef、PubMed、arXiv，兼容旧工作流。

## 它如何工作

**检索 → 去重 → 核验 → 导出**

1. **定义范围**：记录研究主题、日期、类型、数量、是否接受预印本以及实体类型。
2. **按库检索**：使用各来源适合的查询，不把 PubMed 字段语法复制到其他 API。
3. **合并去重**：优先匹配 DOI、PMID、PMCID、arXiv、OpenAlex、Semantic Scholar 或 NCT ID；
   弱题名匹配只在相同实体类型内进行。
4. **保留溯源**：每条记录带 `sources` / `source_records`；冲突进入 `conflicts`。
5. **逐条核验**：对照题名、作者、期刊、年份和标识符，标记 `verified`、`mismatch`、
   `not_found` 或 `manual_needed`。
6. **分类交付**：正式论文、预印本、trial 和未解决记录分开；论文可导出 RIS、BibTeX、NBIB 或 ENW。

任一来源超时或失败时，其他成功结果仍会保留。`sources_queried`、`sources_succeeded`、
`sources_skipped` 与 `errors` 明确展示完整状态。

## 为什么是“核验优先”

| 常见检索输出 | Academic Paper Search |
|---|---|
| 只给标题和链接 | 保留查询、日期、实体类型、标识符与来源追踪 |
| 多库结果重复 | 强标识符优先去重，弱匹配保留冲突 |
| 引用次数混成一个数字 | 使用 `citation_counts` 和 `citation_count_source` 标明口径 |
| 预印本、论文和试验注册混在一起 | 按 publication/preprint/trial 分组且禁止跨实体合并 |
| 单库故障导致整次失败 | 返回部分成功结果并披露失败或跳过原因 |
| 引用格式靠模型补全 | 解析记录后格式化；NCT 不伪造论文引用 |

## 适合的科研任务

- **选题调研**：“找近五年肿瘤免疫治疗耐药机制论文，按正式论文和预印本分组。”
- **MeSH 策略**：“核验生成式 AI 与医学教育的 MeSH，再构建 PubMed 检索式。”
- **引用核验**：“检查这些 DOI / PMID / PMCID 是否对应给定题名，逐项报告冲突。”
- **版本追踪**：“判断这些 arXiv 预印本是否已有正式发表版本。”
- **试验追踪**：“查 ClinicalTrials.gov 招募中试验，并另行核验其 linked publications。”
- **文献导出**：“把已核验论文去重后导出 RIS，同时单列未解决引用。”

它适合综述前期检索、证据地图和引用整理，但不会替代正式系统综述所需的订阅数据库、双人筛选、
偏倚评估或学科馆员复核。

## MCP 工具

四个工具名保持稳定；客户端可能添加 MCP 命名空间前缀。

| Tool | 用途 |
|---|---|
| `search_papers` | 搜索 publication 或 trial，合并记录并返回来源状态 |
| `get_paper_by_id` | 解析 DOI、PMID、PMCID、arXiv、OpenAlex、Semantic Scholar URL 或 NCT ID |
| `get_citation` | 格式化已解析论文；trial 返回结构化边界错误 |
| `lookup_mesh` | 查询 PubMed MeSH 描述词 |

## CLI

```bash
nature-academic-search --help
nature-academic-search serve
nature-academic-search preflight
nature-academic-search citation --pmid 28344011 --format ris
nature-academic-search citation --input refs.txt --format bib --output references/
```

## 能力边界

- 本项目未连接 Google Scholar、Web of Science、Scopus、Embase、CNKI、万方，不会声称覆盖这些来源。
- 当前以元数据、标识符、引用和检索策略为核心，不承诺自动获得付费全文。
- 上游 API 会限流、超时或暂时不可用；预检和搜索结果会逐源披露。
- 不同来源的引用次数口径不同，不会相加成“全网总引用数”。
- 引用进入正式稿件前仍应由作者核对原文、出版社页面和期刊要求。

## 开发与维护

```bash
python -m pip install -e ".[test]"
python scripts/sync_skill.py --check
python -m ruff check src tests
python -m pytest
python -m pytest mcp-server/tests
python -m build
twine check dist/*
```

项目支持 Python 3.10–3.13。发布与依赖维护流程见[维护手册](docs/maintenance.md)。

## 参与项目

发现解析、来源冲突或安装问题时，请提交 [Issue](https://github.com/wp-a/nature-academic-search/issues)。
贡献代码前请保留四个 MCP 工具名、实体边界与结果契约，并添加回归测试。

如果这个项目能让你的文献检索更可追溯，欢迎点一个
[Star](https://github.com/wp-a/nature-academic-search)；它会帮助更多中文科研用户找到这套工作流。

## License

[MIT](LICENSE)
