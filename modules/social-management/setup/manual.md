# Social Management — manual setup and acceptance

Start with [user account setup](accounts.md) for all fifteen providers, password management,
MFA/recovery, agent access and repeat sign-in tests. Its
[private checklist template](account-readiness.template.md) includes unsupported platforms.
Account readiness is separate from adapter and live-action acceptance below.

## 1. Register only the providers you need

Create a developer application and add `http://127.0.0.1:8765/oauth/callback` as its exact redirect
URI. The root `.env.example` documents the variable names. Supply the issued values privately to
the process launching the standalone service or desktop app; the OAuth code reads process
environment and does not itself load `.env`. A Finder-launched app may not inherit shell values.
See [developer setup and secret injection](accounts.md#5-register-and-connect-the-four-implemented-adapters):

- YouTube: `SOCIAL_YOUTUBE_CLIENT_ID` and `SOCIAL_YOUTUBE_CLIENT_SECRET`; enable YouTube Data API
  v3, which includes the live resources. Confirm the selected channel is eligible to go live.
- Twitch: `SOCIAL_TWITCH_CLIENT_ID` and `SOCIAL_TWITCH_CLIENT_SECRET`.
- X: `SOCIAL_X_CLIENT_ID`. Configure OAuth 2.0 authorization-code with PKCE and read/write access.
- Discord: `SOCIAL_DISCORD_CLIENT_ID` and `SOCIAL_DISCORD_CLIENT_SECRET`. Enable the
  `webhook.incoming` OAuth scope; the consent flow lets the account owner choose one announcement
  channel. Discord Go Live remains a manual Discord desktop screen-share workflow.

TikTok, Instagram, Facebook, and LinkedIn need implementation and provider registration/access
before this repository can claim a working connection. Bluesky, Mastodon, Kick, Rumble, DLive,
and Restream have planned adapters. Trovo remains in the catalog but its live service has retired;
follow the account guide's recovery-only instructions. Catalog scopes and links are proposed
integration inputs, not proof of current provider eligibility.

## 2. Choose the profile and account

For separate walkthrough, AI content and gaming queues and their AgentWorkflows controls,
see the [editorial portfolio guide](editorial.md). Bind its logical channels only after the
account connection below; concept review remains usable before accounts are connected.

Install the module as shown in [`automated.md`](automated.md), load the exported environment values,
then run:

```bash
cd modules/social-management
PYTHONPATH=. .venv/bin/python -m social_management serve
```

In Stream Extend or Creator Extend, select **Social** instead. The apps render the same committed
catalog and logos and start the loopback service from the module environment installed by **Module
setup**. OAuth consent opens in the system browser.

Use the always-visible profile switcher for routine identity changes. In **Social**, choose the
profile, brand, platform, purpose, and active connected account. Each profile remembers this route,
so switch to another profile and back and confirm the earlier account selection returns. Confirm the
provider consent page names the expected application and scopes. After return, refresh accounts,
select the intended account, and confirm the posting route names it. The
token-free metadata ledger is `~/.hybrid-creator-platform/social/connections.json`; inspect it locally and confirm it has
no access token, refresh token, authorization code, client secret, stream key, or upload URL.
Its account IDs/names are still private; do not publish the whole file.

Use **Disconnect &lt;account&gt;** only after checking the profile and account name in the confirmation.
It removes both the local connection record and the OS credential entry. Reconnect starts a fresh
provider consent flow; it does not silently reuse a token. Remote provider grants, Discord webhooks,
browser sessions and assistant tool access have separate [revocation steps](accounts.md#7-return-later-reconnect-and-revoke-access).

Use `profile-add` from the module README for another Stream, Content, or hybrid identity. Restart
the picker and confirm the new identity appears. Before `profile-remove`, disconnect every account
bound to it; the CLI refuses to orphan those connections.

## Verification

Run the automated checks before using real accounts.

**Automated — run these:**

- `python3 -m pytest -q tests/social_management`
- `python3 -m ruff check modules/social-management tests/social_management`
- `make test`

**Manual — nothing automates these:**

- [ ] Open the picker on the MacBook display and confirm every profile/logo/provider state.
- [ ] Switch across every Stream/hybrid and Content/hybrid profile from the app headers; switch back
  and confirm its brand, provider, capability, and selected account route were restored.
- [ ] Connect two disposable accounts to one profile/provider, select each by name, restart both
  apps, and confirm the selected redacted connection is shared without exposing a token.
- [ ] Connect a disposable/test account for each enabled adapter and reject one consent flow.
- [ ] Re-run one expired callback and confirm it fails without changing the existing connection.
- [ ] Build an unapproved job and confirm the provider receives no request.
- [ ] Approve an X text job, enter its exact job ID, and confirm one post appears on the selected account.
- [ ] Connect a disposable Discord channel, approve one text job, and confirm the webhook message
  appears without expanding user-provided mentions.
- [ ] Upload a short private YouTube test video and confirm its ID belongs to the selected channel.
- [ ] For an explicitly approved live test, prepare a private YouTube broadcast and check its
  visibility before sending color bars from OBS. Treat Twitch as potentially public: use local
  recording until the owner authorizes the exact external test and its audience. Stop after the
  bounded test and verify no key appears in logs or saved JSON.
- [ ] Repeat connection and private-action checks on Windows Credential Manager.
- [ ] Revoke each test connection at the provider and run `disconnect --confirm <connection-id>`.
- [ ] Disconnect one disposable account in the native Social tab and confirm both its public ledger
  row and operating-system credential entry are gone while the other account remains.

### Last step — full feature test run

Run the [Social Management section](../../../tests/ACCEPTANCE-CHECKLIST.md#social-management--social-management)
of the platform acceptance checklist end to end.

Record platform, account label, OS, date, result, and remote test ID in the P-062/P-065 proposal rows. Do
not mark the module implemented until these live actions pass on both macOS and Windows.
