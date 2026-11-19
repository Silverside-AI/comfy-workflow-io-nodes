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

`tests/fixtures/` stands in for workflows already saved in prod, and CI runs `python3 tests/test_saved_workflows.py` on every pull request. Each node has its own file, `tests/fixtures/nodes/<NodeClass>.json`: saved instances of it, and its widgets and outputs in order.

- After adding a node, an input, a dropdown option or a `VALUE_TYPES` meaning or kind, run `python3 tests/update_fixtures.py` and commit the changed node files with the node change.
- New inputs go in `optional`, and new widgets go after the existing ones.
- Fixtures only grow. Never edit or delete a fixture, or an entry in a node file, to make a test pass: a failure means saved workflows would break. Change the node instead, or flag it to a human, since a real break needs stored workflows migrated.
- When a new kind of workflow ships (a new node in real use), add a small exported API workflow that uses it to `tests/fixtures/workflows/`.

## Add a line to the changelog

A pull request that changes what workflows can contain (a node, an input, a dropdown option, a `VALUE_TYPES` meaning or kind) or what Brand Brain must handle adds one line to [CHANGELOG.md](../../../CHANGELOG.md), under today's date (newest first), with the PR link. Skip doc wording, refactors and test-only changes.

## `VALUE_TYPES` is append-only

In `api_nodes/common.py`, **`VALUE_TYPES` may only grow**: add new meanings at the **end** of the tuple. Never remove, rename, or reorder. Saved workflows store the chosen `value_type`; invalid entries break loading in ComfyUI. If a meaning is wrong, add a **new** type—leave existing values forever.
