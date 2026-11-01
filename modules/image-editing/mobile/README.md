# Mobile Image + Video Editing

API endpoints and UI specifications for the Creator Extend mobile app's
editing features. The mobile app acts as a canvas and mask painter — all
AI compute runs on the user's desktop ComfyUI instance.

## Architecture

```
Mobile App (Tauri)
  ├── Image/video viewer
  ├── Mask painter (tap, draw, auto-select)
  ├── Prompt input
  └── Operation picker (fill, remove, expand, upscale, restyle)
        │
        ▼  HTTP POST to FastAPI
Desktop Stack
  ├── FastAPI /api/v1/edit/*  (receives image + mask + params)
  ├── ComfyUI (runs inpainting workflow)
  └── MinIO (stores input + output)
        │
        ▼  HTTP response or WebSocket push
Mobile App
  └── Shows result, allows [Save] [Edit More] [Undo] [Share]
```

## Editing Modes (modeled after ComfyUI mask editor)

### Image Editing
1. **Generative Fill** — draw/tap area, type what to fill with
2. **Remove Object** — draw over object, AI reconstructs background
3. **Expand Canvas** — drag edges outward, AI fills new area
4. **Restyle Region** — select area, apply style/prompt to just that area
5. **Upscale** — enhance resolution 2x or 4x
6. **Auto-Select** — tap on object, SAM segments it automatically

### Video Editing
Modeled after ComfyUI's video node workflow where you can select specific
frames and regions to edit while leaving the rest untouched:

1. **Scrub to frame** — timeline scrubber to pick the frame to edit
2. **Select region** — draw mask on the frame (same tools as image)
3. **Edit region** — fill/remove/restyle just that area
4. **Propagate** — optionally apply the edit across a frame range
   (uses temporal consistency via optical flow or frame interpolation)
5. **Export clip** — save edited segment as video

### Video Frame Operations
- **Single frame edit** — edit one frame, export as still or re-insert
- **Range edit** — select frame range, apply edit across all frames
- **Keyframe edit** — edit keyframes, interpolate between them
- **Object tracking** — select object in first frame, mask follows it
  (uses SAM + point tracking via CoTracker or similar)

## API Endpoints (FastAPI)

```
POST /api/v1/edit/inpaint
  Body: { image: base64, mask: base64, prompt: str, model: str }
  Returns: { job_id: str, status: "queued" }

POST /api/v1/edit/remove
  Body: { image: base64, mask: base64 }
  Returns: { job_id: str, status: "queued" }

POST /api/v1/edit/outpaint
  Body: { image: base64, direction: str, pixels: int, prompt: str }
  Returns: { job_id: str, status: "queued" }

POST /api/v1/edit/upscale
  Body: { image: base64, scale: 2|4, model: str }
  Returns: { job_id: str, status: "queued" }

POST /api/v1/edit/auto-select
  Body: { image: base64, point: [x, y] }
  Returns: { mask: base64 }

POST /api/v1/edit/video/frame
  Body: { video_url: str, frame_number: int, mask: base64, prompt: str }
  Returns: { job_id: str, status: "queued" }

POST /api/v1/edit/video/range
  Body: { video_url: str, start_frame: int, end_frame: int,
          mask: base64, prompt: str, propagation: "keyframe"|"all" }
  Returns: { job_id: str, status: "queued" }

GET /api/v1/edit/status/{job_id}
  Returns: { status: "queued"|"processing"|"done"|"error",
             result_url: str|null, progress: float }

WebSocket /ws/v1/edit/progress
  Pushes: { job_id: str, progress: float, preview: base64|null }
```

## ComfyUI Workflow Mapping

Each API endpoint maps to a specific ComfyUI workflow JSON:

| Endpoint     | Workflow                                |
| ------------ | --------------------------------------- |
| /inpaint     | `inpaint-fill-v1.json`                  |
| /remove      | `inpaint-remove-v1.json`                |
| /outpaint    | `outpaint-expand-v1.json`               |
| /upscale     | `upscale-4x-v1.json`                    |
| /auto-select | `auto-select-sam-v1.json`               |
| /video/frame | `video-frame-edit-v1.json`              |
| /video/range | `video-range-edit-v1.json`              |

The FastAPI endpoint loads the workflow JSON, injects the user's image/mask
as inputs, queues it to ComfyUI's API, and streams progress back.

## Mobile UI Spec

### Mask Painter
- **Brush tool** — finger draws mask (adjustable size via pinch)
- **Tap to select** — tap sends point to SAM, returns auto-mask
- **Lasso tool** — draw closed shape, fills as mask
- **Invert** — flip mask selection
- **Feather slider** — blur mask edges (0-50px)
- **Undo/Redo** — stack-based

### Result Handling
- Side-by-side before/after comparison (swipe to reveal)
- Layer stack — each edit is a layer, can toggle visibility
- Export: save to camera roll, upload to MinIO, share to socials

## Mobile scrub-select-edit flow

The interface this API backs:

1. Load a video from the camera roll or MinIO
2. Scrub the timeline to a frame
3. Tap or draw to select a region on that frame
4. Type a prompt and choose an operation (fill / remove / restyle)
5. The edit is processed on **desktop ComfyUI**, not on the device
6. Optionally propagate the edit across a frame range

Step 6 depends on `video-range-edit-v1.json`, which is **not built** — see
[`../workflows/README.md`](../workflows/README.md). Single-frame edits work against
`video-frame-edit-v1.json`; range propagation has no workflow behind it yet.

