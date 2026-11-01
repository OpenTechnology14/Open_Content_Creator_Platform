# Private account readiness — blank template

Copy this file into a private note outside every Git checkout before filling it in.
Follow [the account setup guide](accounts.md) in the repository; that relative link may need
replacing with a bookmark after copying. This committed template contains no actual results.

Use labels only. Store passwords, recovery codes, emails, phone numbers, remote account IDs,
OAuth secrets, webhook URLs and stream keys in your vault, not here. Even non-secret account
labels and status can be private business information; do not publish the filled note.

Owner/operator label: _not recorded_  
Last updated / device: _not recorded_  
Private vault item naming convention (no share link): _not recorded_

## Foundation

- [ ] Password manager chosen, owner can unlock it, manager recovery accessible independently
- [ ] Owner/recovery mailbox secured; backup factor available
- [ ] Actual password/SSO/passkey method saved for each used account
- [ ] Agent tool/browser scope checked; owner will enter all credentials and consent
- [ ] GitHub/AgentWorkflows and authorized Blog/marketing sources accessible for the intended task

## Provider checks

Replace `not checked` only with an observed result, date and device. Use `not needed yet`,
`pending`, `not offered` or `failed: <redacted reason>` when appropriate. An implemented
adapter is not proof that an account is connected. Repeat rows for extra identities.

| Provider / destination label | Account exists | Vault / recovery / MFA | Fresh sign-in date + device | Developer ready | App connection / action test |
|---|---|---|---|---|---|
| YouTube / OpenTechnology | not checked | not checked | not checked | not checked | not checked |
| YouTube / AI Content | not checked | not checked | not checked | not checked | not checked |
| YouTube / Gaming | not checked | not checked | not checked | not checked | not checked |
| Twitch | not checked | not checked | not checked | not checked | not checked |
| X | not checked | not checked | not checked | not checked | not checked |
| Discord | not checked | not checked | not checked | not checked | not checked |
| TikTok | not checked | not checked | not checked | not checked | adapter pending |
| Instagram | not checked | not checked | not checked | not checked | adapter pending |
| Facebook | not checked | not checked | not checked | not checked | adapter pending |
| LinkedIn | not checked | not checked | not checked | not checked | adapter pending |
| Bluesky | not checked | not checked | not checked | deferred | adapter pending |
| Mastodon | not checked | not checked | not checked | deferred | adapter pending |
| Kick | not checked | not checked | not checked | deferred | adapter pending |
| Rumble | not checked | not checked | not checked | deferred | adapter pending |
| Trovo (existing account only) | not checked | not checked | not checked | live service retired | live service retired |
| DLive | not checked | not checked | not checked | deferred | adapter pending |
| Restream | not checked | not checked | not checked | deferred | repository adapter pending |

## Per-account handoff (repeat as needed)

- Platform / destination label:
- App profile / intended purpose:
- Vault item label only:
- Sign-in method (password, passkey, named SSO provider):
- Owner/control verified and backup factor available (yes/no/limitation):
- Most recent sign-out/sign-in result, date and device:
- Developer application/consent requirement (non-secret status only):
- Adapter availability checked on:
- Connection identity matched and restart/read-back result:
- Approved action test, privacy/audience, date and result (or not run):
- Current blocker / next step / who performs it:
- Access revocation location checked (provider, app, browser, assistant tools):

## Return-session checklist

- [ ] Owner fresh sign-in succeeds with the saved method and intended identity
- [ ] Current adapter and developer requirements rechecked
- [ ] Supported connection renewed if needed; exact profile/account read back
- [ ] App restart/read-back passed; cached metadata not treated as live token health
- [ ] YouTube portfolio binding checked after any connection replacement
- [ ] Concept approval and final publication approval remain separate
- [ ] Private report updated with observed results only; no credentials included

Next bounded task: _not recorded_  
External upload/post/live test authorized: _not recorded; no test permission implied_
