# Social Management

**Labels:** `Content` `Stream` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (partial)

Shared `Content` + `Stream` profile, brand, social-account, and publication control. It gives the
desktop apps and future mobile companion one versioned catalog for profile/brand/platform dropdowns.

**Start here:** [set up your accounts, password management and agent access](setup/accounts.md).
It covers all fifteen providers, including pending adapters, with a
[blank private readiness checklist](setup/account-readiness.template.md) and repeat sign-in steps.

The committed starter identities are Main Stream, Main Content, OpenTechMarketing, Video Review,
and Agent Game Labs. Their brand choices include the Open Content Creator Platform, Stream Extend,
Creator Extend, and OpenTechApp logos. Edit [`catalog.yaml`](catalog.yaml) to add identities; do not
put account IDs, client secrets, access tokens, or stream keys in that file.

Create a private local profile without changing Git, then restart the picker:

```bash
PYTHONPATH=. .venv/bin/python -m social_management profile-add \
  --id minecraft-tutorials --name "Minecraft Tutorials" --kind hybrid \
  --brand stream-extend --brand creator-extend --default-brand stream-extend \
  --destination youtube=live-stream,post-video
```

Local profiles are stored in `~/.hybrid-creator-platform/social/profiles.json`. A custom profile
may select committed brands and provider capabilities but cannot replace a starter profile.

## What works

- Shared native Social tab in Stream Extend and Creator Extend, plus the standalone local picker
- An always-visible active-profile switcher in both apps, with separate Stream and Content workspaces
- Per-profile remembered brand, platform, capability, and connected-account routing; switching away
  and back restores the last route for that profile
- Multiple verified accounts for the same profile/provider, selectable by account name, with
  reconnect and confirmation-gated disconnect controls in the native Social tab
- Validated private profile create/update/remove commands layered over the starter dropdown
- OAuth authorization-code flow, ten-minute state, and PKCE where supported
- OS credential-manager token storage, automatic token refresh, disconnect, and a redacted public ledger
- YouTube, Twitch, X, and Discord account/channel verification contracts
- Approval-gated YouTube video upload/live setup, Twitch stream-key handoff, X text posting, and
  Discord announcement posting through an OAuth-created incoming webhook
- Registration-visible catalog entries for TikTok, Instagram, Facebook, and LinkedIn
- Extensible planned entries for Bluesky, Mastodon, Kick, Rumble, Trovo, DLive, and Restream

Provider developer registration, scopes, quotas, channel eligibility, and app review still apply.
A visible provider name does not mean its adapter or developer account is ready; the dropdown shows
`available`, `registration-required`, or `planned` for that reason.
Trovo's existing planned entry is stale for live onboarding: its live service ended June 30, 2026.
See the [recovery-only instructions and official notice](setup/accounts.md#trovo--live-service-retired-existing-account-recovery-only).

Discord is a content destination in this module. Discord Go Live is a manual screen-share action in
the Discord desktop client, so the catalog does not present it as an OBS ingest destination.

Active workspace state contains only catalog IDs and a redacted connection ID. It is shared locally
between the two desktop apps so a Stream recording can retain its source identity and enter Creator
Extend already assigned to the current Content profile. Tokens never enter that workspace file.

## Quick local check

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/python -m social_management profiles
PYTHONPATH=. .venv/bin/python -m social_management serve
```

On Windows, use `.venv\Scripts\python.exe` and set `PYTHONPATH=.` for the command. The picker binds
only to `127.0.0.1`; low-latency OBS and media processing remain local. Provider APIs are used for
authorization and the approved remote action only.

After connecting, create a reviewable job and execute it with the exact ID printed by `plan`:

```bash
PYTHONPATH=. .venv/bin/python -m social_management plan \
  --connection <connection-id> --capability post-text --brand opentechapp \
  --text "Reviewed post text" --approve --output /tmp/social-job.json
PYTHONPATH=. .venv/bin/python -m social_management publish \
  /tmp/social-job.json --confirm <job-id>
```

Use `post-video` with `--media`, or `live-stream` to receive an ephemeral ingest destination. The
publish command prints a live destination only to the current terminal; do not save or paste it
into issue logs.

## Channel portfolio and concept approvals

P-062's [editorial controls and AgentWorkflows adapter](setup/editorial.md) add separate
OpenTechnology walkthrough, AI content and gaming channel definitions, a private local
concept queue, revision-bound owner decisions, production briefs and sanitized reports.
They run through `python -m social_management portfolio`; concept approval retains the
existing final publishing gate. These controls do not create accounts or launch production.

## Module boundaries

Automation Control schedules shows and hands live destinations to OBS. Content Creation produces
videos and Shorts. Marketing Crosswalk produces source marketing material. This module owns the
identity/account/capability map and the final external-action gate; it does not generate content or
control a game.

See [`setup/manual.md`](setup/manual.md) for provider registration and live acceptance, and
[`setup/automated.md`](setup/automated.md) for repeatable local checks.
