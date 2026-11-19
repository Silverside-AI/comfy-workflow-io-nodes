---
name: push-changes
description: >-
  Contributing to comfy-workflow-io-nodes. Use when editing Workflow IO nodes or
  api_nodes/common.py, especially VALUE_TYPES and value_type, and to keep the
  saved-workflow fixtures in tests/fixtures/ up to date.
---

# push-changes

Read [docs/comfy-json-ui-contract.md](../../../docs/comfy-json-ui-contract.md) for full context.

## Keep the saved-workflow fixtures up to date

`tests/fixtures/` stands in for workflows already saved in prod, and CI runs `python3 tests/test_saved_workflows.py` on every pull request.

- After adding a node, an input, a dropdown option or a `VALUE_TYPES` meaning or kind, run `python3 tests/update_fixtures.py` and commit the fixture changes with the node change.
- New inputs go in `optional`, and new widgets go after the existing ones.
- Fixtures only grow. Never edit or delete a fixture, or an entry in `widget_order.json`, to make a test pass: a failure means saved workflows would break. Change the node instead, or flag it to a human, since a real break needs stored workflows migrated.
- When a new kind of workflow ships (a new node in real use), add a small exported API workflow that uses it to `tests/fixtures/workflows/`.

## `VALUE_TYPES` is append-only

In `api_nodes/common.py`, **`VALUE_TYPES` may only grow**: add new meanings at the **end** of the table, or add a kind to an existing meaning. Never remove or rename a meaning, and never take a kind away from one (reordering breaks no saved workflow, but avoid it). Saved workflows store the chosen `value_type`, and ComfyUI checks it against that node's own list; invalid entries break loading. If a meaning is wrong, add a **new** type—leave existing values forever.
