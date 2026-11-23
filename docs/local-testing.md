# Local testing

Fixtures prove a saved graph loads. A local Comfy smoke proves a Workflow IO node does what its widgets say. A local `POST /prompt` is the same API a deployment uses. What changes is whether the graph can run on this machine.

## Local Comfy is enough

- The change is inside a Workflow IO node (a value, a trim, a crop, a new field).
- The graph is only this pack plus core Comfy.
- You check the default, one normal value, and one boundary (empty, open end, clamp).

Point `ComfyUI/custom_nodes/comfy-workflow-io-nodes` at the branch and restart Comfy. Wire the input to the matching output. Put a fixture you can count in Comfy’s input folder and set `value` to that filename. Queue once per row (`POST /prompt` or the canvas). Check the output, not only that the queue finished: frame count, image size, or the echoed value. Confirm new widgets in `object_info` and in **Export (API)**.

## Local Comfy is not enough

- The graph calls a vendor API (image, video, or LLM nodes that need a key).
- The graph needs models or custom nodes that exist only on the Comfy deployment.
- You need the app to upload the file or send the new field.

Run the real graph on the Comfy that has those nodes, weights, and keys. Pass the file the way a call does (the app upload, not a hand-typed `value`, when that is what you are testing). Check the product output, not the Workflow IO node alone. If the node is already right locally and the app does not send the new field yet, say that in the PR and do not block the node change on it.

## Example: video trim (local is enough)

Video Input → Video Output. A 30-frame clip in the input folder. `end_frame` 0 means the last frame.

```bash
ffmpeg -y -f lavfi -i "testsrc=size=320x240:rate=10" \
  -vf "drawtext=fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:text='%{n}'" \
  -frames:v 30 -pix_fmt yuv420p trim-source.mp4
```

| start | end | Frames |
|-------|-----|--------|
| 1 | 0 | 30 |
| 11 | 20 | 10 |
| 21 | 0 | 10 |
| 1 | 999 | 30 |

```bash
ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=nb_read_frames -of csv=p=0 output.mp4
```
