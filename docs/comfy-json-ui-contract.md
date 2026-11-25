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

## Exported JSON → `api_config`

Each API node serializes its widgets into the API JSON `inputs`. The
parser maps:

```
WorkflowIOTextInput node "2"  ->  api_config.mappings["prompt"] = {
    node_id: "2", field: "value", type: "string", required: true,
    default: {enabled: true, value: "a photograph of a cat"},
    tooltip: "<description>", advanced_setting: false }

WorkflowIOFloatInput node "5"  ->  api_config.mappings["strength"] = {
    node_id: "5", field: "value", type: "float", ...,
    min: 0, max: 1, step: 0.05, value_type: "strength" }   # "none" when absent

WorkflowIOVideoInput node "6"  ->  api_config.mappings["video"] = {
    node_id: "6", field: "value", ...,
    start_frame: 1, end_frame: 0,    # trim; (1, 0) = the whole video
    max_frames: 0,                   # most frames the trim may keep; 0 = no limit
    max_seconds: 0,                  # longest the trim may last, in seconds; 0 = no limit
    max_length: 0 }                  # older name of max_frames; still applies

WorkflowIOImageOutput node "8"  ->  api_config.output_nodes = ["8", ...]

WorkflowIOTextOutput node "9" with action  ->  api_config.actions["Suggest prompt"] = {
    node_id: "9", fills: "prompt", inputs: ["video", "reference_image"] }
    # left out of output_nodes and of the normal run's workflow
```

A Video Input's optional `start_frame` / `end_frame` trim the uploaded video
before it reaches the graph: frames counted from 1, inclusive, `end_frame` 0 =
the last frame (the same convention as Workflow IO Video Trim). The app sends
them per call next to `value`; when absent the whole video is used, as before.
The workflow author can cap the trim's length (0 = no limit): `max_frames` in
frames, for models limited by frame count (upscalers), and `max_seconds` in
seconds, for models limited by duration (video generation), measured on the
clip's own timestamps. `max_length` is the older name of `max_frames`, kept so
workflows saved with it keep their cap. The app's trim tool should keep the
selection within every cap set, and a longer range that still arrives is cut
short at its end by the strictest one.

Because `output_nodes` is emitted as an allowlist (not a rename map), the runner
returns each output with the exact filename the node saved — no server-side
renaming. See [`examples/sample_api_workflow.json`](../examples/sample_api_workflow.json)
for the full exported shape the parser consumes.

## Actions: a step the app runs before the real run (Suggest prompt)

A Workflow IO Text Output with `action` set (a button label, e.g. `Suggest
prompt`) and `fills` (the `param_name` of an input, e.g. `Prompt`) is a step the
app runs on its own. Example: a video edit whose prompt an LLM can write from the
clip and the reference. The user presses **Suggest prompt**, the written prompt
appears in the Prompt field, they read it, change it if they like, and press
Generate: the real run uses the field as it is, so what they see is what runs.

How the app runs it:

1. **The action** (button pressed): send the workflow trimmed to that Text Output
   and every node that feeds it. ComfyUI runs every output node it is given, and
   deployments drop ComfyUI's `partial_execution_targets`, so trimming is how
   only the suggestion branch runs (no render). Send values only for the inputs
   left in the trimmed workflow; enable the button once those are filled.
2. **The result**: the job returns one `file` output, `<output_name>.txt` (UTF-8);
   its content goes into the input named by `fills`.
3. **The real run**: send the workflow without its action outputs, with the
   input as the user left it. Nodes that only fed the action don't run.

[`tools/action_graph.py`](../tools/action_graph.py) does both trims and lists each
action's inputs (`python tools/action_graph.py workflow_api.json [--write]`).
With `action` empty, the text is simply returned with the normal run.

## How data flows

```
Workflow IO widgets  →  Comfy API JSON inputs  →  parser  →  api_config.mappings  →  Composer
```

Deploy and rollout order (editor + runner, backend registration, Image Reframer, etc.) are documented with the platform rollout notes, not in this repo.
