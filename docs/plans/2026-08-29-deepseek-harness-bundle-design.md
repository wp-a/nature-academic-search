# DeepSeek Harness Bundle Design

## Goal

为 `nature-academic-search` 增加一个可通过 `dsh plugin --profile <name> add`
安装的独立 npm Bundle，让 DeepSeek Harness 复用现有 Python MCP 服务，
同时把项目定位清晰地扩展为 Codex、Claude Code 与 DeepSeek Harness 三端兼容。

## Context

DeepSeek Harness 的公开插件协议是 npm 包加 `package.json` 中的
`dsh.bundle.patch`。Bundle 通过 `cordis.patch.yml` 组装插件；官方
`@deepseek-ai/dsh-mcp-client` 负责把外部 MCP server 的工具注册到
`ctx.tools`，工具名使用 `mcp__<serverName>__<tool>` 命名空间。

仓库现有 Python 包已经负责多源检索、强标识符去重、字段核验、引文图谱、
ClinicalTrials.gov 分流和引用导出。DSH 适配层不复制这些领域逻辑，只负责
安装和配置 MCP bridge。

## Architecture

新增 `plugins/dsh-academic-paper-search/` npm 包（发布名 `dsh-academic-paper-search`），包含：

- `package.json`：声明 `dsh.bundle.patch`、Node 引擎和精确依赖版本；
- `index.js`：最小合法 Cordis module 元数据入口；
- `cordis.patch.yml`：插入一个 `@deepseek-ai/dsh-mcp-client` 实例，使用
  `uvx --from nature-academic-search==0.3.0 nature-academic-search-mcp` 启动
  Python MCP server；
- `README.md` / `README.zh.md`：安装、环境变量、工具命名、边界和升级说明。

Patch 显式转发 `PUBMED_EMAIL`、`NCBI_API_KEY`、`CROSSREF_MAILTO`、
`OPENALEX_API_KEY` 和 `SEMANTIC_SCHOLAR_API_KEY`，空值安全，不把密钥写入
仓库。默认不要求 Semantic Scholar 或 ClinicalTrials.gov 凭据；论文检索的
默认五源行为保持不变。

## Compatibility Boundary

- Codex / Claude Code 继续使用原有插件和 Python MCP 配置，不改变安装标识、
  MCP 工具名或结果契约；
- DSH 使用 `mcp__academic_search__*` 工具命名空间；
- DSH 当前为 developer preview，README 明确提示升级可能需要重新验证；
- WPIRONMAN 仍是可选模型中转，不是论文来源，不参与 MCP 事实检索。

## Verification

新增离线测试验证 npm manifest、Bundle patch 的插入行、MCP 命令与敏感环境变量
转发；现有 Python 测试、Ruff、构建和插件验证继续作为回归门禁。
