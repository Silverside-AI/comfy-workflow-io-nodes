"""Add the current nodes, dropdown options and widgets to the fixtures.

Run after adding a node, an input, a dropdown option or a ``VALUE_TYPES``
meaning, and commit the result with the change. It only adds: entries for
things that no longer exist are kept, so the tests keep failing on a break
instead of the fixtures quietly following it.

    python3 tests/update_fixtures.py
"""

import json

from nodes import FIXTURES, WIDGET_TYPES, load_nodes

COVERAGE = FIXTURES / "workflows" / "coverage.json"
WIDGET_ORDER = FIXTURES / "widget_order.json"
UPSTREAM = "upstream"  # stands in for whatever feeds a required link input


def _default(inp):
    cfg = inp["cfg"]
    if inp["type"] == "COMBO":
        return cfg.get("default", inp["options"][0])
    return cfg.get("default", {"INT": 0, "FLOAT": 0.0, "STRING": "", "BOOLEAN": False}[inp["type"]])


def _base_inputs(spec):
    inputs = {}
    for name, inp in spec["inputs"].items():
        is_widget = inp["type"] in WIDGET_TYPES and not inp["cfg"].get("forceInput")
        if is_widget:
            inputs[name] = _default(inp)
        elif inp["required"]:
            inputs[name] = [UPSTREAM, 0]
    return inputs


def _load(path):
    return json.loads(path.read_text()) if path.exists() else {}


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main():
    nodes = load_nodes()
    added = []

    coverage = _load(COVERAGE) or {UPSTREAM: {"class_type": "ExternalNode", "inputs": {}}}
    for class_type, spec in nodes.items():
        base = _base_inputs(spec)
        wanted = {class_type: base}
        for name, inp in spec["inputs"].items():
            if inp["type"] == "COMBO" and not inp["from_comfyui"]:
                for option in inp["options"]:
                    wanted[f"{class_type} {name}={option}"] = {**base, name: option}
        for node_id, inputs in wanted.items():
            if node_id not in coverage:
                coverage[node_id] = {"class_type": class_type, "inputs": inputs}
                added.append(f"coverage: {node_id}")

    order = _load(WIDGET_ORDER)
    for class_type, spec in nodes.items():
        now = {"widgets": spec["widgets"], "outputs": spec["outputs"]}
        old = order.get(class_type)
        if old is None:
            order[class_type] = now
            added.append(f"widget order: {class_type}")
            continue
        for key in ("widgets", "outputs"):
            if now[key][:len(old[key])] == old[key] and len(now[key]) > len(old[key]):
                added.append(f"widget order: {class_type} {key} += {now[key][len(old[key]):]}")
                old[key] = now[key]
            # anything else is a break; leave the record so the test reports it

    _write(COVERAGE, coverage)
    _write(WIDGET_ORDER, order)
    print("\n".join(added) if added else "Fixtures already cover the current nodes.")


if __name__ == "__main__":
    main()
