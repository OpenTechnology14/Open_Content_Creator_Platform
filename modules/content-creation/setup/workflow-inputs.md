# Creator Extend: configure a workflow before running it

**Labels:** `Content` · P-057

Creator Extend now packages its curated workflows with the desktop application. A normal app
launch can list and load them without a repository working directory. Changing or adding a
curated JSON file requires rebuilding the app; this is not an arbitrary workflow-file importer.
Empty starter scaffolds are omitted from the list.

1. Open Creator Extend and choose **Preflight** beside a workflow. It checks the configured
   ComfyUI endpoint, graph node classes, fixed model selectors and the server-reported GPU/VRAM.
   Resolve any named missing node or model first; the app keeps **Configure** disabled until the
   preflight passes.
2. Review the image, prompt and seed fields exposed by that template.
3. For images or masks, upload a PNG/JPEG/WebP up to 10 MiB, or enter a filename already in the
   configured ComfyUI input folder. The editor shows the server receiving the upload first.
4. Enter prompts and whole-number seeds (0–9007199254740991), then choose **Run with these inputs**.
5. The workflow card follows the existing pending/success/error states. Completed outputs appear
   in **Output history** for this app session. On validation or upload failure, the editor stays
   open for correction; no job is queued by an upload alone.

The panel only exposes supported literal image/text/seed fields. Model selection, node classes,
connections, video source fields and other custom-node parameters are unchanged. `LoadImageMask`
uses the template's channel setting; this is a file picker, not a mask-painting tool. For templates
that load mask images through `LoadImage`, supply the expected mask image yourself.

Edits apply to a freshly loaded copy of the bundled graph and do not change the template. Image
uploads use `overwrite=false`, and the actual filename returned by ComfyUI is used. Uploaded
files remain on that configured server even if you close the panel or a later job fails; clean
up inputs through your normal ComfyUI storage management. The upload request checks size and
raster signatures; ComfyUI performs actual image decoding when the workflow runs.

ComfyUI, required models and custom nodes must already be installed and configured. Preflight
checks only the node classes and fixed choices reported by the live server. Its VRAM values are
observations, not a compatibility threshold or output-quality guarantee; model terms, downloads
and a real output review remain operator work. The panel does not make every template compatible
with every OS/GPU or repair known upstream node issues. It does not add live video processing, job
cancellation, remote pairing or a new hosted service. Preview downloads accept PNG, JPEG, WebP,
GIF, MP4 and WebM, read at most 8 MiB per output, load at most four outputs per job and retain at
most twenty jobs. A later app restart does not restore unsaved field values or job history.

## Verification

From the repository:

```bash
cargo test --locked --manifest-path apps/creator-extend/src-tauri/Cargo.toml
npm --prefix apps/creator-extend run check
npm --prefix apps/creator-extend run build
make test
```

Optional acceptance against an operator-selected local ComfyUI server:

```bash
HCP_COMFYUI_ACCEPTANCE_URL=http://127.0.0.1:8188 cargo test --locked --manifest-path apps/creator-extend/src-tauri/Cargo.toml --test workflow_inputs_contract live_upload_prepare_queue_and_read_output -- --ignored
```

PowerShell equivalent:

```powershell
$env:HCP_COMFYUI_ACCEPTANCE_URL = 'http://127.0.0.1:8188'
cargo test --locked --manifest-path apps/creator-extend/src-tauri/Cargo.toml --test workflow_inputs_contract live_upload_prepare_queue_and_read_output -- --ignored
```

That explicit test uploads the small synthetic fixture, queues a model-free LoadImage → SaveImage
job, discovers its output through prompt history and retrieves the preview through the same
bounded helper used by the desktop UI. It writes input/output files on the selected
server. Ordinary offline tests do not contact it. Native Windows acceptance remains pending.
