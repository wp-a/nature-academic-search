# dsh-academic-paper-search

Academic Paper Search for [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (`dsh`).
This is a thin Bundle adapter: it installs the official
`@deepseek-ai/dsh-mcp-client` and launches the existing
`nature-academic-search` Python MCP server. Search, de-duplication, verification,
citation graphs, trial routing, and export remain implemented in one runtime.

> DeepSeek Harness is currently a developer preview. Its plugin protocol may
> change; re-run the checks below after upgrading DSH or this Bundle.

## Install

Requirements:

- Node.js >= 22.19 and `pnpm` (used by DSH profile management)
- DeepSeek Harness (`@deepseek-ai/dsh`)
- `uvx` (from `uv`) on `PATH`
- A contact email for NCBI requests

```sh
npm install --global @deepseek-ai/dsh pnpm
export PUBMED_EMAIL=researcher@example.com
dsh plugin --profile web add dsh-academic-paper-search
dsh web
```

For a headless profile:

```sh
dsh plugin --profile headless add dsh-academic-paper-search
dsh --profile headless
```

The first profile restart after installation mounts the Bundle. The Python
server is started lazily by the MCP client when the profile activates the
server; package inspection itself does not make network requests.

## Tools in DSH

The bridge uses the stable namespace `academic_search`, so the model sees:

- `mcp__academic_search__search_papers`
- `mcp__academic_search__get_paper_by_id`
- `mcp__academic_search__get_citation`
- `mcp__academic_search__lookup_mesh`

The default publication search queries Crossref, PubMed, arXiv, OpenAlex and
Europe PMC, then de-duplicates by DOI, PMID, PMCID, arXiv ID and OpenAlex ID.
Semantic Scholar is explicit enrichment/search; ClinicalTrials.gov is selected
with `entity_type="trial"` and stays separate from publications. Citation
relations are available through `get_paper_by_id(include_relations=true)`.

## Environment and credentials

The Bundle forwards these variables to the Python MCP process. Values are read
from the environment that launches `dsh`; no key is stored in this package:

| Variable | Use |
|---|---|
| `PUBMED_EMAIL` | Required for PubMed requests |
| `NCBI_API_KEY` | Optional NCBI rate-limit increase |
| `CROSSREF_MAILTO` | Optional Crossref polite-pool contact |
| `OPENALEX_API_KEY` | Optional OpenAlex quota |
| `SEMANTIC_SCHOLAR_API_KEY` | Optional Semantic Scholar quota |

The explicit forwarding is intentional because DSH removes credential-shaped
ambient variables from child processes. Empty values are safe and keep the
corresponding source available anonymously where supported.

## What this package does not do

- It does not replace the academic databases or turn model output into a
  citation fact. Keep `sources_succeeded`, `sources_skipped`, `errors`, and
  verification statuses visible in reports.
- It does not add a second search implementation. Update the Python package
  and this Bundle's pinned `--from` version together when releasing.
- It does not provide Google Scholar, Web of Science, Scopus, Embase, CNKI or
  Wanfang connectors.
- It does not require the optional
  [WPIRONMAN AI relay](https://api.wpironman.top). That relay can help with
  workflow planning or abstract-level screening, but it is not a scholarly source
  and is not used by the MCP bridge.

## Verify and upgrade

```sh
dsh --version
dsh --profile web --dump-config
npm view dsh-academic-paper-search version
```

To upgrade, install the new Bundle in the target profile and restart DSH:

```sh
dsh plugin --profile web add dsh-academic-paper-search@latest
dsh web
```

For reproducible deployments, pin the Bundle version and review the pinned
`nature-academic-search==0.3.0` line before updating either side.

## License

MIT. The Bundle is maintained in the
[`wp-a/nature-academic-search`](https://github.com/wp-a/nature-academic-search)
repository.
