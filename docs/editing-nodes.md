# Editing nodes

Reference for the editing nodes in `Workflow IO/Inputs`. The summary table is in the [README](../README.md#editing-nodes-workflow-ioinputs).

Media passes **through** these nodes; in a deployed workflow the app shows its
crop, trim or point tool on whatever reaches them and sends the node's fields
back. They have **no metadata block** (no `param_name`, `required`,
`description`, `example`, `advanced`, `group`, `order`): the app finds them by
class. In the editor each one shows the media after a first run.

| Node | In | Out | App tool |
|------|----|-----|----------|
| Workflow IO Image/Video Reframe | `source` (image or video), `mask` | `original`, `cropped`, `mask`, `crop_data` | crop / pad / rotate |
| Workflow IO Image/Video Reframe Composite | `frame`, `original`, `mask`, `crop_data` | `result` | (none: pastes back) |
| Workflow IO Video Trim | `video` | `video`, `keyframe`, `start_frame`, `end_frame`, `duration_trimmed`, `duration_total`, `keyframe_index`, `trim_data` | trim (+ keyframe) |
| Workflow IO Video Trim Composite | `trimmed_video`, `original_video`, `trim_data` | `video` | (none: puts the part back) |
| Workflow IO Point Selector | `image` | `image`, `positive_coords`, `negative_coords` | positive / negative points |

**Image or video (`mode`).** The Reframe and its Composite have `mode` image /
video. Their media sockets keep fixed names (`source`, `original`, `cropped`,
`frame`, `result`) and accept either type, so links survive saving and loading;
the editor labels and types them for the mode:

| mode | Reframe in → out | Composite in → out |
|------|------------------|--------------------|
| image | image → original_image, cropped_image | frame_image, original_image → image |
| video | video → original_video, cropped_video | frame_video, original_video → video |

A mismatch (a video into image mode) stops the run with a clear message.

## Workflow IO Image/Video Reframe

Image Reframe (ComfyUI-MaskAspectCrop) for images and videos. Any image or
video that should be **cropped, padded or rotated** in a deployed workflow goes
through this node.

- **In the editor** it works like Image Reframe without the upload: run once
  and the viewport shows the picture. Drag the frame to crop, push it past the
  edges to pad, turn the image with `rotation`, pick `padding_color`, set
  `feathering`. In video mode the viewport shows one frame at a time, with a
  timeline to scrub and a play button (the frame can be dragged while it
  plays); the whole clip is reframed with the one frame.
- **Frame fields** (the app's crop tool sets them, in source pixels):
  `center_x`, `center_y`, `frame_width`, `frame_height` (0 = full image),
  `rotation` (degrees, clockwise), `padding_color` (grey/black/white/green),
  `feathering` (px). `aspect_ratio` (free/16:9/4:3/1:1/3:4/9:16/21:9) only
  locks the frame's proportions while dragging, in the editor and in the app.
  Optional `crop_purpose` says what the crop is for, so the app can show it
  fittingly: `frame` (the crop or padding is the output's framing: reframe,
  outpaint), `region` (a part to process and paste back) or `auto` (default:
  the app infers it from the graph, e.g. a Composite pasting the crop back
  means `region`).
- **Outputs:** `original` (the image, or the video passed through), `cropped`
  (an image, or a video with the source's audio and frame rate), `mask` (1 in
  the padding, feathered into the image), `crop_data` (the same `CROP_DATA` as
  Image Reframe, so either Composite can paste back).
- In video mode the frame size is rounded down to even numbers (encoders need
  them); the editor shows the rounded size.
- **For the app:** show the crop tool on whatever reaches `source` (usually a
  Workflow IO Image / Video Input upload). The frame is in pixels of the source
  it was drawn on, so start the tool at the full frame for each new upload and
  send the fields back.

```
WorkflowIOImageVideoReframe node "7"  ->  inputs = {
    mode: "video", center_x: 240, center_y: 135, frame_width: 184,
    frame_height: 326, rotation: -6, aspect_ratio: "9:16",
    padding_color: "black", feathering: 0, crop_purpose: "frame",
    source: ["4", 0] }
```

## Workflow IO Image/Video Reframe Composite

Image Reframe Composite for images and videos: `paste` `original onto frame`
(default; puts the original back onto a processed or outpainted frame, output
in frame space) or `crop onto original` (puts the processed crop back into the
original, undoing crop and rotation; output in original space), `feather`
(px), `resize_source`, optional `mask`. `frame` is the processed result,
`original` and `crop_data` come from the Reframe node. In video mode frames are
matched by time (a processed clip at another frame rate or length still lines
up) and the result keeps the original's audio and frame rate.

## Workflow IO Video Trim

Load Video (Trim + Keyframe) (ComfyUI-VideoTrimmer) for a video passing
through. Any video the person running the workflow should **trim** goes
through this node.

- **In the editor** it works like Load Video (Trim + Keyframe) without the
  upload: run once and the timeline shows the video (thumbnail strip, white
  playhead, yellow trim handles that snap to the other markers, play, arrow
  keys ±1 / shift ±10, space to play). Frame numbers come with their time
  (`Frame 37 · 1.50s`; start, end and keyframe in the readout).
- **`mode`**: `trim` (default) = a start and an end; `trim + keyframe` = also a
  keyframe, which appears as soon as the mode is picked (at the playhead) and
  is dragged on the timeline. In `trim` mode the keyframe is hidden and
  ignored (the keyframe outputs give the start frame). The mode also tells the
  app whether its trim tool shows a keyframe marker.
- **Trim fields** (the app's trim tool sets them): `start_frame` (from 1),
  `end_frame` (inclusive; 0 = the last frame, which the editor also stores
  when the end handle sits on the last frame), `keyframe` (0 = the start
  frame; must lie inside the trim).
- **Outputs:** `video` (trimmed, with its audio), `keyframe` (IMAGE),
  `start_frame`, `end_frame`, `duration_trimmed`, `duration_total` (frames),
  `keyframe_index` (0-based inside the trim), as in Load Video (Trim +
  Keyframe), plus `trim_data` (where the trim sits, for the Trim Composite).
- A video that is a plain file (a Workflow IO Video Input or Load Video
  upload) is trimmed frame-exactly from its timestamps, without decoding;
  anything else (generated in the graph, already trimmed) is decoded and
  sliced.
- **For the app:** show the trim tool on whatever reaches `video`; frame
  numbers are counted in that video, so start at the whole video for each new
  upload.

## Workflow IO Video Trim Composite

Puts a processed version of the trimmed part back into the original video's
timeline: frames `start_frame`..`end_frame` (from `trim_data`) are replaced,
the rest of the video and its audio stay as they were, and the processed frames
are resized to the original's size. `fit`: `by time` (default; the processed
part plays at its own speed, cut short or its last frame held to fill the slot)
or `stretch` (sped up or slowed down to fill the slot exactly). The original
must be the video that went into the trim node.

## Workflow IO Point Selector

Positive and negative points on an image passing through. Any image the person
running the workflow should **click points on** (for segmentation) goes
through this node.

- **In the editor** it works like a points editor: run once, then click to add
  a positive point (green), shift-click or right-click for a negative one
  (red), drag to move, right-click a point to delete it, "Clear points" to
  start over.
- **Point fields** (the app's point tool sets them): `positive_points`,
  `negative_points` as JSON `[{"x": 120, "y": 340}, ...]` in pixels of the
  image (empty = none; `[[x, y], ...]` is accepted too). Points outside the
  image are moved onto its edge.
- **Outputs:** `image` (passed through), `positive_coords`,
  `negative_coords`: JSON in KJNodes Points Editor's format, which core SAM3
  Detect (`positive_coords` / `negative_coords`) and SAM2
  (`coordinates_positive` / `coordinates_negative`) read. No points → `[]`.
- **Video segmentation:** pass the keyframe (Video Trim in `trim + keyframe`
  mode) through this node, segment that frame (SAM3 Detect), then track from
  it with AutoMatte: SAM3 Track From Keyframe (ComfyUI-AutoMatte), which takes
  `keyframe_index` and tracks forward and backward with core SAM3. Core SAM3
  Video Track and SAM2's main node always start from the first frame of the
  frames they get. (SeC takes an annotation frame, but its model bundles
  Qwen2.5-3B under a research-only, non-commercial licence.)
- **For the app:** show the point tool on whatever reaches `image`; points
  are in that image's pixels, so start empty for each upload.

## Editor previews

The editing nodes write their viewport/timeline preview (a
small H.264 copy, a thumbnail strip, a PNG) to ComfyUI's temp folder only when
the run was queued from the editor (which sends the UI workflow along); API
runs skip it.
