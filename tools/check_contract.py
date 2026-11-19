#!/usr/bin/env python3
"""Fail on node changes that would break workflows already saved in prod.

Brand Brain stores each workflow version's exported JSON and the runner
validates every node's inputs against the installed node definitions before a
run. So a change here is safe only if it is additive. This script loads the
node definitions from a base ref (default ``origin/main``) and from the working
tree (or ``--head <ref>``) and compares them:

* a node class removed;
* an input removed, its type changed, or an optional input made required;
* a new **required** input on an existing node (new inputs must be optional);
* a dropdown (COMBO) option removed or renamed;
* an INT/FLOAT range narrowed (saved values outside it fail validation);
* a widget inserted before, or moved among, existing ones (saved UI workflows
  store widget values by position);
* an output removed or reordered (saved links point at output indexes);
* ``VALUE_TYPES`` in ``api_nodes/common.py``: a meaning removed, renamed or
  reordered, or a meaning losing a kind (append-only, per kind). Handles both
  the tuple form and the ``meaning -> (kinds, description)`` dict form.

Plain Python, no ComfyUI and no third-party packages. ``comfy_api`` (imported
inside the Video Output node's ``INPUT_TYPES``) is replaced by a stub whose
option lists are marked as coming from ComfyUI, so those dropdowns are not
compared: they depend on the installed ComfyUI, not on this repo.

This is the cheap half of the check. Replaying real prod workflows through
ComfyUI's ``validate_inputs`` still catches what a definition diff can't.

Usage:
    python tools/check_contract.py                       # working tree vs origin/main
    python tools/check_contract.py --base main --head my-branch
"""

import argparse
import importlib.util
import io
import subprocess
import sys
import tarfile
import tempfile
import types
from pathlib import Path

PACKAGE_DIR = "api_nodes"
WIDGET_TYPES = {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"}


class FromComfyUI(list):
    """Options supplied by the installed ComfyUI; not this repo's contract."""


def _install_stubs() -> None:
    class _Enumish:
        @staticmethod
        def as_input():
            return FromComfyUI(["auto"])

    util = types.ModuleType("comfy_api.util")
    util.VideoContainer = _Enumish
    util.VideoCodec = _Enumish
    pkg = types.ModuleType("comfy_api")
    pkg.__path__ = []
    pkg.util = util
    sys.modules.setdefault("comfy_api", pkg)
    sys.modules.setdefault("comfy_api.util", util)


def _repo_root() -> Path:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
    return Path(out.stdout.strip())


def _extract_ref(root: Path, ref: str, dest: Path) -> Path:
    """Write ``ref``'s api_nodes/ into ``dest`` without touching the working tree."""
    proc = subprocess.run(["git", "-C", str(root), "archive", "--format=tar", ref, PACKAGE_DIR],
                          capture_output=True)
    if proc.returncode != 0:
        sys.exit(f"check_contract: cannot read {PACKAGE_DIR}/ at '{ref}': {proc.stderr.decode().strip()}")
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as tar:
        try:
            tar.extractall(dest, filter="data")
        except TypeError:  # Python without extraction filters (< 3.10.12)
            tar.extractall(dest)
    return dest / PACKAGE_DIR


def _load(pkg_dir: Path, alias: str):
    """Import ``pkg_dir`` as a package named ``alias`` (so base and head can coexist)."""
    spec = importlib.util.spec_from_file_location(
        alias, pkg_dir / "__init__.py", submodule_search_locations=[str(pkg_dir)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    common = importlib.import_module(f"{alias}.common")
    return module.NODE_CLASS_MAPPINGS, getattr(common, "VALUE_TYPES", None)


def _describe(cls) -> dict:
    """{'inputs': {name: (section, type, options, cfg)}, 'widgets': [...], 'outputs': [...]}"""
    spec = cls.INPUT_TYPES()
    inputs, widgets = {}, []
    for section in ("required", "optional"):
        for name, entry in (spec.get(section) or {}).items():
            raw_type = entry[0]
            cfg = entry[1] if len(entry) > 1 and isinstance(entry[1], dict) else {}
            if isinstance(raw_type, (list, tuple)):
                kind, options = "COMBO", list(raw_type)
                dynamic = isinstance(raw_type, FromComfyUI)
            else:
                kind, options, dynamic = raw_type, None, False
            inputs[name] = {"section": section, "type": kind, "options": options,
                            "dynamic": dynamic, "cfg": cfg}
            if kind in WIDGET_TYPES and not cfg.get("forceInput"):
                widgets.append(name)
    return {"inputs": inputs, "widgets": widgets, "outputs": list(getattr(cls, "RETURN_TYPES", ()))}


def _check_node(name: str, base: dict, head: dict) -> list:
    errs = []
    for inp, b in base["inputs"].items():
        h = head["inputs"].get(inp)
        where = f"{name}.{inp}"
        if h is None:
            errs.append(f"{where}: input removed")
            continue
        if b["type"] != h["type"]:
            errs.append(f"{where}: type changed {b['type']} -> {h['type']}")
            continue
        if b["section"] == "optional" and h["section"] == "required":
            errs.append(f"{where}: optional input made required")
        if b["type"] == "COMBO" and not (b["dynamic"] or h["dynamic"]):
            lost = [o for o in b["options"] if o not in h["options"]]
            if lost:
                errs.append(f"{where}: dropdown option(s) removed or renamed: {lost}")
        if b["type"] in ("INT", "FLOAT"):
            for bound, narrower in (("min", lambda o, n: n > o), ("max", lambda o, n: n < o)):
                old, new = b["cfg"].get(bound), h["cfg"].get(bound)
                if new is None:
                    continue  # unbounded or unchanged-or-wider: saved values still pass
                if old is None:
                    errs.append(f"{where}: {bound} {new} added where there was none")
                elif narrower(old, new):
                    errs.append(f"{where}: {bound} narrowed {old} -> {new}")

    for inp, h in head["inputs"].items():
        if inp not in base["inputs"] and h["section"] == "required":
            errs.append(f"{name}.{inp}: new input is required; new inputs must go in 'optional'")

    bw, hw = base["widgets"], head["widgets"]
    if hw[:len(bw)] != bw:
        kept = [w for w in hw if w in bw]
        if kept != [w for w in bw if w in hw]:
            errs.append(f"{name}: existing widgets reordered: {bw} -> {hw}")
        else:
            inserted = [w for w in hw[:len(bw)] if w not in bw]
            if inserted:
                errs.append(f"{name}: widget(s) {inserted} inserted before existing ones; "
                            "append new widgets after the last existing one")

    bo, ho = base["outputs"], head["outputs"]
    if ho[:len(bo)] != bo:
        errs.append(f"{name}: outputs removed or reordered: {bo} -> {ho}")
    return errs


def _normalise_value_types(vt):
    """-> ordered {meaning: set(kinds) or None if kinds aren't declared (tuple form)}."""
    if vt is None:
        return None
    if isinstance(vt, dict):
        return {k: set(v[0]) for k, v in vt.items()}
    return {k: None for k in vt}


def _check_value_types(base_vt, head_vt) -> list:
    base, head = _normalise_value_types(base_vt), _normalise_value_types(head_vt)
    if base is None:
        return []
    if head is None:
        return ["VALUE_TYPES: removed from api_nodes/common.py"]
    errs = []
    bk, hk = list(base), list(head)
    if hk[:len(bk)] != bk:
        lost = [k for k in bk if k not in head]
        if lost:
            errs.append(f"VALUE_TYPES: meaning(s) removed or renamed: {lost}")
        else:
            errs.append(f"VALUE_TYPES: meanings reordered or inserted mid-list: {bk} -> {hk}; append new ones at the end")
    for meaning, kinds in base.items():
        new = head.get(meaning)
        if kinds is not None and new is not None and not kinds <= new:
            errs.append(f"VALUE_TYPES['{meaning}']: lost kind(s) {sorted(kinds - new)}")
    return errs


def compare(base_dir: Path, head_dir: Path) -> list:
    _install_stubs()
    base_nodes, base_vt = _load(base_dir, "_contract_base")
    head_nodes, head_vt = _load(head_dir, "_contract_head")
    errs = []
    for name, base_cls in base_nodes.items():
        head_cls = head_nodes.get(name)
        if head_cls is None:
            errs.append(f"{name}: node class removed (saved workflows reference it by class_type)")
            continue
        errs += _check_node(name, _describe(base_cls), _describe(head_cls))
    errs += _check_value_types(base_vt, head_vt)
    return errs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", default="origin/main", help="git ref the saved workflows were built on (default: origin/main)")
    parser.add_argument("--head", default=None, help="git ref to check (default: the working tree)")
    args = parser.parse_args(argv)

    root = _repo_root()
    sys.dont_write_bytecode = True
    with tempfile.TemporaryDirectory(prefix="contract-") as tmp:
        tmp = Path(tmp)
        base_dir = _extract_ref(root, args.base, tmp / "base")
        head_dir = _extract_ref(root, args.head, tmp / "head") if args.head else root / PACKAGE_DIR
        errs = compare(base_dir, head_dir)

    head_label = args.head or "working tree"
    if errs:
        print(f"Contract check FAILED ({head_label} vs {args.base}): these changes would break saved workflows.\n")
        for e in errs:
            print(f"  - {e}")
        print("\nSee docs/comfy-json-ui-contract.md. If a break is intended, it needs a migration of stored workflows.")
        return 1
    print(f"Contract check passed ({head_label} vs {args.base}): node changes are additive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
