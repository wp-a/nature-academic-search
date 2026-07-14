# Installation

## Requirements

- Python 3.10 or newer
- `uv` or `pipx` for isolated Python applications
- Codex CLI, Claude Code, or both
- A contact email for NCBI PubMed requests

## Install from PyPI

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

The legacy positional email remains supported:

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

The plugin uses `uvx` to run the package version pinned in `.mcp.json`. Set the
PubMed contact email in the environment that launches the client:

```bash
export PUBMED_EMAIL=researcher@example.com
```

Optionally set `NCBI_API_KEY` for a higher NCBI request limit.

## Verification

```bash
nature-academic-search --version
nature-academic-search preflight
codex mcp get nature-academic-search --json
claude mcp get nature-academic-search
```

Start a new Codex task or Claude Code session after installing or updating a
plugin so the client reloads skills and MCP tools.
