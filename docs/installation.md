# Installation

## Requirements

- Python 3.10 or newer
- `uv` or `pipx` for isolated Python applications
- Codex CLI, Claude Code, or DeepSeek Harness for agent use. The standalone CLI also runs without an agent.
- A contact email for NCBI PubMed requests. The manual installer requires it.

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

Both plugins include the Skill and MCP configuration. They start the runtime
with `uvx`, so the client must be able to find `uvx` on its `PATH`.

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

DeepSeek Harness uses the [companion Bundle](https://github.com/wp-a/dsh-academic-paper-search) and the official
`@deepseek-ai/dsh-mcp-client` bridge. It keeps the Python MCP server as the only
search implementation and exposes tools under `mcp__academic_search__*`.

Requirements: Node.js >= 22.19, `pnpm`, and `uvx` from `uv` on `PATH`.

Install from a local tarball built from the Bundle's source. The public npm registry
currently does not serve `dsh-academic-paper-search`. The [Harness packaging guide](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/publish.md)
documents the tarball workflow.

```bash
npm install --global @deepseek-ai/dsh pnpm
export PUBMED_EMAIL=researcher@example.com
git clone https://github.com/wp-a/dsh-academic-paper-search.git
cd dsh-academic-paper-search
pnpm pack
dsh plugin --profile web add "$PWD/dsh-academic-paper-search-0.1.0.tgz"
dsh web
```

If the Bundle version changes, use the filename printed by `pnpm pack`.
The Bundle's [runtime configuration](https://github.com/wp-a/dsh-academic-paper-search/blob/main/cordis.patch.yml)
currently pins `nature-academic-search==0.3.0` independently of the Codex and
Claude Code plugins. Use the PyPI CLI directly for the `0.3.1` commands and workflow fixes.
After upgrading Harness or the Bundle, restart the profile and check that the
MCP tools load.

## Source configuration

Set the PubMed contact email in the environment that launches the client:

```bash
export PUBMED_EMAIL=researcher@example.com
```

| Variable | Purpose |
|---|---|
| `NCBI_API_KEY` | Optional NCBI credential |
| `CROSSREF_MAILTO` | Optional CrossRef contact email |
| `OPENALEX_API_KEY` | OpenAlex credential |
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar credential |
| `NATURE_ACADEMIC_SEARCH_CONFIG` | Optional TOML configuration path |

The runtime reads process environment variables and optional TOML configuration.
It does not read `.env` files automatically. Upstream access and quotas depend on
the provider. Missing Semantic Scholar credentials skip its credentialed
preflight check. Keep credentials out of `.mcp.json` and repository files.

Default publication search uses CrossRef, PubMed, arXiv, OpenAlex, and Europe
PMC. Semantic Scholar is available for explicit search and enrichment.
To search ClinicalTrials.gov registrations, select `entity_type="trial"`.

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

## Verification

```bash
nature-academic-search --version
nature-academic-search preflight
codex mcp get nature-academic-search --json
claude mcp get nature-academic-search
```

Start a new Codex task or Claude Code session after installing or updating a
plugin so the client reloads skills and MCP tools.

For a plugin-only install, run `uvx --from nature-academic-search==0.3.1 nature-academic-search preflight`.
Preflight checks the source endpoints. To verify that the client has loaded its tools,
run the [DOI example](../README.md#快速开始) in a fresh session and inspect its MCP call.

| Symptom | What to check |
|---|---|
| The client cannot find `uvx` or `nature-academic-search-mcp` | Check the launch environment's `PATH` and reopen the client. |
| The desktop app cannot see `PUBMED_EMAIL` | Set it in the app's launch environment. Alternatively, register a local MCP with `nature-academic-search install --client codex --email researcher@example.com` and disable the duplicate plugin MCP entry. |
| `search` or `verify` is missing | Run `nature-academic-search --version` and upgrade to PyPI `0.3.1` or newer. Update the plugin separately if needed. |
| An endpoint times out or returns HTTP 429 | Inspect `preflight` and the result's `errors`. Check provider credentials and quotas, then retry the affected source. |
