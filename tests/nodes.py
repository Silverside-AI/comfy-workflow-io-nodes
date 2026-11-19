"""Load the Workflow IO node definitions without ComfyUI, for the fixture tests.

``comfy_api`` (imported inside the Video Output node's ``INPUT_TYPES``) is
replaced by a stub. Its option lists are marked ``FromComfyUI``: they come from
the installed ComfyUI, not from this repo, so their values aren't checked.
"""

import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
WIDGET_TYPES = {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"}


class FromComfyUI(list):
    """Options supplied by the installed ComfyUI; not this repo's contract."""


def _stub_comfy_api() -> None:
    class _Options:
        @staticmethod
        def as_input():
            return FromComfyUI(["auto"])

    util = types.ModuleType("comfy_api.util")
    util.VideoContainer = util.VideoCodec = _Options
    pkg = types.ModuleType("comfy_api")
    pkg.__path__ = []
    pkg.util = util
    sys.modules.setdefault("comfy_api", pkg)
    sys.modules.setdefault("comfy_api.util", util)


def load_nodes() -> dict:
    """{class_type: {"inputs": {name: spec}, "widgets": [...], "outputs": [...]}}"""
    _stub_comfy_api()
    sys.dont_write_bytecode = True
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from api_nodes import NODE_CLASS_MAPPINGS

    return {name: describe(cls) for name, cls in NODE_CLASS_MAPPINGS.items()}


def describe(cls) -> dict:
    spec = cls.INPUT_TYPES()
    inputs, widgets = {}, []
    for section in ("required", "optional"):
        for name, entry in (spec.get(section) or {}).items():
            raw_type = entry[0]
            cfg = entry[1] if len(entry) > 1 and isinstance(entry[1], dict) else {}
            is_combo = isinstance(raw_type, (list, tuple))
            inputs[name] = {
                "required": section == "required",
                "type": "COMBO" if is_combo else raw_type,
                "options": list(raw_type) if is_combo else None,
                "from_comfyui": isinstance(raw_type, FromComfyUI),
                "cfg": cfg,
            }
            if inputs[name]["type"] in WIDGET_TYPES and not cfg.get("forceInput"):
                widgets.append(name)
    return {"inputs": inputs, "widgets": widgets, "outputs": list(getattr(cls, "RETURN_TYPES", ()))}
