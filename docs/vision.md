# Vision

Where this repo is heading, and the work in progress today to get there. For
the nodes and contract as they stand, see the [README](../README.md) and the
[contract doc](comfy-json-ui-contract.md).

## Extending Brand Brain from ComfyUI

A creative builds a feature as a ComfyUI workflow, exports it as JSON and
imports it into Brand Brain, where people use it as a workflow. We want that
to cover a whole feature, end to end:

1. **Backend: the ComfyUI workflow.** The graph is the backend code: it
   chains generative models, and ComfyUI's node language hides most of that
   complexity.
2. **Integration: the Workflow IO nodes.** Standard input, editing and output
   nodes mark what a workflow takes and returns, so Brand Brain can run it. As
   their semantics get more expressive, new features should need fewer and
   fewer changes to the nodes themselves.
3. **Frontend: the generated contract.** A script generates
   `workflow-io-contract.ts` from the nodes, so Brand Brain knows what the
   latest nodes mean. The goal is for Brand Brain to build a workflow's UI
   from it instead of by hand.

Workflows come first; the goal is for other Brand Brain features to be built
the same way.

## Semantic fields: meaning, not presentation

Early HTML tags such as `<b>`, `<br>` and `<hr>` were close to commands: they
said how the page should look. HTML then moved towards separating structure
from presentation, and semantic tags such as `<section>`, `<nav>` and
`<footer>` say what a part of the page *is*. That makes styling and parsing
easier, but the tag still doesn't decide how the page looks: CSS does.

Workflow IO nodes follow the same idea. Saying an input is a number is often
not enough; the node also says what the number is for, e.g. `value_type:
strength`. Brand Brain can use that to parse the workflow and pick a control,
but the node never says what the control is.

That's the boundary: **Workflow IO nodes say what a value means; Brand Brain
decides how it's shown.**
