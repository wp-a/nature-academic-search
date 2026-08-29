# Premium README Introduction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the Chinese-first README communicate the Academic Paper Search Skill's value, workflow, and evidence outputs at a glance.

**Architecture:** Keep the existing detailed scenarios, capability matrix, source table, audit contract, and boundaries. Strengthen the opening with an evidence-led promise, a research-assets table, a Mermaid workflow, and a clearly marked structured-result example.

**Tech Stack:** Markdown, Mermaid, JSON examples, existing repository links and contracts.

---

### Task 1: Strengthen the first-viewport explanation

**Files:** `README.md`

Add a concise promise, explain the difference between a search lead and a citable research record, and describe the assets produced by the Skill.

### Task 2: Show the end-to-end workflow

**Files:** `README.md`

Add a Mermaid flow from research question through source-aware search, identifier deduplication, field verification, citation graph expansion, and auditable export. Add a labeled contract-shaped JSON example without claiming it is a live result.

### Task 3: Verify and commit

Run `git diff --check`, the full Python test suite, and the Skill mirror check. Review the rendered Markdown structure and commit only the README and plan changes.
