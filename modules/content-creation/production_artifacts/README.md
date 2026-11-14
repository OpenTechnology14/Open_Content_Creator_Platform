# Finalized-media production exports

P-067-ORCH-04, Content Creation. This package prepares local YouTube longform, YouTube
Shorts and TikTok files from an explicitly imported finalized source. It does not operate
an App walkthrough, OBS, accounts, the native Library or uploads. App integration and
independent exact-head review remain separate acceptance steps. The legacy inbox schema1
and existing Shorts CLI remain compatible.

## Running and authority

Portable DTO/schema imports support Python 3.11+. Filesystem/media worker execution is
limited to audited **CPython 3.11.18, 3.12.10 and 3.12.13**, with the existing Shorts dependencies
(`pydantic` v2 and `imageio-ffmpeg`). No installation, service, GPU, account or network is required once
these local dependencies are available. The fixed worker entry point is:

```sh
PYTHONPATH=modules/content-creation python -B -m production_artifacts --registry-fd 3
```

Descriptor 3 must be an inherited, private launcher registry. It is not a request parameter.
The trusted native launcher selects an existing approved, absolute, symlink-free root and
registers finalized input handles. Its private registry has this shape:

```json
{
  "schema_version": 1,
  "root_id": "root-one",
  "root_path": "<absolute approved root>",
  "inputs": {
    "input-one": {
      "parent": "<absolute approved input directory>",
      "relative_path": "recording.mp4",
      "sha256": "<expected lowercase SHA256>",
      "source_profile_id": "stream-main",
      "content_profile_id": "content-main",
      "origin": "manual"
    }
  }
}
```

The strings in angle brackets are documentation placeholders, not valid registrations.
Requests can reference only these opaque handles. They cannot add roots, paths, executables,
filters, environment variables, URLs or managed-capture authority. Manual and fixture origins
are pinned by the launcher and cannot be relabelled. Managed registration is deliberately
unsupported until the reviewed native finalization receipt exists. The launcher retains its
private original path/identity registry; portable manifests contain relative snapshot paths.
CLI tests prove filesystem behavior, not native ID, pack, webview-origin or capture admission.

macOS and Linux use directory descriptors, `openat`/no-follow flags, exclusive files and
handle-based hashing/decoding. Pass canonical macOS temporary roots (`/private/tmp`), since
`/tmp` itself is a symlink. Windows fails closed with `platform_unavailable`; native Windows
handle/reparse-point implementation and physical acceptance remain required. No shipping
source contains a workstation-specific interpreter or FFmpeg path.

ORCH04-CI-01 keeps package, schema, protocol and worker-help imports available on Windows.
The missing POSIX `fcntl` capability is detected at runtime admission; roots, stores, exports,
source/registry admission, descriptor media operations and process launch reject with
`platform_unavailable` before root/disk/process access. There is no unlocked fallback or new
Windows filesystem implementation. Worker startup exits2 with the allowlisted
`platform_unavailable` diagnostic before reading its registry. Missing `fcntl` on a POSIX host
also fails closed.

Portable DTO/wire/import and positive unsupported-admission tests run on every CI host.
Only POSIX descriptor/media/process cases use explicit platform reasons or a POSIX fixture
exclusion on Windows. The supported Mac critical suite still runs with the no-skips plugin.
A fresh interpreter blocks only `fcntl` to reproduce the collection defect off Windows;
this controlled simulation is separate from the native Windows CI result. Import/admission
compatibility does not establish Windows export, app or physical-host acceptance.

DigitalOcean: there is no daemon, HTTP endpoint, Compose service or cloud integration.
An opt-in batch launcher could use the same approved local-filesystem contract on Linux;
DigitalOcean execution has not been accepted. Capture and ordinary exports remain local.

## Candidate wire v1 — independent review pending

[wire/schema.json](wire/schema.json) and [wire/roundtrip.json](wire/roundtrip.json) are the
candidate Rust/TypeScript handoff. ORCH04-R1 refines this unaccepted ABI; it is not frozen
and ORCH05 must wait for independent acceptance. All names are snake_case; unknown fields, coercions,
nonfinite numbers, invalid IDs and future versions are rejected. The minimal namespace
contains ProductionSession, FinalizedSource, ExportRequest/Attempt, Artifact, stored
PlanRecord, metadata, JobEvent, request/reply and command payload DTOs. Future capture and
publication DTOs/runtime are intentionally absent. Timestamps are UTC; elapsed time and
process epochs are local to one worker lifetime.

One JSON object per line, request and response at most 1 MiB. Requests have
`{schema_version:1, request_id, command, payload}`. Responses have
`{request_id, ok:true, revision?, value}` or
`{request_id, ok:false, error:{code,retryable}}`. Malformed envelopes may return a null
request ID. An oversized stdio frame is fatal, so its suffix cannot become another command.
Replies can arrive out of order: correlate by request ID, never by arrival order.

| Command | Payload schema | Result |
|---|---|---|
| `production.create` | `Create` | ProductionSessionV1, revision1 |
| `production.list` | `Page` | items and nullable next_cursor |
| `production.get` | `Get` | production, sources, plans, attempts, independent account/publication state |
| `source.register` | `SourceRegister` | validated immutable source and revision |
| `plan.register` | `PlanPayload` | immutable clip_plan_ref (id/hash) and revision |
| `export.start` | `ExportRequestV1` | job_id, attempt_id, queued phase and revision |
| `job.get` | `JobGet` | authoritative attempt, persistence error and account/publication state |
| `job.cancel` | `JobCancel` | durable idempotent cancellation acknowledgement and revision |
| `artifact.inspect` | `ArtifactGet` | immutable artifact plus current local/review/account/publication state |

Plan registration accepts strict `ExportJobV1`, not the permissive legacy ShortsJob.
Every nested object forbids unknown fields and coercions. There is one bounded manual section;
`automatic` and `edit.enabled` require literal JSON false. `PlainEditV1` has no style, watermark,
caption or punch-in payload. All persisted free text, including section/clip labels, uses
portable-text-v1; its forbidden URI/control pattern appears in JSON Schema as well as Python.
`wire/negative.json` supplies cross-language rejection cases for strings in numeric/boolean
fields, boolean/float/future schema versions, nested URLs, unknown/unused fields and limits.
Native Rust/TS decoders must pass both positive and negative fixtures, including strict JSON
scalar types; JSON Schema alone is not permission to coerce values.

The adapter converts validated job data to the existing selector in memory, then projects into
strict `ExportClipPlanV1`. The legacy Shorts CLI behavior is unchanged. Only this strict plan is
stored with literal title/description and metadata revision. Initial selection is manual2–10s,
fixed walkthrough classification, pinned show/source/session, and no editing. Other timings
or edits require a future reviewed preset. Plan hash is SHA256 of canonical JSON of
production_id, source_id, clip_plan, title, description and metadata_revision, excluding
id/schema/hash fields. Export takes exactly one immutable stored reference. Development roots
written before this ABI repair may fail strict parsing; retain them read-only, use a fresh root
and explicit source import, and never silently rewrite their plans or successful files.

Create, source, plan, export and cancel mutations require operation_id. Repeating the identical
payload returns the original durable result, even after restart; an altered payload with that
key returns `operation_conflict` before writes. This includes expected_revision in the payload
hash. Revision CAS applies before every mutation; stale expectations return
`revision_conflict` with no committed change. Progress updates also advance production revision.
An export acknowledgement is not completion; query job.get after duplicate acknowledgement.
Cancellation acknowledges a request, not a completed termination. A new retry uses a new
operation key and current revision and creates a fresh attempt.

Events are `{event:"job.event.v1",value:JobEventV1}` (at most16 KiB). Sequence increases within
an attempt and includes process_epoch/generation/job/attempt correlation. The 64-event memory
ring is coalesced under backpressure; reconnect uses polling snapshots. The native receiver
must discard stale generations/sequences and validate all correlation fields. Progress counts
validated destination outputs, not invented frame percentages. Diagnostic requests use a
separate single-worker lane (one queued request) so status/cancel remain responsive. Output
queue8, bounded 128 KiB subprocess diagnostics, no raw stderr/request contents in replies.
A disconnected/blocked host cancels current owned work; no persisted PID authorizes a signal.

Error codes are enumerated in schema `ErrorV1`/attempt/event fields. Admission failures include
`invalid_request`, `invalid_registry`, `unsafe_path`, `platform_unavailable`,
`production_unavailable`, `source_unavailable`, `profile_conflict`, `plan_conflict`,
`revision_conflict`, `operation_conflict`, `corrupt_state` and `limit_exceeded`. Runtime codes
include `dependency_unavailable`, `disk_space`, `disk_unavailable`, `media_limit`,
`invalid_media`, `media_failed`, `source_changed`, `process_timeout`, `cancelled`,
`export_busy`, `execution_unsettled`, `worker_busy`, `job_unavailable`, `job_not_owned`, `artifact_unavailable`,
`terminal_attempt`, `worker_restarted` and `persistence_failed`. No error contains an input
path, account label, credential, provider response or secret URL.

## Storage, failures and truth

One private root ledger `state.json` owns revisions, IDs, operation results, source records,
plans and attempt history. Updates use a bounded2-second interprocess lock and commit using a same-directory
exclusive temporary file, flush/fsync, atomic replace and directory fsync. A portable snapshot
is written at `<profile>/<production>/manifest.json` before the ledger commit. **The ledger is
authoritative**: a crash may leave that portable snapshot one revision ahead. Native readers
must get/admit through the worker, not infer a job from a standalone manifest. Such orphaned
snapshot/files are retained evidence; they are never automatically adopted, replayed or published.

A source is held open, identity/hash/full-decode checked, exclusively copied, fsynced, rehashed
and decoded from the independent copy. Name publication is provisional: the final no-follow
path must bind the retained validated descriptor, with identical bytes/hash/full decode and
unchanged identities for every ancestor. Reopening after decode checks name replacement; a
second binding/stamp/ancestor check occurs under ledger CAS immediately before admission.
Swapped temporary/final names, symlinks or moved/replaced ancestors reject admission and retain
all orphan evidence. The pending copy name is retained rather than unlinking a possibly
replaced entry; it is an additional hardlink to our independent copy, never to the original. Original bytes are not
modified or hardlinked. Registration pins both profiles and source hash. Losing the original
later does not invalidate a verified snapshot. Missing/changed snapshots block exports.

Outputs occupy `<profile>/<production>/<destination>/attempts/<attempt>/`, with numeric
video/clip filenames, metadata.json and artifact.json. Raw `.encoded` files are retained as
attempt evidence and have no preview/validated authority. Successful media and metadata are
committed before the aggregate attempt update. Terminal attempts are never reopened. A fresh
retry never overwrites prior success. Individual errors yield partial or failed state; cancelling
preserves earlier artifacts. The fixed codec/probe inherits the root execution lease and a
lifetime witness pipe. **Every process retaining media write authority must retain the lease;
every process whose lifetime must delay terminal return must retain the witness.** These are
trusted fixed-codec/helper obligations; the descriptors do not enforce media-writer containment.
A helper that closes both but retains media can write after witness EOF and exclusion release.
The maintained descriptor-drop negative fixture demonstrates this excluded boundary. Native
launcher/packaging must pin and verify the supported codec/helper chain and descriptor behavior;
descriptor-closing, close-fds/exec or detached helper chains need separate containment proof
before support. Lease inheritance and process-group cancellation are not an executable sandbox.

Under that obligation, a worker death leaves inherited leases excluding new work; restart
reports recovery_required/busy while a holder remains. A live worker waits for witness EOF.
Polling reacquires exclusion after release and only then marks unfinished attempts interrupted.
An explicit new operation/current revision creates a fresh retry. No recovery mutation occurs
in export admission: changed operation keys and stale revisions leave the ledger unchanged.
A released but unreconciled attempt rejects new exports as export_busy until a valid
status/get/list observation reconciles it. No persisted PID/group is adopted or signalled.
An escaped descendant retaining the lease/witness leaves execution_unsettled/recovery_required
and exclusion intact until release; a descriptor-dropping writer is outside this guarantee.

Signalling authority is separate from execution exclusion. The fixed worker uses audited
CPython 3.11.18/3.12.10/3.12.13 Popen reapers and their **private** _waitpid_lock implementation, not a generic
Python ownership guarantee. Group check-and-signal holds that lock for the entire syscall;
it never calls poll recursively under the lock. A busy lock grants no signal authority.
An observed returncode revokes signalling permanently for that Popen, including KILL after
TERM-to-reap retirement. An exited but unreaped leader still reserves its ID under the
supported policy; no getpgid/killpg(0) existence check or numeric reuse assumption is used.

The supported launcher/worker must keep OS-default SIGCHLD (no SIG_IGN, custom handler or
SA_NOCLDWAIT), exclusive child reaping through the pinned Popen wait/poll methods, and unchanged
stdlib helper bindings for the whole worker lifetime. No foreign/raw waitpid/waitid reaper,
native signal-policy mutation or monkeypatch is supported. Competing Popen wait/poll uses the
same lock and is tested across the reaped-before-returncode interval. Runtime/version/helper
availability, loaded reaper-source fingerprints and Python-visible default SIGCHLD are checked before worker-registry reads or
child launch; unsupported configuration fails platform_unavailable. The native launcher must
pin/verify the interpreter/stdlib and native reaper policy too; Python introspection alone
cannot certify foreign native reapers or SA_NOCLDWAIT. If authority is lost, cancellation
retains exclusion and eventually reports execution_unsettled rather than guessing ownership.


CI-03 corrects the former 3.12.13-only dependency mismatch with existing Linux3.11.18 and
Mac3.12.10 CI. The five ownership-relevant POSIX methods in the official tagged sources have
identical normalized ASTs: [3.11.18](https://github.com/python/cpython/blob/v3.11.18/Lib/subprocess.py),
[3.12.10](https://github.com/python/cpython/blob/v3.12.10/Lib/subprocess.py) and
[3.12.13](https://github.com/python/cpython/blob/v3.12.13/Lib/subprocess.py).
Admission checks those pinned source fingerprints as well as the exact audited version and
unchanged live method bindings. Missing/modified stdlib source fails closed; a native bundle
must retain auditable stdlib source. This does not support arbitrary Python3.11+ patches or
certify foreign reapers. Existing CI runtimes, test selections, gates and timeouts stay intact;
the actual supported-runtime signalling/media tests must execute there, with portable Windows
unsupported-admission coverage separate. New patches require audit plus actual-runtime proof.

Phases: queued → validating → rendering → validating-output → complete/partial/failed/cancelled;
restart produces interrupted. The cycle repeats per destination before terminal commit.
A persistence failure exposes `persistence_failed` and an interrupted observation, retaining the
last durable snapshot and files. Unknown/corrupt state is preserved and rejected; no implicit
migration or deletion occurs. Initial bounds: 100 productions/root, 100 sources and attempts per
production, 1000 total sources/plans/attempts, 2000 operation results and a 1 MiB ledger. Saturation
blocks new work; no pruning/deletion is automatic. Paging is at most100 records.

Disk admission reserves source-copy bytes plus bounded output estimates (30 Mbps longform,
two10 Mbps clips, doubled for retained raw/faststart outputs), plus the larger of10% or1 GiB.
Probe timeout20s, per-process decode timeout at most1800s, per-output render timeout600s;
cancel attempts TERM only under the unreaped-leader reservation, waits2s, then attempts KILL
only if that reservation still holds, followed by bounded settling/reap. Media
bounds (dimensions, frame rate, duration, file size) precede full decode. Only MP4/MOV and
Matroska/WebM magic and fixed demuxers are admitted; no playlist or network protocol is allowed.

Presets v1 are conservative local project formats, not provider maximums or upload eligibility:

- youtube-longform-v1: full source range, dimensions rounded down to even without upscale;
  scale retains display aspect through SAR adjustment, H.264/yuv420p MP4, AAC128k, faststart.
  The candidate CI04 precision contract below chooses one bounded SAR before encoding.
  Validation requires exactly that canonical measured SAR/DAR, not an arbitrary close
  value. It does not reset non-square pixels to SAR1:1. Unrepresentable geometry rejects.
- youtube-shorts-v1 and tiktok-local-v1: manual8 seconds, 720×1280/30fps fit/pad through the
  existing Shorts renderer, AAC128k, faststart, no applied NOVA branding or watermark.

Video stores required strict positive integer sar_num/sar_den, each1..65535. SAR is measured
together with dimensions and pixel format from the SAME decoded frame (FFmpeg showinfo),
then verified constant across EVERY decoded frame; input header dimensions are not authority.
DAR is exactly width*sar_num/(height*sar_den), derived as a rational, never from width/height
alone; it is not an untrusted redundant field. Unknown, zero, out-of-bounds or malformed SAR
fails invalid_media before source admission. Even rounding compensates SAR; canonical
codec precision may introduce only the explicitly bounded projection error below.
Candidate schema1/positive-negative fixtures include anamorphic and invalid aspect cases.
Prior unaccepted ledgers without measured aspect fail strict parsing and remain read-only;
there is no implicit SAR1 assumption or data migration. Explicit fresh import is required.

CI04 candidate longform precision contract (NOT FROZEN): let W,H be the original dimensions,
R the original measured SAR, w=2*floor(W/2), h=2*floor(H/2), and intended t=(W*R/H)*(h/w).
Choose the closest positive rational q with BOTH numerator and denominator at most4096.
Use exact rational absolute error; ties prefer smaller reduced denominator, then numerator.
For every denominator1..4096 only its nearest clamped numerators need examination; this is
a bounded exhaustive optimum, not Fraction.limit_denominator alone. Exactly representable
ratios stay unchanged. Reject unless BOTH w*abs(q-t)<=1/2 and h*abs(1/q-1/t)<=1/2, in display
pixel coordinates. These symmetric projection budgets are computed BEFORE encoding.
They never authorize an arbitrary observed output, even a closer one within the budget.

The fixed scale filter explicitly sets q with setsar max4096; actual dimensions remain w,h
and measured SAR/DAR must equal that precomputed canonical value exactly. Full decode/hash,
AAC/H264/yuv420p, duration and other format checks remain. Coded H264 SPS, MP4 container and
all decoded frames must agree in real-codec evidence. Original source measurements and all
prior attempts stay unchanged; metadata records the actual canonical output, not a rewritten
source. The precision rule refines this unaccepted preset, not a frozen API or old history.

The shared cap comes from FFmpeg's [libx264 wrapper](https://github.com/FFmpeg/FFmpeg/blob/n7.0.2/libavcodec/libx264.c)
reducing SPS SAR to4096; FFmpeg7.0.2 [MOV pasp reader](https://github.com/FFmpeg/FFmpeg/blob/n7.0.2/libavformat/mov.c)
reduces to32767 while7.1 retains full precision. CI04 measured intended46144/43275 turning
into25187/23621 on Linux, separately from coded4037/3786. Canonical4037/3786 fits all these
fixed components. For721x577 SAR16:15 ->720x576, canonical DAR is20185/15144 versus intended
11536/8655; horizontal drift72/1820435 and vertical81/2910677 pixels are below1/2. Even720x576
SAR16:15 retains exact4:3; ordinary square pixels remain exact. The old Linux25187/23621 and
nearby noncanonical values reject despite being within the projection budget. Actual4:3->5:4
distortion still rejects and retains sibling clips that passed format/decode checks; inner image aspect was not proven by those older checks. Strict DTO SAR bounds1..65535 are
unchanged; the preset's representation envelope is narrower, never widened for CI.

The adapter supplies descriptor input, owned process execution and media inspection through
optional backward-compatible renderer seams. Python relocates FFmpeg's bounded MP4 moov/chunk
offsets using descriptor reads/writes because macOS descriptor reopen during FFmpeg faststart
can corrupt offsets. Full byte/hash/media/audio decode follows relocation. The helper supports
ordinary FFmpeg nonfragmented MP4 with a moov atom at most16 MiB; unsupported atom structures
fail validation. It does not claim arbitrary MP4 editing support.

Artifact inspection checks current bytes, full decode, path identity and metadata hash without
rewriting history. `validated` is local file state; `review-needed` is editorial state;
account/publication are independently `unavailable`. Nothing in this package can approve or
mark a file published. Reveal/preview require future native handle/hash admission on every use.

## Verification and rollback

```sh
python -B -m pytest tests/content_creation/test_production_artifacts*.py tests/content_creation/test_stream_shorts*.py -p no:cacheprovider
PYTHONPATH=modules/content-creation python -B -m production_artifacts.schema
# Explicit, sequential mutations in this task's isolated checkout only; never during other tests:
PYTHONPATH=modules/content-creation python -B -m production_artifacts.verify_mutations --output <fresh-owned-evidence-directory>
# Synthetic fixture only; no App walkthrough/capture claim:
PYTHONPATH=modules/content-creation python -B -m production_artifacts.fixture_run --stdio --source <synthetic-source.mp4> --sha256 <expected-hash> --output <fresh-owned-root>
make test
python -B -m ruff check modules/ scripts/
```

The fixture utility drives the fixed worker over actual stdio, retains request/result and event
correlation, probes/hashes/fully decodes each output and verifies the original hash. Its target
pins are synthetic test values, not evidence of a recorded App journey. Synthetic codec tests,
filesystem/process tests and mutation restoration do not prove native playback, audible quality,
Windows, account consent, supported upload or app integration. Exact run results belong in the PR.

Rollback disables the new worker/native mount later; retain originals, source snapshots,
ledger, manifests, attempts and successful files. Never clean output, rewrite the inbox, revoke
accounts or delete remote content as rollback.

The reaper fingerprint normalization removes documentation and only the proven known-empty
`type_params` AST schema field added in CPython3.12. Nonempty/unknown fields and executable
changes remain fingerprint differences. Schema-shape tests do not claim actual3.11 runtime
execution. Source-backed stdlib verification is an admission prerequisite, not proof of
arbitrary interpreter trust; the native launcher still owns runtime provenance/reaper policy.


## R3 candidate geometry boundary and CI05 diagnostics — NOT FROZEN

This single-geometry DTO currently admits only static, untransformed decoded media.
Both probe and full decode put `-noautorotate` BEFORE `-i`. Every frame's dimensions,
SAR and pixel format must agree; dimensions/SAR are never mixed with input-header data.
ALL displaymatrix/spherical transforms are explicitly unavailable, including valid standard
90/180/270-degree rotations, reflections and non-quarter turns. They fail `invalid_media`
before finalized-source/ledger publication. They are not normalized and orientation is not
silently discarded. The filter deletes ONLY unregistered ancillary SEI, preserving display/
spherical side data for rejection. Real track-matrix and H264 in-band orientation fixtures
verify that retained frame data under the fixed codec. Quarter-turn support needs a separate
reviewed full-transform/timeline measurement policy; angle-only logging cannot prove it.
Rendering's default autorotation agrees with the admitted no-transform static domain.
The CI04 original-DAR/even-dimension/both-component-cap/canonical-output rule is unchanged.

A bounded incremental observer consumes the ENTIRE stderr stream before its128KiB tail
can evict measurements. Pending lines are capped4096bytes; geometry is constant-space,
frame count bounded by the existing86400s*120fps envelope and decode's existing deadline.
Malformed/missing/out-of-bounds/overlong/truncated per-frame measurements, geometry/format
changes, transforms, or missing/mismatched final `-progress` frame count reject. Passthrough
frame timing prevents output sync from hiding a count mismatch. Full decode/audio success
alone is insufficient. Source admission AND artifact validation run this full-timeline check;
`full=False` is only an internal provisional probe, never finalized/artifact authority.
Parser errors use existing owned TERM/wait/witness handling; they do not signal/reap directly
or bypass the audited leader reservation, exclusion, cancellation or timeout rules.

Old candidate source/attempt records and successful/failed/orphan bytes remain immutable;
no history rewrite or implicit geometry migration. Re-import explicitly under the repaired
candidate policy. Dynamic timelines and valid rotated media are product limitations here,
not a new editor, sandbox or native Library completion claim. SAR-only changes are tested in
the parser; actual MP4/Matroska probes currently impose constant decoded SAR for the synthetic
SAR-changing bitstream, so no real demuxed SAR-only rejection proof is inferred from it.

CI05 remains unlocalized after b752/7c/d73/14fd Windows focused jobs hit15m without
Windows step logs. No phase marker or stack was observable, so neither plugin execution nor
a historical backpressure cause is inferred. The workflow's one diagnostic -p flag, exact
selection, assertions and15m limit stay unchanged; protection begins only after plugin setup.

## R4 candidate vertical image fit and diagnostic exit — NOT FROZEN

The production adapter alone replaces its fixed plain vertical graph; legacy Shorts CLI
source/behavior is unchanged. A720x1280 square-pixel canvas is NOT proof that the image inside
its padding preserved aspect. Earlier "valid siblings" meant format/decode-valid only. Retain
those old unaccepted artifacts/history read-only and re-export to a NEW attempt; do not rewrite
or silently certify their image content under this repaired candidate policy.

For ORIGINAL admitted source DAR D (not observed output or longform canonical SAR), choose
limiting width720 if D>=720/1280, otherwise limiting height1280. The other ideal dimension is
720/D or1280*D respectively. Select the closest positive even integer within the canvas;
ties choose the lower value. Reject invalid_media unless that dimension is within ONE exact
output pixel of its ideal. Fit the ENTIRE source frame, no crop; set square pixels explicitly.
Round each centered pad offset DOWN to even: x=2*floor((720-w)/4),y=2*floor((1280-h)/4).
This preserves4:2:0 chroma alignment and moves the image center at most one output pixel;
left/right or top/bottom padding may differ by two. There is no generic tolerance applied to
observed output. Constants/graph are adapter-owned, never caller filter text. Manual2..10s,
plain/no watermark/AAC/faststart/full geometry/hash checks remain; CI04 longform math unchanged.
Ordinary1280x720 SAR1 gives720x404@(0,438), even720x576 SAR16:15 gives720x540@(0,370), and
odd721x577 SAR16:15 also gives720x540@(0,370), within the declared source-based rounding bound.
Independent raw-pixel rectangle/corner tests prove shape, placement and full-source retention
for BOTH vertical destinations, separately from outer SAR/SPS/container/decode/audio evidence.

CI05 test-only logging now uses a bounded8-record nonblocking queue: at most2048 marker
attempts of512bytes, parameter-free phase text, plus one optional32KiB traceback read from
an owned temporary file. Writer/trace threads may stall or lose output; no successful output
is required for exit. Native self-exit protection is armed BEFORE logging/thread startup.
Readable stack output is best effort. Normal close requires both threads settled and native
cancellation/completion confirmed; unsettled output or cancellation failure exits nonzero,
never labels a possibly live callback disarmed. Existing pytest/faulthandler deadlines are
untouched. No process IDs/foreign handles/groups or product reaper/signal policy are used.

Only actual Windows+GITHUB_ACTIONS activates the session diagnostic. Windows support here is
restricted to x64(AMD64/x86_64),8-byte pointers; ARM64/32-bit reject diagnostic setup. The native
OS timer calls the kernel TerminateProcess entry directly with GetCurrentProcess's self
pseudo-handle, NOT a Python callback. This is an explicit x64 ABI ADAPTATION INFERENCE:
WAITORTIMERCALLBACK is VOID(PVOID,BOOLEAN), TerminateProcess is BOOL(HANDLE,UINT); these are not
documented identical/vendor-supported wrapper signatures. Under the claimed x64 register ABI,
the timer's TRUE low byte gives a nonzero exit code, not guaranteed exact1; upper bits are
unspecified. This inference requires independent Astra review and ACTUAL Windows child/CI
proof. Source arguments and local POSIX tests are not that proof. DLL/export references stay
alive; DeleteTimerQueueTimer with completion wait must succeed before cancellation is claimed.
ERROR_IO_PENDING/other failures take the explicit nonzero exit path, never free a pending
callback and continue. Creation failure exits2 before trying to log.

The300s deadline is subject to OS scheduling/termination and I/O cancellation; it is not a
hard real-time guarantee or protection before interpreter/plugin setup. Output/GIL/stdio
locks are absent from its native termination path. Local controlled-child proof uses ONLY
an otherwise-unused default, unblocked POSIX SIGALRM/empty interval timer; it preserves
foreign alarms/handlers/masks and faulthandler timers. That POSIX mechanism never activates
the plugin or changes production worker policy. Full-pipe/held-writer/GIL/closed-sink tests
observe termination BEFORE any parent stderr drain. No local Windows/ABI acceptance follows.
Parent owns actual next-head Windows outcome/log retrieval. A missing trace still leaves a
runner/startup evidence gap, and a diagnostic deadline is FAILURE, never pass or API freeze.

Windows child tests retain the full unsigned32-bit return code and emit a bounded
ORCH04_NATIVE_CHILD_RESULT record on actual Windows+Actions even when pytest succeeds.
The candidate comparison requires lowbyte1 (the timer TRUE assumption), rejects setup
refusal2/control97 and ambiguous NT failure-severity0xCxxxxxxx values, and keeps all upper
bits for review; it never accepts arbitrary nonzero/native-crash results. This additional
fail-closed test criterion is not a guarantee about unspecified upper register bits.
Observed full codes, selected-test execution and independent ABI review are still required.

Primary sources: [timer callback](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/legacy/ms687066(v=vs.85)),
[x64 ABI](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention?view=msvc-170),
[self process handle](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getcurrentprocess),
[termination](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess),
[timer creation](https://learn.microsoft.com/en-us/windows/win32/api/threadpoollegacyapiset/nf-threadpoollegacyapiset-createtimerqueuetimer),
[cancellation/completion](https://learn.microsoft.com/en-us/windows/win32/api/threadpoollegacyapiset/nf-threadpoollegacyapiset-deletetimerqueuetimer).
