---
name: obsidian-writer
description: >
  Invoke when writing, updating, or organizing notes in an Obsidian vault.
  Handles topic discovery, index creation with Mermaid diagrams, deep-dive
  notes, compression of existing content, and source attribution.
  Triggers: "write to obsidian", "save this to my vault", "create notes about",
  "add to obsidian", "document this topic", "make obsidian notes".
---

# Obsidian Writer Skill

## Workflow

### Step 0 — Discover
- Call `search_notes_tool` with the topic name before doing anything else.
- **Results found** → enter update/compress mode (Step 5).
- **No results** → enter create mode (Steps 1–4).

### Step 1 — Clarify (only if needed)
- Ask the user only if the topic or target folder is ambiguous.
- If the topic and scope are obvious, skip this step entirely.

### Step 2 — Folder
- Check if a related folder already exists; reuse it.
- Create a new folder only if none fits.
- Naming: `Topic/Subtopic/` hierarchy — never flat single-level folders.

### Step 3 — Index Note (`00 - {Topic} — Index.md`)

Always create this first. Template:

```markdown
# {Topic}

> One-sentence summary of what this topic covers.

## Overview

2–4 sentences. No padding. State what it is and why it matters.

## Diagram

```mermaid
(flowchart, sequence, or mindmap — pick the one that best represents the topic)
```

## Deep Dives

| Note | What it covers |
|------|----------------|
| [[Folder/00 - Topic — Index]] | This index |
| [[Folder/01 - Subtopic A]] | Brief description |
| [[Folder/02 - Subtopic B]] | Brief description |

## Links

- [[related/Other Note]]

## Sources

- [Title](URL)
```

### Step 4 — Deep-Dive Notes

Create as many as the topic warrants (no fixed cap). Naming: `01 - Subtopic.md`, `02 - Subtopic.md`, etc.

**Hard limit: 500 words per note.** No filler. Every sentence earns its place.

Template:

```markdown
# Subtopic Title

> One-line summary.

(Explanation — bullets or short prose, whichever is clearer for this content.)

## Sources

- [Title](URL)
```

Rules:
- Each note must link back to the index: `[[Folder/00 - Topic — Index]]`
- Cross-link between sibling deep-dives where they explicitly relate.
- Use code blocks (with language tag) for all code.
- Use tables for comparisons.
- Use `>` blockquotes for key insights.

### Step 5 — Update/Compress Mode

When existing notes are found:
1. Read each affected note with `note_read`.
2. Merge new information in; remove redundant or outdated content.
3. Rewrite to stay under 500 words — compress aggressively, cut padding.
4. Regenerate the Mermaid diagram in the index if the understanding has evolved.
5. Update the deep-dive table in the index if notes were added or removed.

### Step 6 — Canvas

After all notes are written, apply the `obsidian-canvas` skill to build or update the visual map.

---

## Conventions

| Rule | Detail |
|------|--------|
| Wikilinks | Always full vault-relative: `[[Folder/Subfolder/Note]]` |
| Code | Fenced blocks with language tag |
| Comparisons | Markdown tables |
| Key insights | `>` blockquote |
| Word limit | 500 words max per note |
| Index naming | `00 - {Topic} — Index.md` — never bare `Index.md` |
| Sources | Every note citing external info must have `## Sources` |
| Claude knowledge | Note as: `> Source: Claude training knowledge as of {date}` |
