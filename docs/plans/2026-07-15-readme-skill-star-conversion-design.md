# README and Skill Star Conversion Design

**Date:** 2026-07-15
**Status:** Approved
**Primary audience:** Chinese-speaking researchers using Codex or Claude Code

## Objective

Improve repository discovery and visitor-to-user conversion without overstating
the package's capabilities. The repository should explain, within the first
screen, that it coordinates a reproducible workflow across literature search,
deduplication, metadata verification, and citation export.

The design optimizes for qualified stars from researchers and research-tool
users, not for vanity metrics. A visitor should be able to answer three questions
quickly:

1. What research task does this solve?
2. Why should I use it instead of a generic paper-search MCP server?
3. How can I try it in Codex or Claude Code now?

## Positioning

Use a Chinese-first workflow promise:

> 让 Codex / Claude Code 完成可复现的文献检索、核验与引用导出。

The differentiator is evidence discipline rather than source count. The project
must emphasize:

- traceable PubMed, CrossRef, and arXiv provenance;
- deterministic deduplication and identifier resolution;
- explicit separation of peer-reviewed records and preprints;
- disclosure of partial source failures;
- verified citation metadata and reference-manager-ready exports;
- Codex and Claude Code support from one repository.

Do not imply support for Google Scholar, Semantic Scholar, Web of Science,
Scopus, CNKI, full-text retrieval, systematic-review automation, or citation
counts unless those capabilities are implemented and verified later.

## README Information Architecture

The README will be rewritten in this order:

1. Chinese-first title and one-sentence value proposition.
2. Compact quality and distribution badges.
3. A copy-ready Chinese prompt demonstrating the target workflow.
4. A short, truthful example of the result contract.
5. A three-step quick start for Codex, Claude Code, and CLI users.
6. A workflow diagram: define scope, search sources, deduplicate, verify, export.
7. Use cases for literature discovery, MeSH query construction, citation
   verification, preprint checking, and citation-file export.
8. A source capability matrix that states what each source contributes.
9. A comparison section explaining the verification-first design.
10. Stable MCP tools and CLI examples.
11. Evidence boundaries, privacy, and upstream API limitations.
12. Development, maintenance, contribution, and a restrained star call to action.

The README stays Chinese-first while retaining English product names, command
names, identifiers, and badges for GitHub and package searchability. It will not
duplicate the full installation manual.

## Demonstration Contract

The README demonstration will use a clearly labeled illustrative output rather
than invented live search statistics. The example should show the shape of a
trustworthy response:

- original query and databases searched;
- search date or cutoff field;
- raw and deduplicated record counts represented as placeholders or explicitly
  marked example values;
- DOI, PMID, or arXiv identifiers;
- merged provenance;
- peer-reviewed, preprint, and unresolved classifications;
- per-source errors when applicable;
- selected export format.

The example must not present fabricated article metadata as a real result.

## Skill Design

Both `SKILL.md` copies remain byte-for-byte identical. The package's embedded
skill continues to use the root copy.

The skill will add:

- Chinese and English trigger phrases in the YAML description;
- an intent router for discovery, identifier resolution, citation verification,
  MeSH strategy, and citation-file export;
- a minimum search-scope contract that asks only outcome-changing questions;
- source selection rules and a clear unsupported-source boundary;
- a staged workflow for search, inspection, verification, classification, and
  export;
- a result-reporting template that always includes query, sources, cutoff,
  unique-result count, provenance, and failures;
- explicit verification states: `verified`, `mismatch`, `not_found`, and
  `manual_needed`;
- Chinese prompt examples that help the clients trigger the skill naturally;
- progressive-disclosure links to detailed workflow and citation-file
  references.

The skill should guide agent behavior without reproducing tool documentation or
turning into a general academic-writing guide.

## Repository Metadata

Set a Chinese-first GitHub description that includes the searchable English
terms `Codex`, `Claude Code`, `MCP`, `PubMed`, `CrossRef`, and `arXiv`.

Set the homepage to the PyPI project page. Add focused topics such as:

- `academic-search`
- `literature-review`
- `citation-management`
- `pubmed`
- `crossref`
- `arxiv`
- `mcp`
- `codex`
- `claude-code`
- `research-tools`

Do not add unrelated trending topics.

## Star Growth Mechanics

README and metadata improve conversion but do not create distribution alone.
The repository will therefore expose reusable sharing hooks without adding a
marketing site:

- a concise value proposition suitable for GitHub search and social posts;
- copy-ready prompts that produce a visible result quickly;
- clear installation paths that reduce abandonment;
- contribution and issue links that signal active maintenance;
- release and PyPI links that demonstrate installability.

External promotion, directory submission, launch posts, and community outreach
remain separate follow-up activities. No automated starring, unsolicited
promotion, or artificial social proof is part of this change.

## Verification

The implementation is complete when:

- root and plugin skill files are identical;
- the skill validator and plugin validators pass;
- package metadata tests and the full test suites pass;
- README commands match the manifests and installed CLI;
- all README links resolve locally or point to intended public destinations;
- GitHub description, homepage, and topics match the approved positioning;
- the repository remains clean after the implementation commit.
