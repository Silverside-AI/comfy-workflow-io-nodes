# Comfy JSON UI contract

Workflow IO nodes attach an API contract to a ComfyUI graph. Exported workflow JSON should carry enough information for **Brand Brain Composer** to build the run form without admins configuring every field by hand in the mapping editor. Authors set inputs once in ComfyUI; the app translates that into widgets. The saved mapping remains authoritative after pre-fill (admins can override).

This document describes what belongs in **this repository** versus the frontend, and how semantic fields such as `value_type` fit in.

## Comfy vs Brand Brain

| Where | Responsibility |
|-------|------------------|
| **Comfy / this repo** | Exported JSON describes what each input **is** and **how it behaves** (type, `options`, multi-value + `separator`, `value_type`). |
| **Brand Brain** | Renders the **UI**: widget choice, layout, grid, styling. Parser and mapping editor bridge Comfy → composer; the composer reads the saved mapping. |

Node widgets must not encode layout, colours, or toolbar placement. Passthrough at `run()` time; semantics exist for export and the app only.

## Semantic fields (behavior, not presentation)

Input **classes** (Text, Int, Enum, …) name data types. They do not say how choices should **look**. For enum-like inputs, the app may also need:

| Source in export / mapping | What it declares | What Brand Brain infers |
|----------------------------|------------------|-------------------------|
| **Workflow IO Multi Enum Input** (or `multiple: true` on the mapping) | Several options at once | Multi picker |
| `separator` | How the downstream node splits the string value | How to join picks when calling the API |
| `value_type` (e.g. `aspect_ratio`, `strength`) | What each option, or a number, **means** | Which control to use (e.g. ratio shapes instead of plain labels; a slider for a strength) |

Do **not** add to Workflow IO nodes: grid area names, Svelte widget ids, colours, or CSS hints.

**Workflow IO Multi Enum Input** is implemented in this repo (merged SIL-1730). Wiring it through parser, mapping editor, and composer is platform work in other repositories.

## `value_type` vocabulary

Allowed meanings live in `VALUE_TYPES` in `api_nodes/common.py` and surface as an optional widget (default `none`) on Enum, Multi Enum, Int and Float nodes. On an Enum it says what each option means; on a number, what the value means.

Each meaning lists the **kinds** of value it applies to (`enum`, `int`, `float`), and a node's dropdown shows only the meanings for its kind:

| Meaning | Kinds | What it says |
|---------|-------|--------------|
| `none` | enum, int, float | No particular meaning (default) |
| `aspect_ratio` | enum | Ratios like 16:9 |
| `strength` | int, float | An amount judged by eye between `min` and `max` |
| `degrees` | int, float | An angle in degrees |
| `frame_count` | int | An exact number of video frames |

A meaning describes the value, never the widget: `strength` lets Brand Brain choose a slider, but the node does not say "slider". The vocabulary is shared, so the parser and mapping editor can check a pair (Float + `aspect_ratio` is never valid) against the same table.

The vocabulary is **append-only**, per kind. You may **add** a new meaning, or a new kind on an existing meaning; **never remove, rename, or reorder** meanings, and **never take a kind away** from one. ComfyUI checks a saved `value_type` against that node's own list, so either change would break saved graphs of that kind. If a meaning changes, add a new type and treat the old one as legacy in the app—do not edit the list in place.

## How data flows

```
Workflow IO widgets  →  Comfy API JSON inputs  →  parser  →  api_config.mappings  →  Composer
```

Deploy and rollout order (editor + runner, backend registration, Image Reframer, etc.) are documented with the platform rollout notes, not in this repo.
