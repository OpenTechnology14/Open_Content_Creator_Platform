# Proposal: Stream recording handoff and profile workspaces

**Queue row:** `P-065`  
**Agent model / effort:** `gpt-6-astra` / `xhigh` — Cross-app recording ownership, persistence and account routing
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** `Code complete — external acceptance open` — state is authoritative in [`../PROPOSALS.md`](../PROPOSALS.md)  
**Owner:** OpenTechnology14 + agent  
**Date:** 2026-09-20  
**Roadmap layers:** Creator Experience, Content Creation, Social Management  
**Evidence level:** Offline contracts, native macOS UI, and packaged-app builds verified; real OBS/provider/Windows acceptance remains open

## Outcome

A live session started inside Stream Extend records locally through OBS and, when stopped, places
the finalized non-empty media file in a shared recording inbox. Creator Extend reads that inbox
immediately, assigns each recording to a content profile, lets the operator reveal or archive it,
and can add an existing recording manually. Media stays at its original local path; registration
does not duplicate it, upload it, or require Stream Extend and Creator Extend to be open together.

Both apps also expose a compact active-profile switcher. The detailed Social view remembers the
selected brand, provider, capability, and connected account separately for every profile. Switching
back to a profile restores its last routing rather than resetting the operator to the first account.

## Boundaries

- Stream Extend starts recording before it starts streaming. If streaming fails, it rolls back the
  recording it started. It never stops a recording that was already owned by OBS or another tool.
- Only a recording started by the in-app live-session control is finalized automatically. A stream
  started directly in OBS is not claimed by Stream Extend.
- The shared inbox stores private local metadata and a canonical file path, protected by atomic
  writes and a cross-process lock. It does not copy video into the repository or cloud storage.
- Creator Extend recording state is workflow metadata (`ready`, `editing`, `archived`), not proof
  that editing or publishing completed.
- Social credentials remain in the operating-system credential manager. Active profile/account
  routing contains connection IDs and public account labels only.
- Uploads, posts, and live destinations keep the P-062 human-approval boundary.

## Implementation map

| Area | Change |
|---|---|
| `apps/shared/recording-library` | Shared atomic recording inbox, deduplication, state updates, reveal action, tests |
| Stream Extend OBS client | Start/stop an owned stream+recording session with rollback and finalized-path result |
| Stream Extend UI | Use the owned live-session commands and report Creator Extend handoff |
| Creator Extend UI | Recording inbox with refresh/import/profile assignment/reveal/status/archive controls |
| Shared Social Manager | Durable active workspace and per-profile routing preferences |
| Shared UI | Compact profile switcher plus connected-account selection in Social Management |
| Content Creation docs/tests | Replace the documented missing recording ingress with the implemented local contract |

## Verification

- Shared Rust unit tests prove atomic inbox round trips, canonical-path deduplication, profile/status
  updates, missing-file reporting, active workspace persistence, per-profile preference restoration,
  and catalog validation.
- The fake OBS WebSocket contract proves recording starts before streaming, stop returns the real
  path, and an already-active recording is not claimed or stopped.
- Both complete Rust app suites and both Svelte check/build commands pass.
- Focused Python/docs contracts, `make test`, Ruff, and `git diff --check` pass.
- Native OBS picture/audio acceptance and Windows UI acceptance remain external evidence.

## Acceptance limits

The code cannot honestly prove capture-device quality, real OBS encoder output, OS-specific reveal
behavior, provider credentials, or an external post without native/manual runs. Those remain open
even when all offline tests pass.
