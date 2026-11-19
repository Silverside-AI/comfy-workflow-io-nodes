"""Add the current nodes, dropdown options and widgets to the node fixtures.

Run after adding a node, an input, a dropdown option or a ``VALUE_TYPES``
meaning, and commit the result with the change. Each node has its own file,
``tests/fixtures/nodes/<NodeClass>.json``. It only adds: entries for things
that no longer exist are kept, so the tests keep failing on a break instead of
the fixtures quietly following it.

    python3 tests/update_fixtures.py
"""

import json

from nodes import FIXTURES, WIDGET_TYPES, load_nodes

NODE_FIXTURES = FIXTURES / "nodes"
UPSTREAM = "upstream"  # stands in for whatever feeds a required link input


def _default(inp):
    cfg = inp["cfg"]
    if inp["type"] == "COMBO":
        return cfg.get("default", inp["options"][0])
    return cfg.get("default", {"INT": 0, "FLOAT": 0.0, "STRING": "", "BOOLEAN": False}[inp["type"]])


def _saved_cases(spec) -> dict:
    """One saved node with every widget at its default, plus one per dropdown option."""
    base = {}
    for name, inp in spec["inputs"].items():
        if inp["type"] in WIDGET_TYPES and not inp["cfg"].get("forceInput"):
            base[name] = _default(inp)
        elif inp["required"]:
            base[name] = [UPSTREAM, 0]
    cases = {"defaults": base}
    for name, inp in spec["inputs"].items():
        if inp["type"] == "COMBO" and not inp["from_comfyui"]:
            for option in inp["options"]:
                cases[f"{name}={option}"] = {**base, name: option}
    return cases


def _dump(data) -> str:
    """Widgets and outputs one per line; each saved case on one line, so an
    addition shows up in a diff as one added line."""
    lines = ["{"]
    for key in ("widgets", "outputs"):
        items = ",\n".join(f"    {json.dumps(item)}" for item in data[key])
        lines.append(f'  "{key}": [\n{items}\n  ],')
    cases = ",\n".join(f"    {json.dumps(case)}: {json.dumps(inputs, ensure_ascii=False)}"
                       for case, inputs in data["saved"].items())
    lines.append(f'  "saved": {{\n{cases}\n  }}')
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    NODE_FIXTURES.mkdir(parents=True, exist_ok=True)
    added = []
    for class_type, spec in load_nodes().items():
        path = NODE_FIXTURES / f"{class_type}.json"
        if not path.exists():
            data = {"widgets": spec["widgets"], "outputs": spec["outputs"], "saved": _saved_cases(spec)}
            added.append(f"{path.name}: new")
        else:
            data = json.loads(path.read_text())
            for key in ("widgets", "outputs"):
                old, now = data[key], spec[key]
                if now[:len(old)] == old and len(now) > len(old):
                    data[key] = now
                    added.append(f"{path.name}: {key} += {now[len(old):]}")
                # anything else is a break; leave the record so the test reports it
            for case, inputs in _saved_cases(spec).items():
                if case not in data["saved"]:
                    data["saved"][case] = inputs
                    added.append(f"{path.name}: saved {case}")
        path.write_text(_dump(data))
    print("\n".join(added) if added else "Fixtures already cover the current nodes.")


if __name__ == "__main__":
    main()
