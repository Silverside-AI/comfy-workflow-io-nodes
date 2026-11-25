# comfy-workflow-io-nodes

Custom ComfyUI nodes that let a workflow author declare its **API contract
inside the graph** instead of hand-mapping it in a deploy UI. When a workflow
is exported from ComfyUI (**Export (API)**), the nodes' widget values carry the
contract, and Brand Brain's parser builds the `api_config` from them. This repo
doesn't produce that JSON; its releases publish the node pack and a TypeScript
contract (see [Releasing](#releasing)).

- **Input nodes** are passthrough: they hold a `value` and output it. The API
  runner overrides `value` per call, always on this node's own field, never on a
  third-party node.
- **Editing nodes** pass media through; the app shows a crop, trim or point
  tool on it and sends the node's fields back.
- **Output nodes** mark what's returned to the caller and set its filename.

Docs: [Vision](docs/vision.md) ·
[Comfy JSON ↔ Brand Brain contract](docs/comfy-json-ui-contract.md)
(`value_type`, `api_config` mapping, actions) ·
[Editing nodes](docs/editing-nodes.md) · [Testing suggestions](docs/testing-suggestions.md) ·
[Changelog](CHANGELOG.md) ·
[AGENTS.md](AGENTS.md)

## Nodes

### Inputs (`Workflow IO/Inputs`)

| Node | Output | Notes |
|------|--------|-------|
| Text Input | STRING | single/multi-line |
| Int Input | INT | min/max/step; optional `value_type` |
| Float Input | FLOAT | min/max/step; optional `value_type` |
| Bool Input | BOOLEAN | |
| Enum Input | STRING | `options` → API enum allowlist; optional `value_type` |
| Multi Enum Input | STRING | several `options`, joined by `separator` (default `,`); optional `value_type` |
| Seed Input | INT | `randomize_if_omitted` |
| Image Input | IMAGE, MASK | LoadImage-style, reads the file the runner writes |
| Video Input | VIDEO | LoadVideo-style, decoding deferred to the consumer; optional trim (`start_frame`, `end_frame`, caps `max_frames` / `max_seconds`) |

Every input shares `param_name` (the API key), `required`, `description`,
`example`, `advanced`, `group`, `order`. `value_type` says what a value means,
never how to show it; see the [contract doc](docs/comfy-json-ui-contract.md#value_type-vocabulary).

### Editing nodes (`Workflow IO/Inputs`)

| Node | App tool |
|------|----------|
| Image/Video Reframe | crop / pad / rotate an image or video |
| Image/Video Reframe Composite | (none: pastes the processed crop back) |
| Video Trim | trim, optionally with a keyframe |
| Video Trim Composite | (none: puts the processed part back) |
| Point Selector | positive / negative points, e.g. for SAM |

No metadata block: the app finds them by class. Fields, outputs and editor
behaviour: [docs/editing-nodes.md](docs/editing-nodes.md).

### Outputs (`Workflow IO/Outputs`)

| Node | Takes | Notes |
|------|-------|-------|
| Image Output | IMAGE | png/jpg/webp |
| Video Output | VIDEO | audio preserved; `codec` (auto/h264/av1/prores, ComfyUI 0.44+) and a wirable `video_format` (MP4, ProRes, WebM, MKV) |
| 3D Output | FILE_3D | GLB, glTF, FBX, OBJ, STL in their own format, under the `3d` UI key |
| Text Output | STRING | a UTF-8 `.txt` returned as a `file` output; `action` + `fills` make it an app button such as **Suggest prompt** ([actions](docs/comfy-json-ui-contract.md#actions-a-step-the-app-runs-before-the-real-run-suggest-prompt)) |

Outputs are `OUTPUT_NODE`s that pass their input through, so they can sit
mid-graph. Wire `filename` for dynamic names.

## Install

Upload the zip from a [release](https://github.com/Silverside-AI/comfy-workflow-io-nodes/releases) (`comfy-workflow-io-nodes-<version>.zip`)
to Comfy; it unpacks to `custom_nodes/comfy-workflow-io-nodes/`, so a newer
zip replaces the old one. For local dev, clone into `ComfyUI/custom_nodes/`
and restart. No pip dependencies beyond ComfyUI's own.

Deploy to **both the editor and the runner**: a workflow saved in one fails at
cold start in the other if its nodes are missing.

## Development

Same flow as the Brand Brain repos, except this one has only **`main`** (no
`develop` or staging): alphas take staging's place.

1. Branch from the latest `main` with the Linear ticket's branch name.
2. Change the nodes, then run the checks:

   ```bash
   python3 tests/test_saved_workflows.py   # saved workflows still validate (CI runs this on every PR)
   python3 tests/update_fixtures.py        # after adding a node, input, dropdown option or VALUE_TYPES meaning
   ```

   Node changes must be additive: fixtures in `tests/fixtures/` only grow, new
   inputs go in `optional`, `VALUE_TYPES` is append-only. Details in
   [push-changes](.cursor/skills/push-changes/SKILL.md). Optional pre-commit
   hook: `pip install pre-commit && pre-commit install`.
3. Add a line to [CHANGELOG.md](CHANGELOG.md) if the change affects what
   workflows can contain or what Brand Brain must handle.
4. Open a PR into `main` titled `SIL-1234: <ticket title>`. **Saved workflows**
   must pass; Bugbot, then human review.
5. To test before merging, publish an **alpha** (below) and upload it to a
   scratch Comfy workspace.

## Releasing

The **Publish Comfy nodes and BB contract** action (Actions → Run workflow)
creates a GitHub Release with two files:

- `comfy-workflow-io-nodes-<version>.zip`: the node pack to upload to Comfy.
- `workflow-io-contract.ts`: the TypeScript contract generated from the nodes
  (`scripts/generate_workflow_io_contract.py`), which Brand Brain pins by tag.

| `release` | Run from | Result |
|-----------|----------|--------|
| `alpha` | any branch | Pre-release `alpha-<branch>`, versioned `<latest>+alpha.<branch>.<sha>`. Replaced on each run, linked in a comment on the branch's PR, deleted when the PR closes (**Alpha cleanup**). |
| `patch` (default) / `minor` / `major` | `main` only | Bumps the latest `v*` tag (`v0.1.0` → `v0.1.1` for a patch) and creates that release with generated notes. |

The run summary links the zip and contract. After a release, upload the zip to
the editor and runner, and bump the pinned contract tag in Brand Brain if the
contract changed.
