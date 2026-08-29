# dsh-academic-paper-search

面向 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（`dsh`）的
Academic Paper Search 插件。它是一个薄适配 Bundle：安装官方
`@deepseek-ai/dsh-mcp-client`，再启动现有的 `nature-academic-search` Python MCP
服务。检索、去重、引用核验、引文图谱、试验分流和导出仍由同一套运行时负责，
不会复制第二份搜索逻辑。

> DeepSeek Harness 当前仍是 developer preview。升级 DSH 或本 Bundle 后，请重新
> 执行文末的检查命令。

## 安装

准备：

- Node.js >= 22.19 和 `pnpm`（DSH 用它管理 profile 插件）
- DeepSeek Harness（`@deepseek-ai/dsh`）
- `uv` 提供的 `uvx`，并已加入 `PATH`
- 用于 NCBI 请求的联系邮箱

```sh
npm install --global @deepseek-ai/dsh pnpm
export PUBMED_EMAIL=researcher@example.com
dsh plugin --profile web add dsh-academic-paper-search
dsh web
```

无界面运行可以使用 headless profile：

```sh
dsh plugin --profile headless add dsh-academic-paper-search
dsh --profile headless
```

安装后需要重启目标 profile 才会挂载 Bundle。Python 服务由 MCP client 在 profile
激活时按需启动，查看包信息本身不会发起网络请求。

## DSH 中的工具

Bundle 固定使用 `academic_search` namespace，模型看到的工具名是：

- `mcp__academic_search__search_papers`
- `mcp__academic_search__get_paper_by_id`
- `mcp__academic_search__get_citation`
- `mcp__academic_search__lookup_mesh`

默认论文检索跨 Crossref、PubMed、arXiv、OpenAlex 和 Europe PMC，并按 DOI、PMID、
PMCID、arXiv ID、OpenAlex ID 去重。Semantic Scholar 需要显式检索或富化；
ClinicalTrials.gov 使用 `entity_type="trial"` 单独查询，不与论文记录混合。调用
`get_paper_by_id(include_relations=true)` 可以继续取得 references / cited_by 引文关系。

## 环境变量与凭据

Bundle 会把下列变量转发给 Python MCP 进程。值来自启动 `dsh` 的环境，不会写入本包：

| 变量 | 用途 |
|---|---|
| `PUBMED_EMAIL` | PubMed 请求必需 |
| `NCBI_API_KEY` | 可选，提升 NCBI 速率上限 |
| `CROSSREF_MAILTO` | 可选，进入 Crossref polite pool |
| `OPENALEX_API_KEY` | 可选，提升 OpenAlex 配额 |
| `SEMANTIC_SCHOLAR_API_KEY` | 可选，提升 Semantic Scholar 配额 |

显式转发是有意设计：DSH 会清理子进程继承环境中形似凭据的变量，Bundle 的显式
配置才会保留它们。空值安全，对支持匿名访问的来源不会造成额外影响。

## 边界

- 本包不替代学术数据库，也不会把模型输出自动当作引用事实。报告应保留
  `sources_succeeded`、`sources_skipped`、`errors` 和核验状态。
- 本包不增加第二套搜索实现。发布新 Python 版本时，应同步更新 Bundle 的
  `--from nature-academic-search==...` 固定版本。
- 本包不连接 Google Scholar、Web of Science、Scopus、Embase、CNKI 或万方。
- 本包不要求可选的 [WPIRONMAN AI 中转](https://api.wpironman.top)。中转可以辅助
  workflow 计划或摘要级初筛，但不是学术来源，也不会参与 MCP 事实检索。

## 验证与升级

```sh
dsh --version
dsh --profile web --dump-config
npm view dsh-academic-paper-search version
```

升级时在目标 profile 中重新安装并重启：

```sh
dsh plugin --profile web add dsh-academic-paper-search@latest
dsh web
```

需要可复现部署时，请固定 Bundle 版本，并在更新前审阅
`nature-academic-search==0.3.0` 这一行。

## 许可证

MIT。本 Bundle 与 Python MCP 服务共同维护于
[`wp-a/nature-academic-search`](https://github.com/wp-a/nature-academic-search)。
