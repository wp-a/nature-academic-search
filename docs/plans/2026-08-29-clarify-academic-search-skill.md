# Clarify Academic Search Skill Introduction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the main README explain `nature-academic-search` as a complete research Skill + MCP before showing installation commands.

**Architecture:** Keep the existing capability, scenario, source, output, and boundary sections. Add a concise product definition and workflow overview near the top, then tighten the navigation so readers understand the Skill's purpose before choosing an installation path.

**Tech Stack:** Markdown, existing repository links and command examples, pytest/documentation validation.

---

### Task 1: Add a clear Skill overview

**Files:**
- Modify: `README.md`

Add sections covering target users, the research problems solved, the six core capabilities, the request-to-artifact workflow, and the distinction between metadata retrieval and evidence judgment. Keep the existing source list and detailed scenarios as the authoritative references.

### Task 2: Make navigation and entry points consistent

**Files:**
- Modify: `README.md`

Update the top navigation and short installation lead-in so readers can move from definition to examples, capability matrix, data-source boundaries, outputs, and installation without inferring the product model.

### Task 3: Verify and commit

Run:

```bash
git diff --check
PYTHONPATH=src python -m pytest -q
python scripts/sync_skill.py --check
```

Review headings, links, commands, and line wrapping, then commit the README change separately from unrelated work.
