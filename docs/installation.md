# Installation

## Requirements

- Python 3.10 or newer
- `uv` or `pipx` for isolated Python applications
- Codex CLI, Claude Code, DeepSeek Harness, or any combination
- A contact email for NCBI PubMed requests

## Install from PyPI

Use `0.3.1` or newer for CLI `search` / `verify`, automatic workflow verification,
and screening-aware export. The package and this repository's plugin runtime pin
are synchronized at `0.3.1`. PyPI `0.3.0` does not include the two CLI commands or
the workflow fixes. `uv tool upgrade nature-academic-search` upgrades the CLI;
plugin users must also update the plugin to change its pinned runtime.

```bash
uv tool install nature-academic-search
nature-academic-search install \
  --client both \
  --email researcher@example.com
```

The installer copies the managed skill into each selected client and registers
`nature-academic-search-mcp` through `codex mcp add` or
`claude mcp add --scope user`. It does not edit client configuration files
directly.

Preview changes without writing:

```bash
nature-academic-search install \
  --client both \
  --email researcher@example.com \
  --dry-run
```

## Install from this repository

Use the current `main` source when testing changes that have not been released to
PyPI. The 2026-07-31 MeSH ESummary parsing fix is included in PyPI `0.3.0`; use the
source checkout only when testing unreleased changes:

```bash
git clone https://github.com/wp-a/nature-academic-search.git
cd nature-academic-search
bash install.sh --client both --email researcher@example.com
```

The legacy positional email remains supported from an existing checkout:

```bash
bash install.sh researcher@example.com
```

Equivalent explicit form:

```bash
bash install.sh \
  --client both \
  --email researcher@example.com
```

The shell installer uses `uv tool install` or `pipx install`; it refuses global
`pip` installation.

## Install as a plugin

### Codex

```bash
codex plugin marketplace add wp-a/nature-academic-search
codex plugin add nature-academic-search@wp-a-academic-tools
```

### Claude Code

```bash
claude plugin marketplace add wp-a/nature-academic-search
claude plugin install nature-academic-search@wp-a-academic-tools
```

## Install as a DeepSeek Harness Bundle

DeepSeek Harness uses the companion npm Bundle and the official
`@deepseek-ai/dsh-mcp-client` bridge. It keeps the Python MCP server as the only
search implementation and exposes tools under `mcp__academic_search__*`.

Requirements: Node.js >= 22.19, `pnpm`, and `uvx` from `uv` on `PATH`.

```bash
npm install --global @deepseek-ai/dsh pnpm
export PUBMED_EMAIL=researcher@example.com
dsh plugin --profile web add dsh-academic-paper-search
dsh web
```

Before the npm Bundle is published, install the package from its standalone
repository checkout:

```bash
git clone https://github.com/wp-a/dsh-academic-paper-search.git
dsh plugin --profile web add ./dsh-academic-paper-search
```

The DSH package is intentionally a thin adapter. Its `cordis.patch.yml` pins
`nature-academic-search==0.3.0`, forwards optional source credentials explicitly,
and enables bounded MCP reconnects. DSH is currently a developer preview, so
re-check the Bundle after upgrading the harness.

The Codex / Claude plugin uses `uvx` to run the package version pinned in `.mcp.json`.
The standalone DSH Bundle manages its runtime pin independently; check its repository
before assuming it has adopted Python `0.3.1`. Set the
PubMed contact email in the environment that launches the client:

```bash
export PUBMED_EMAIL=researcher@example.com
```

Optional source credentials:

```bash
export NCBI_API_KEY=
export OPENALEX_API_KEY=
export SEMANTIC_SCHOLAR_API_KEY=
```

## 可选工作流模型层

`0.3.1` 起，workflow 默认按标识符回查核验。无需模型时使用
`steps: [plan, search, verify, export]`；若启用 `screen`，导出还要求筛选为 `include`，
模型未配置或失败的待处理记录不会导出。`plan.json` 由 YAML 本地生成。
需要摘要级初筛辅助时可配置 OpenAI-compatible 中转站；密钥只放在运行环境，不要写入 YAML：

> **模型入口：** [进入 WPIRONMAN AI 中转控制台](https://api.wpironman.top)

```bash
export ACADEMIC_SEARCH_LLM_BASE_URL=https://api.wpironman.top/v1
export ACADEMIC_SEARCH_LLM_API_KEY=your-relay-key
export ACADEMIC_SEARCH_LLM_MODEL=your-model
export ACADEMIC_SEARCH_LLM_PROTOCOL=responses_http
```

Responses 使用普通 HTTP；中转站不提供 Responses WebSocket 时无需改用另一个客户端。默认只发送
标题、摘要、标识符和批准的元数据，全文需要在 workflow 中显式设置
`privacy.allow_full_text: true`。网关不可用只会跳过模型步骤，不会阻断学术源检索。

The runtime accepts empty optional credentials; upstream access and quotas still
depend on the source's current requirements. A missing
Semantic Scholar key causes its credentialed preflight check to be skipped; it
does not disable the five default publication sources. Never commit real key
values to `.mcp.json`, TOML, or documentation snippets.

Default publication search uses CrossRef, PubMed, arXiv, OpenAlex, and Europe
PMC. Semantic Scholar is explicit search/enrichment. ClinicalTrials.gov is
selected with `entity_type="trial"` and remains separate from publications.

## Verification

```bash
nature-academic-search --version
nature-academic-search preflight
codex mcp get nature-academic-search --json
claude mcp get nature-academic-search
```

Start a new Codex task or Claude Code session after installing or updating a
plugin so the client reloads skills and MCP tools.

The preflight report lists queried, skipped, successful, and failed endpoint
checks without printing credential values. This project has not connected
Google Scholar, Web of Science, Scopus, Embase, CNKI, or Wanfang.
