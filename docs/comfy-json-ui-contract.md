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

`value_type` says what a value means, so Brand Brain can show it appropriately. It's an optional widget (default `none`) on Enum, Multi Enum, Int and Float nodes: on an Enum it says what each option means; on a number, what the value means.

The meanings live in [`VALUE_TYPES`](../api_nodes/common.py) in `api_nodes/common.py`, the single list to read or add to. Each entry gives the **kinds** of value it applies to (`enum`, `int`, `float`) and what it says, and a node's dropdown offers only the meanings for its kind.

**Rules**

- A meaning describes the value, never the widget: `strength`, not "slider". Brand Brain picks the control.
- Filter by kind, never by node. A new input declares its kind (`enum`, `int`, `float`); don't give a node class its own list or ask authors to pick a type. `VALUE_TYPES` grows with meanings, not with nodes.
- Append-only, per kind: add meanings at the end, or kinds to a meaning; never remove, rename, or take a kind away. ComfyUI rejects a saved value that is no longer in a node's list.
- If a meaning changes, add a new one and treat the old one as legacy in the app; do not edit the list in place.

## How data flows

```
Workflow IO widgets  →  Comfy API JSON inputs  →  parser  →  api_config.mappings  →  Composer
```

Deploy and rollout order (editor + runner, backend registration, Image Reframer, etc.) are documented with the platform rollout notes, not in this repo.
