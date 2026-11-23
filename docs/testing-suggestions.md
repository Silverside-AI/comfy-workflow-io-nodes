# Testing suggestions

Fixtures prove a saved graph loads. A local Comfy smoke proves a Workflow IO node does what its widgets say. A local `POST /prompt` is the same API a deployment uses. What changes is whether the graph can run on this machine.

## Local testing

### When this approach is recommended

- The change is inside a Workflow IO node (a value, a trim, a crop, a new field).
- The graph is only this pack plus core Comfy.
- You check the default, one normal value, and one boundary (empty, open end, clamp).

### How to test

Point `ComfyUI/custom_nodes/comfy-workflow-io-nodes` at the branch and restart Comfy so it imports that node code.

Write a small workflow that uses the node: the input wired to the matching output, a fixture you can count in Comfy’s input folder, and `value` set to that filename. Queue that workflow once per row. API JSON (`class_type` + `inputs`) is what `POST /prompt` runs. UI JSON (`nodes`, `links`, `widgets_values`) is what you open on the canvas, and **Export (API)** writes the API JSON from that graph. Check the output, not only that the queue finished: frame count, image size, or the echoed value. Confirm new widgets in `object_info` and in **Export (API)**.

### Example: video trim

The workflow file is **Video Input** wired to **Video Output**. Comfy does not call ffmpeg. ffmpeg is part of the test setup: it writes a 30-frame clip with the frame number painted on each frame, and you put that file in Comfy’s input folder. `end_frame` 0 means the last frame. Queue that workflow once per row.

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

After each queue, ffprobe counts the frames in the file Comfy wrote. That count is the check.

```bash
ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=nb_read_frames -of csv=p=0 output.mp4
```

## Testing in Comfy Cloud

### When this approach is recommended

- The graph calls a vendor API (image, video, or LLM nodes that need a key).
- The graph needs models or custom nodes that exist only on the Comfy deployment.
- You need the app to upload the file or send the new field.

### How to test

Create a deployment that includes the node and run the workflow on Comfy Cloud.
