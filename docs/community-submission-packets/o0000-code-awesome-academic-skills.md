# Human Submission Packet: O0000-code/awesome-academic-skills

This target explicitly requires a human to inspect the project and file the recommendation. Do not submit this packet automatically. Open the [Recommend a skill form](https://github.com/O0000-code/awesome-academic-skills/issues/new?template=recommend-skill.yml), review every statement, and make the required human attestation yourself.

## Form Fields

- **Name:** `nature-academic-search`
- **Source URL:** `https://github.com/wp-a/nature-academic-search`
- **Author:** `wp-a`
- **Author URL:** `https://github.com/wp-a`
- **License:** `MIT`
- **Category:** `Discover & Collect — Literature Search & Discovery`
- **Lifecycle stage:** `discovery`
- **Type:** `skill`
- **Description:** Searches, deduplicates, and verifies paper metadata across five open scholarly sources for Codex and Claude Code, with citation exports; it does not cover subscription databases.
- **Homepage URL:** `https://www.wpironman.top/2026/07/academic-paper-search-reproducible-literature-search/`
- **Install hint:** `git clone https://github.com/wp-a/nature-academic-search.git && cd nature-academic-search && bash install.sh --client both --email researcher@example.com`
- **Languages:** `en, zh`
- **Tags:** `literature-search, citation-verification, pubmed, mcp, codex, claude-code`

## Executable-Surface Disclosure

All seven form statements can be checked after human review.

- **Network endpoints:** `api.crossref.org`, `eutils.ncbi.nlm.nih.gov`, `export.arxiv.org`, `api.openalex.org`, `www.ebi.ac.uk/europepmc/webservices/rest`, `api.semanticscholar.org`, and `clinicaltrials.gov/api/v2`.
- **Hooks:** none.
- **Bypass permissions:** not required.
- **Telemetry:** none.
- **Auto-update:** none; the MCP plugin pins package `0.2.0`.
- **allowed-tools:** the Skill does not declare a `Bash(*)` wildcard.
- **Commercial dependency:** none is required for the default sources; supported source API keys are optional.
- **Bash scripts:** `install.sh` is public, commented, and supports `--dry-run`.

## Validate The Claim

Exact prompt:

```text
使用 $nature-academic-search 检索 “large language models medical education”，每个默认论文源最多返回 3 条。报告检索日期、sources_queried、sources_succeeded、errors、去重前后数量和稳定标识符；然后核验 DOI 10.1371/journal.pdig.0000198。不要静默隐藏限流或来源失败。
```

A correct result names all five requested default publication sources, preserves any partial failure instead of claiming complete coverage, returns deduplicated records with stable identifiers, and resolves the DOI to “Performance of ChatGPT on USMLE: Potential for AI-assisted medical education using large language models.” A dated reference run and screenshot are available in [the topic-scoping example](../examples/topic-scoping.md).

## Human Checklist

- [ ] I personally inspected the repository and this packet.
- [ ] I searched existing entries and open/closed issues for duplicates.
- [ ] I confirmed the public links, repository age, and MIT license.
- [ ] I read the target contribution guide and Code of Conduct.
