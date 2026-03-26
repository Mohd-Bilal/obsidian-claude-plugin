---
name: obsidian-canvas
description: >
  Invoke to create or update an Obsidian canvas that visually maps a set of notes
  as linked nodes. Handles node layout, edge creation, and updates to existing canvases.
  Triggers: "create a canvas", "visualise these notes", "make a canvas map", or
  automatically after obsidian-writer finishes a topic with 3+ notes.
---

# Obsidian Canvas Skill

## When to Create a Canvas

- Only when a topic folder has **3 or more notes** (index + at least 2 deep dives).
- Canvas file lives in the same folder as the notes: `{Folder}/{Topic}.canvas`
- Skip canvas creation for single standalone notes.

## Workflow

### Step 1 — Check for Existing Canvas
- Use `canvas_read` to check if `{Folder}/{Topic}.canvas` exists.
- **Exists** → enter update mode (Step 4).
- **Does not exist** → enter create mode (Steps 2–3).

### Step 2 — Plan Layout

| Node | Position | Size |
|------|----------|------|
| Index note | Center `{x: 0, y: 0}` | 400 × 200 |
| Deep-dive 1 | `{x: 500, y: -300}` | 250 × 130 |
| Deep-dive 2 | `{x: 500, y: 0}` | 250 × 130 |
| Deep-dive 3 | `{x: 500, y: 300}` | 250 × 130 |
| Deep-dive N | Continue 300px apart vertically | 250 × 130 |

Adjust x-offsets for very large sets (wrap into 2 columns at 6+ deep dives).

### Step 3 — Create Canvas

Call `canvas_create` with:

```json
{
  "path": "Folder/Topic.canvas",
  "nodes": [
    {
      "id": "index",
      "type": "file",
      "file": "Folder/Topic — Index.md",
      "x": 0, "y": 0,
      "width": 400, "height": 200
    },
    {
      "id": "dive-01",
      "type": "file",
      "file": "Folder/01 - Subtopic.md",
      "x": 500, "y": -150,
      "width": 250, "height": 130
    }
  ],
  "edges": [
    {
      "id": "edge-dive-01-index",
      "fromNode": "dive-01",
      "fromSide": "left",
      "toNode": "index",
      "toSide": "right"
    }
  ]
}
```

Edge direction convention: **deep-dive → index** (deep dives point to their hub).
Cross-edges between deep-dives: add only when those notes explicitly wikilink to each other.
Label edges only when the relationship is non-obvious.

### Step 4 — Update Mode

1. Call `canvas_read` to get current nodes and edges.
2. Compare against current notes in the folder.
3. Add nodes for any notes not yet on the canvas.
4. Remove nodes for notes that no longer exist.
5. Reconcile edges accordingly.
6. Call `canvas_update` with the full updated JSON.

## ID Convention

Use short, stable, human-readable IDs:
- Index node: `"index"`
- Deep-dive nodes: `"dive-01"`, `"dive-02"`, etc.
- Edges: `"edge-{fromId}-{toId}"`

## Node Types

| Use | Type |
|-----|------|
| Linking to a `.md` note | `"file"` |
| Free-floating label | `"text"` |
| Group/section boundary | `"group"` |

Always use `"file"` for note nodes in this skill. `"text"` nodes are only for adding short annotations if helpful.
