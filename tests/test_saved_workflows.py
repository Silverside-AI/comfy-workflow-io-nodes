"""Workflows saved in prod must keep working after a node change.

Brand Brain stores each workflow version's exported API JSON, and the runner
validates it against the node definitions it has installed before every run.
These tests do the same against the fixtures in ``tests/fixtures/``:

* ``workflows/*.json``: API workflows known to work. Each Workflow IO node in
  them must pass the same checks as ComfyUI's ``validate_inputs``: the node
  class exists, every required input is present, a dropdown value is in the
  list, a number has the right type and is within min/max, a link points at an
  existing output. ``coverage.json`` holds every node and every dropdown option.
* ``widget_order.json``: each node's widgets and outputs, in order. Saved UI
  workflows store widget values by position and links by output index, so the
  current lists must start with the recorded ones (append only).

Fixtures only grow: never edit or delete one to make a test pass. A failure
means a saved workflow would break. ``python3 tests/update_fixtures.py`` adds
new nodes, options and widgets; it never removes anything.

Run: ``python3 tests/test_saved_workflows.py`` (no ComfyUI needed).
"""

import json
import unittest

from nodes import FIXTURES, load_nodes

NODES = load_nodes()
OURS = "WorkflowIO"


def _is_link(value) -> bool:
    return isinstance(value, list) and len(value) == 2 and isinstance(value[1], int)


def _type_matches(output_type: str, input_type: str) -> bool:
    if "*" in (output_type, input_type):
        return True
    return output_type in input_type.split(",") or input_type in output_type.split(",")


def validate(workflow: dict) -> list:
    """Errors ComfyUI would raise for the Workflow IO nodes in an API workflow."""
    errors = []
    for node_id, node in workflow.items():
        class_type = node.get("class_type", "")
        if not class_type.startswith(OURS):
            continue  # other packs' nodes aren't this repo's contract
        where = f"node {node_id} ({class_type})"
        spec = NODES.get(class_type)
        if spec is None:
            errors.append(f"{where}: node class no longer exists")
            continue
        given = node.get("inputs", {})
        for name, inp in spec["inputs"].items():
            if name not in given:
                if inp["required"]:
                    errors.append(f"{where}: required input '{name}' is missing")
                continue
            value = given[name]
            if _is_link(value):
                source = workflow.get(str(value[0]), {})
                source_spec = NODES.get(source.get("class_type", ""))
                if source_spec is not None:  # only our own nodes' outputs are known here
                    outputs = source_spec["outputs"]
                    if value[1] >= len(outputs):
                        errors.append(f"{where}: '{name}' links to output {value[1]} of node {value[0]}, "
                                      f"which has only {len(outputs)}")
                    elif inp["type"] != "COMBO" and not _type_matches(outputs[value[1]], inp["type"]):
                        errors.append(f"{where}: '{name}' ({inp['type']}) is linked to a {outputs[value[1]]} output")
                continue
            if inp["type"] == "COMBO":
                if not inp["from_comfyui"] and value not in inp["options"]:
                    errors.append(f"{where}: '{name}' value {value!r} is not in the list {inp['options']}")
            elif inp["type"] in ("INT", "FLOAT"):
                try:
                    number = int(value) if inp["type"] == "INT" else float(value)
                except (TypeError, ValueError):
                    errors.append(f"{where}: '{name}' value {value!r} is not {inp['type']}")
                    continue
                low, high = inp["cfg"].get("min"), inp["cfg"].get("max")
                if low is not None and number < low:
                    errors.append(f"{where}: '{name}' value {number} is below min {low}")
                if high is not None and number > high:
                    errors.append(f"{where}: '{name}' value {number} is above max {high}")
    return errors


class SavedWorkflowsStillValidate(unittest.TestCase):
    def test_workflows(self):
        paths = sorted((FIXTURES / "workflows").glob("*.json"))
        self.assertTrue(paths, "no fixture workflows found")
        for path in paths:
            with self.subTest(workflow=path.name):
                errors = validate(json.loads(path.read_text()))
                if errors:
                    self.fail(f"{path.name} would no longer run:\n  " + "\n  ".join(errors))


class WidgetsAndOutputsOnlyAppended(unittest.TestCase):
    def test_widget_order(self):
        recorded = json.loads((FIXTURES / "widget_order.json").read_text())
        for class_type, old in recorded.items():
            with self.subTest(node=class_type):
                current = NODES.get(class_type)
                if current is None:
                    self.fail(f"{class_type}: node class no longer exists")
                for key, what in (("widgets", "widget values by position"), ("outputs", "links by output index")):
                    now = current[key]
                    if now[:len(old[key])] != old[key]:
                        self.fail(f"{class_type} {key} changed from {old[key]} to {now}: saved workflows store "
                                  f"{what}. Only append new {key} after the existing ones.")


if __name__ == "__main__":
    unittest.main()
