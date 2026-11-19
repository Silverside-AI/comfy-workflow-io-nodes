---
name: push-changes
description: >-
  Contributing to comfy-workflow-io-nodes. Use when editing Workflow IO nodes or
  api_nodes/common.py, especially VALUE_TYPES and value_type.
---

# push-changes

Read [docs/comfy-json-ui-contract.md](../../../docs/comfy-json-ui-contract.md) for full context.

## `VALUE_TYPES` is append-only

In `api_nodes/common.py`, **`VALUE_TYPES` may only grow**: add new meanings at the **end** of the table, or add a kind to an existing meaning. Never remove or rename a meaning, and never take a kind away from one (reordering breaks no saved workflow, but avoid it). Saved workflows store the chosen `value_type`, and ComfyUI checks it against that node's own list; invalid entries break loading. If a meaning is wrong, add a **new** type—leave existing values forever.
