---
name: deep-researcher
description: >
  Research a topic deeply using web search and fetch. Produces structured
  research output (key concepts, subtopics, facts, sources) ready to be
  passed to the obsidian-writer skill.
  Triggers: "research X", "find out about X", "look up X", or as a first
  step before writing notes about a topic.
---

# Deep Researcher Skill

## Purpose

Gather comprehensive, well-sourced information on a topic and produce a
structured research brief. The output of this skill is **not** written to
Obsidian directly — it is a markdown document handed off to the
obsidian-writer skill.

## Workflow

### Step 1 — Clarify Scope (only if needed)

If the topic is ambiguous or very broad, ask one focused question:
- What angle or subtopics matter most?
- Is this conceptual understanding, practical how-to, or comparison?

Skip this step if the topic and intent are clear.

### Step 2 — Search

Run 3–5 targeted `WebSearch` queries covering:
- Core concept / definition
- How it works (internals / mechanism)
- Common patterns, best practices, or use cases
- Pitfalls, gotchas, or limitations
- Any recent developments (if the topic evolves quickly)

### Step 3 — Fetch and Extract

For the top 3–5 most relevant URLs from search results:
- Call `WebFetch` to retrieve the page content
- Extract only the signal: definitions, explanations, code snippets, diagrams descriptions, key facts
- Discard nav, ads, boilerplate

### Step 4 — Synthesise

Produce a **Research Brief** in this exact format:

```markdown
# Research Brief: {Topic}

## Summary
2–4 sentences. What is this? Why does it matter?

## Key Concepts
- **Concept A**: one-line definition
- **Concept B**: one-line definition
(list all essential concepts; no padding)

## How It Works
Explain the core mechanism. Use numbered steps if sequential.
Use a code block if a minimal example clarifies better than prose.

## Subtopics
List 3–6 subtopics worth their own Obsidian notes, with a one-line description each:
- **Subtopic A** — what this covers
- **Subtopic B** — what this covers

## Gotchas and Pitfalls
- Bullet list of non-obvious issues, edge cases, or common mistakes

## Sources
- [Title](URL) — one-line summary of what this source contributed
```

## Output Rules

- The Research Brief is the **only** output. No preamble, no trailing commentary.
- Every claim must trace to a source in the `## Sources` section.
- Hard limit: 1000 words for the brief. Compress aggressively.
- If a subtopic is large enough to deserve its own deep dive, flag it explicitly in the Subtopics section with `(deep dive warranted)`.
