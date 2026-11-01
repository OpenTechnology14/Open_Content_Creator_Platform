# Set up your social accounts and access

Prepare your accounts now, including platforms whose app integrations are still pending.
Start with the password manager and the three YouTube destinations, then work through
the other platforms you intend to use. An unused platform can stay **not needed yet**.
This guide creates no accounts and grants no access by itself.

**Reviewed:** 2026-11-01 against the repository's [catalog](../catalog.yaml), OAuth/vault
implementation and the official sources linked below. Provider screens and eligibility
can change; record a blocker if the current screen differs. No real account has been tested
as part of writing this guide.

## 1. Choose the identities

Keep the owner login separate from the public channel identity. One owner may manage
several channels; each destination still needs its own confirmed channel identity.

| Destination | What belongs here | App profile / logical channel |
|---|---|---|
| OpenTechnology | Walkthroughs for all eligible projects, organized with playlists | OpenTechMarketing / `opentechnology` |
| AI Content Studio (working name) | Original content from approved concepts, including Blog-inspired ideas | Main Content / `ai-content` |
| Gaming (working name) | Gaming shows and highlights | Main Stream / `gaming` |

Choose the public names and available handles during setup; the working names above do not
reserve them. Start with one gaming destination and repeat the checklist for each additional
channel you choose. Use an existing account you own when appropriate. Do not create a new
personal identity for every project where a provider supports Pages/channels under one owner.

The [portfolio guide](editorial.md) explains routing. Its binding controls currently target
YouTube only; other platforms use the existing Social profile/account picker when supported.
Do not bind the same remote YouTube channel to the walkthrough, AI and gaming rows.

## 2. Set up password management and recovery first

1. **Keep your existing password manager** if you already use one. Otherwise choose one
   and install its official desktop/mobile app and browser extension. Official starting
   guides: [Bitwarden](https://bitwarden.com/help/getting-started-browserext/) or
   [1Password](https://support.1password.com/explore/get-started/). There is no required
   password-manager product or vault connector in this project.
2. Use a unique master passphrase, enable the manager's available MFA, and save its recovery
   instructions/material somewhere you can reach without unlocking that same vault, such
   as a physically secured recovery sheet. Confirm you can unlock it on your recovery device.
   Follow the manager's own recovery procedure; do not assume support can recover a forgotten
   master password. See [Bitwarden recovery limits](https://bitwarden.com/help/product-faqs/)
   and [1Password recovery codes](https://support.1password.com/recovery-codes/).
3. Secure the **owner email account** first: unique password or passkey, available MFA, current
   recovery method and a backup factor. This mailbox controls most account resets. Avoid
   making the mailbox and vault depend exclusively on each other for recovery.
4. Create a vault folder/tag such as **OpenTechnology / Social**. For each login, save its
   official URL, actual sign-in method, owner email/username, generated unique password if
   applicable, and recovery details. If you use **Continue with Google/Apple/etc.**, record
   that provider; do not assume the site has a separate password.
5. Enable a passkey/security key or authenticator where offered. Complete the site's required
   verification and keep a backup factor or recovery codes. If a site offers only SMS, record
   that limitation and keep the recovery number current. If no additional factor is offered,
   record **not offered**, not **MFA passed**. Keep recovery codes private; never paste them
   into chat or reporting.
6. Create separate vault items for **developer application credentials**. Label by provider
   and test/production use. Keep OAuth client secrets, webhook URLs and stream keys out of
   account-readiness notes. Do not export an unencrypted vault into a project folder.

Use labels such as `Social / YouTube / Owner` and `Developer / YouTube / Local test`.
Your private vault can hold channel IDs, recovery email addresses and ownership records.
The agent only needs a non-secret account label and the result of a check.

## 3. Keep a private readiness checklist



Copy [the blank checklist](account-readiness.template.md) into a private note outside Git.
It includes every catalog provider and separate rows for the three YouTube destinations.
Never commit the filled copy. Use these states independently:

| State | Evidence you record |
|---|---|
| Account exists | You can identify the intended account/channel in its own website |
| Secured | Vault item saved; recovery and offered MFA checked, or a limitation recorded |
| Sign-in tested | Fresh sign-in reached the intended identity, with date and device |
| Developer ready | Optional application registration, redirect and access product checked |
| App connected | Supported adapter returned the expected account and requested capability |
| Action tested | A separately authorized upload/post/live test reached its intended destination |

**Sign-in test for every active provider:** keep your existing owner session/recovery device
available. Open a separate browser profile or private window, visit the official site, and
sign in yourself using the saved method. Complete MFA, open the intended channel/Page/server,
then sign out of that test window and repeat. Record the result without credentials or
screenshots of security codes. This checks repeatability without ending every existing session.
For a shared Google owner, test channel switching into each of the three YouTube channels.

An account can be **sign-in tested / adapter pending**. Developer approval, an installed app,
and a successful browser login are each insufficient evidence of a working app connection.

## 4. Prepare each platform

Repository states below describe code availability, not your account's readiness. Even the
four implemented adapters still require real provider and OS-vault acceptance.

### YouTube — implemented adapter; account acceptance pending

1. Sign in to [YouTube](https://www.youtube.com/) with the secured Google owner. Create or
   select the OpenTechnology channel. Use the channel creation/business-name path for
   additional AI-content and gaming channels; check the selected identity before each change.
   See Google's [channel creation instructions](https://support.google.com/youtube/answer/1646861).
2. Set the chosen name, handle and description. Record each channel's identity privately,
   along with which owner login controls it. Put project walkthroughs in playlists within
   OpenTechnology rather than creating one channel for every project.
3. If a human teammate needs access, use the appropriate
   [YouTube Studio permission role](https://support.google.com/youtube/answer/9481328) instead
   of sharing the Google password. A teammate role does not by itself prove our OAuth flow
   can act on that channel; verify the returned channel during connection.
4. Perform the common sign-in test for all three channels. Check upload/live eligibility in
   Studio if you intend to use it, but do not start a broadcast as a login test.
5. For app connection, complete the developer setup in section 5. Later, the first approved
   upload test should use a short synthetic clip with **Private** visibility and a checked
   destination. Concept approval and final publication approval remain separate.

### Twitch — implemented adapter; account acceptance pending

1. At [Twitch](https://www.twitch.tv/), create/select the gaming owner account, verify its email,
   and confirm the intended channel name. Repeat only for additional distinct channels needed.
2. Enable [Twitch 2FA](https://help.twitch.tv/s/article/two-factor-authentication?language=en_US).
   Follow its phone verification/authenticator steps and save recovery information privately.
3. Sign out/in through the common test and open Creator Dashboard. Do not copy the stream key
   into notes. Developer registration requires a verified email and 2FA; see section 5.
4. Treat broadcasting as potentially public. Stop before **Go Live**; a local OBS recording
   can test production without broadcasting. A private Twitch live test is not assumed here.

### X — implemented adapter; account acceptance pending

1. At [X](https://x.com/), create/select the intended brand account, verify the requested
   contact method and save its actual login method. Separate the brands only where you need
   distinct feeds; do not assume the YouTube channel structure creates X accounts.
2. In security settings, enable an authenticator or security key and save recovery material.
   See [X's 2FA instructions](https://help.x.com/en/managing-your-account/two-factor-authentication).
3. Run the common sign-in test and check the handle. Developer/API access is a separate step;
   review current access requirements in the portal without purchasing access as part of this checklist.
4. Use section 5 when connecting. Do not send a test post during login preparation; an app
   connection does not make posts private. Later remove grants through
   [Apps and sessions](https://help.x.com/en/managing-your-account/connect-or-revoke-access-to-third-party-apps).

### Discord — implemented announcement adapter; account acceptance pending

1. Create/select your owner at [Discord](https://discord.com/), verify email, and configure
   [passkeys/security keys or MFA](https://support.discord.com/hc/en-us/articles/25966860846231-Security-Keys-Passkeys-and-Passwordless-Login-on-Discord).
2. Select or create the intended project/community server. Prepare a test text channel whose
   viewing permission is limited to the people testing. Confirm you can manage the intended
   webhook destination; do not give unrelated people server-wide administrator access.
3. Run the sign-in test, checking both server and channel. Prepare a developer application
   only when ready for section 5.
4. Our connection uses OAuth `webhook.incoming`; it is not a user token, bot token or automated
   personal account. Choose the test channel during consent. A webhook URL is a secret.
   Discord Go Live remains a manual desktop screen-share feature, outside this adapter.

### TikTok — registration-required catalog entry; adapter pending

1. Create/select the intended account at [TikTok](https://www.tiktok.com/). Verify the offered
   contact method, save the login method, and configure the security/recovery options shown.
2. Set the public handle/profile and run the common sign-in test. Record **adapter pending**.
3. When preparing developer access, use [TikTok for Developers](https://developers.tiktok.com/apps)
   and review Content Posting API access. Direct Post requires the appropriate product/scope
   and review; unaudited clients have private-post restrictions. Registration alone does not
   enable public posting. See [TikTok's Direct Post setup](https://developers.tiktok.com/docs/en/content-posting-api-get-started).
4. Keep any app credentials in the vault for future implementation; there is no working
   TikTok connect button to unlock by adding credentials today.

### Instagram — registration-required catalog entry; adapter pending

1. Create/select the brand account at [Instagram](https://www.instagram.com/), confirm email,
   save its login method and enable the security/recovery options in Accounts Center.
2. For future publishing integration, inspect the professional account options and choose
   Creator or Business to fit the actual account. Check the visibility implications before
   converting an existing personal account. Run the common sign-in test.
3. Record the chosen account type and any connected Facebook Page privately. Meta has
   [Instagram Login](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/)
   and [Facebook Login](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/)
   integration routes. The future implementation must pick and verify its route and requirements
   before you link assets or request scopes solely for it.
4. These Meta documentation pages were rate-limited during this review. Treat route-specific
   requirements as **needs current portal check**. The catalog's proposed scopes are not an
   implemented integration or a guarantee of Meta approval.

### Facebook — registration-required catalog entry; adapter pending

1. At [Facebook](https://www.facebook.com/), sign in with your legitimate owner profile and
   use Pages to create/select the brand Page. Use Page access for collaborators rather than
   sharing the personal profile's password. Confirm current instructions in the
   [Facebook Help Center](https://www.facebook.com/help/).
2. Secure the owner login in Accounts Center, record which Page you control, and perform the
   common test by switching into that Page after fresh sign-in.
3. If preparing developer access, use [Meta for Developers](https://developers.facebook.com/apps),
   record the relevant owned assets, and check current Page permissions and review requirements.
   Leave unavailable verification/review steps marked pending; no paid setup is required here.
4. The repository has no working Facebook connection yet. Keep registration details private
   and defer token generation and publishing tests until the adapter exists.

### LinkedIn — registration-required catalog entry; adapter pending

1. Use your real professional owner account at [LinkedIn](https://www.linkedin.com/). If you
   need an organization presence, create/select its Page and confirm your admin access. See
   [LinkedIn Page creation](https://www.linkedin.com/help/linkedin/answer/a544879).
2. Save the login method, enable offered two-step verification and recovery, then test fresh
   sign-in and access to the intended member profile and/or Page.
3. Prepare an app in [LinkedIn Developers](https://www.linkedin.com/developers/apps) only as
   needed. Record whether future posts target a member or organization; those are different
   access requirements. Sign-in access alone does not grant organization publishing. See
   [LinkedIn's developer quick start](https://learn.microsoft.com/en-us/linkedin/marketing/quick-start).
4. Mark publishing and repository connection **adapter/access pending**. The proposed
   `w_member_social` scope is not evidence of Page publishing support.

### Bluesky — planned adapter

1. Create/select your account using [Bluesky](https://bsky.app/). Verify email, save the actual
   sign-in method and handle, and inspect the security/recovery options currently offered.
2. If using a custom handle, record its domain ownership privately; a custom domain is optional.
   Run the common sign-in test and confirm the handle.
3. Mark **adapter pending**. Do not create an app password just to fill the checklist; future
   integration must choose a supported authorization method using
   [Bluesky's developer documentation](https://docs.bsky.app/).

### Mastodon — planned adapter

1. Choose a server whose rules and registration policy suit the project, then register there.
   Mastodon is not one shared login website. Record the server URL and full `@name@server`
   identity; see [Mastodon signup](https://docs.joinmastodon.org/user/signup/).
2. Verify email, enable available 2FA and save recovery material. Check the server's account
   settings and authorized-app controls; see [account preferences](https://docs.joinmastodon.org/user/contacts/).
3. Run the common test on that exact server. Leave app registration/token generation pending
   until the repository's Mastodon adapter exists; do not paste a personal token into config.

### Kick — planned adapter

1. Create/select the gaming identity at [Kick](https://kick.com/), verify email and save its login.
2. Enable an authenticator in security settings using
   [Kick's 2FA guide](https://help.kick.com/en/articles/7120898-how-to-enable-two-factor-authentication).
   Save recovery material and run the common sign-in test.
3. Confirm access to the creator dashboard, leaving stream keys private and broadcasting off.
   Record any eligibility blocker. Developer preparation can be reviewed at
   [Kick Developers](https://docs.kick.com/); the repository adapter remains pending.

### Rumble — planned adapter

1. Create/select your owner at [Rumble](https://rumble.com/), confirm email and select the intended
   channel. Inspect offered security/recovery options and save them.
2. Check [account verification](https://rumble.support/en/help/account-verification) if uploading
   or streaming is intended. Rumble's guide limits a phone number to one verified account;
   inspect channel-management options before creating multiple owner accounts.
3. Complete the common test and inspect [Rumble Studio](https://studio.rumble.com/) access if
   needed. Record verification/eligibility blockers and **adapter pending**. Do not initiate
   a broadcast or disclose the ingest key as a readiness test.

### Trovo — live service retired; existing-account recovery only

Trovo ended live streaming on **June 30, 2026** and suspended new-streamer onboarding earlier.
Its notice says account and gaming data are retained.
See [Trovo's official announcement](https://support.trovo.live/category/8/article/2394).

1. Do not create a new account for live streaming or spend time registering a live adapter.
2. If you already have an account, retain its vault/recovery record and check existing account
   access through the official site/support as needed. Do not assume old VODs remain available.
3. Mark **live service retired**. The repository still has a `planned` Trovo catalog entry;
   that stale entry is not an available streaming destination. Catalog retirement is a
   separate runtime follow-up, not completed by this guide.

### DLive — planned adapter

1. At [DLive](https://dlive.tv/), use the offered email or supported social sign-in flow. Save
   which method you actually chose; secure the upstream login if using social sign-in.
2. Verify the requested contact details, inspect offered security/recovery controls and
   record any missing MFA option. DLive's [account guidance in its terms](https://community.dlive.tv/about/terms-of-service/)
   distinguishes email/social accounts and recommends 2FA when available.
3. Perform the common test and check access to the intended channel/dashboard without going
   live. Mark **adapter pending**; no wallet or payout onboarding is needed for this sign-in check.

### Restream — planned repository adapter

1. Create/select your owner at [Restream](https://restream.io/) and save the actual login method.
   Its [sign-in guide](https://support.restream.io/en/articles/9335654-log-in-and-out-of-your-account)
   distinguishes Google sign-in from an email/password login.
2. Configure [Restream 2FA](https://support.restream.io/en/articles/870429-how-to-enable-two-factor-authentication)
   where available for that method and save recovery material. Secure the upstream Google
   identity as well when using it. Perform the common test.
3. Open the destination/channel settings to understand which identity would be used. Adding
   a destination grants Restream access to that provider; do that separately when you intend
   to use it, checking each consent. It does not connect Restream to this repository.
4. Leave streaming off and mark **repository adapter pending**. No paid plan is needed just
   to record account readiness; assess plan requirements when choosing actual destinations.

## 5. Register and connect the four implemented adapters

Skip this section for unsupported providers. Account preparation above is still useful.
Use the [module installation steps](automated.md) and [manual acceptance guide](manual.md)
before real-account testing. Developer registration and quota/review requirements can still
block an implemented adapter.

The native local service currently uses this exact redirect URI:

```text
http://127.0.0.1:8765/oauth/callback
```

| Provider | Developer setup for this implementation | Environment variable names |
|---|---|---|
| YouTube | In [Google Cloud](https://console.cloud.google.com/apis/credentials), select an owned project, enable YouTube Data API v3, configure the consent audience/test users, then create a Web application OAuth client with the redirect above. This local service uses a client secret; keep it owner-managed, never bundle it for distribution. | `SOCIAL_YOUTUBE_CLIENT_ID`, `SOCIAL_YOUTUBE_CLIENT_SECRET` |
| Twitch | [Register an application](https://dev.twitch.tv/docs/authentication/register-app/) with verified email/2FA, the callback above and a fitting category; use the confidential authorization-code configuration with its client secret. | `SOCIAL_TWITCH_CLIENT_ID`, `SOCIAL_TWITCH_CLIENT_SECRET` |
| X | In the [developer portal](https://developer.x.com/en/portal/dashboard), enable OAuth 2.0, configure a Native/public client with PKCE, the exact callback and the required read/write access. This adapter does not use a confidential-client secret. | `SOCIAL_X_CLIENT_ID` |
| Discord | In [Developer Applications](https://discord.com/developers/applications), create/select the app, register the OAuth2 redirect and retain its client ID/secret. Follow the [OAuth2 registration instructions](https://docs.discord.com/developers/topics/oauth2). The connect flow requests `identify` and, for announcements, `webhook.incoming`. Do not substitute a bot token. | `SOCIAL_DISCORD_CLIENT_ID`, `SOCIAL_DISCORD_CLIENT_SECRET` |

Google's [web OAuth instructions](https://developers.google.com/identity/protocols/oauth2/web-server)
permit local testing redirects; YouTube live resources use
[YouTube Data API v3](https://developers.google.com/youtube/data/live/getting-started).
X documents [public clients and PKCE](https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code).
If a provider rejects the configuration, record that blocker; do not invent a public callback,
weaken TLS elsewhere or change client types just to make the form submit.

1. Save client credentials in your vault. Supply the named values to **the process launching
   the local service/app**, preferably with your password manager's supported environment
   injection or a private local launcher. Follow that product's instructions; there is no
   implemented vault integration here. Do not type literal secrets into shell history.
2. The root `.env.example` lists the variable names. Saving values to `.env` alone is not
   sufficient: this OAuth code reads process environment and does not itself load that file.
   A desktop app launched from Finder may not inherit a terminal's variables. Stop and fix
   the launch environment if credentials are reported missing; report variable names only.
3. Confirm the installed Python keyring backend is the expected macOS Keychain or Windows
   credential backend before consent. The app stores tokens under `HybridCreatorPlatform.social`.
   Inspect the backend name/presence, not stored secret values; stop on an unexpected/plaintext
   backend. Real persistence and Windows acceptance still need testing.
4. Open **Social**, choose profile, brand, provider and purpose, then **Connect**. You complete
   login/MFA and consent in the browser. Check the official provider hostname, application name,
   account/channel and requested scope. Cancel if any are wrong. Never share a callback URL
   containing a code or copy a token into the app manually.
5. Start with account-read when available. Upload/post/live capabilities request additional
   scopes and may require new consent. YouTube distinguishes read, upload and broad live scopes;
   Twitch live access requests stream-key permission; X posting includes write/offline access;
   Discord posting creates a channel-specific webhook. Grant the purpose you actually intend
   to test; an account-read connection alone cannot prove publishing readiness.
6. A successful fresh OAuth callback performs the provider identity check. Back in Social,
   refresh and check that returned account and selected route. Restart the app, refresh again
   and confirm the record persists. The refresh/list controls read cached metadata; they are
   not a token-health test. Record initial connection and restart checks separately, leaving
   ongoing token/vault acceptance pending until its actual test passes. For YouTube, follow
   [Bind real accounts separately](editorial.md#bind-real-accounts-separately)
   and read back the portfolio report. Other providers do not use that YouTube-only binding command.

The application stores OAuth tokens and Discord webhook secrets through the OS credential
manager. The local `connections.json` is token-free metadata, but includes account identifiers
and names: it is **still private**. Do not attach it wholesale to public issues. Neither the
readiness tracker nor AgentWorkflows should hold passwords, cookies, tokens or stream keys.

## 6. Give the agent useful access

You remain the account owner. The assistant has no independent social identity to invite as
a human teammate. It can use tools enabled for the current session and the application's
scoped connection when that integration exists. Browser login does not automatically create
an OAuth connection or authorize an action.

| Access | How to prepare it | Owner/agent boundary |
|---|---|---|
| Setup help and status | Share the non-secret platform/brand label and current blocker; open the relevant settings page if browser tools are enabled | Agent can guide navigation and inspect non-secret status. You enter passwords/passkeys, codes, CAPTCHA and consent. |
| App account access | Complete the intended provider's supported OAuth flow yourself | Agent can operate supported controls within the authorized task. No generic vault access or raw credential sharing is required. |
| AgentWorkflows and reporting | Keep the existing GitHub repository access and installed project/reporting paths available to the coding tools | AgentWorkflows is a repository, not a social login provider. Public workflow files stay generic; filled readiness records and account details stay private. |
| Blog/marketing sources | Make the authorized repository/source material readable | Drafting concepts needs source access, not permission to publish or access all social accounts. |
| Production and publication | Review the exact concept/revision, then the finished output under the existing gate | Signing in or approving a concept does not authorize public uploads, messages or live streams. CT-D19 remains unanswered. |

Before an assisted sign-in session, choose the browser profile/workspace and the tool
permissions you intend to expose. Keep security-code and vault screens under your control.
Local agents with **Full access** can access files and the network broadly; a saved secret
is not guaranteed invisible merely because it is in a vault or ignored `.env`. Use the host's
permission controls to limit tools when desired; the guide does not change them.
See [OpenAI's permission modes](https://learn.chatgpt.com/docs/permission-modes).

The project [security skill](../../../.claude/skills/security/SKILL.md) requires the owner to
perform secret entry. The assistant should never dump a vault, environment, browser cookies
or OS credentials into chat/logs. It can check configuration presence without displaying values.
Do not send a password-manager invitation or recovery code to “ChatGPT.” There is no need for
a new AI-service key merely to run these local account/approval controls.

## 7. Return later, reconnect and revoke access

1. Read the private tracker and current adapter status. Unlock your vault locally and repeat
   the fresh sign-in test with the saved method. If access fails, use the provider's official
   recovery route; report a redacted error and keep dependent account actions paused.
2. For a newly implemented adapter, recheck its developer setup and current consent scopes.
   Unsupported rows stay pending even if you can sign in successfully in the browser.
3. For an expired/revoked connection, select the exact profile/account and use the app's
   reconnect flow. Confirm any disconnect first; fresh consent replaces the local connection.
   Recheck the returned identity and update YouTube portfolio binding if its connection ID changed.
4. Repeat the restart/read-back check and date the tracker. Do not test disaster recovery by
   deleting the only working factor or revoking production credentials while a show is running.
5. If removing access, treat the following as separate actions. Check which apps/accounts
   share a provider grant before revoking it.

| Remove this access | Action |
|---|---|
| Portfolio route | `portfolio unbind` removes the local route only; it does not revoke OAuth |
| Local app connection | **Disconnect** removes its local record and OS token entry |
| Provider authorization | Revoke the application in that provider's connected-app/security settings; local deletion alone does not revoke the remote grant |
| Discord announcement webhook | Delete the specific webhook in the server/channel integrations as well; revoking OAuth alone must not be assumed to delete it |
| Browser session | Sign out/remove the session at the provider; this does not necessarily revoke the app's OAuth token |
| Assistant tool access | Disable the relevant browser/app connector or reduce host tool permissions; this is separate from the social provider's grant |
| Exposed credential | Owner rotates the affected password/client secret/key at its issuer, updates the private runtime source and reconnects affected apps; do not paste the old or new value into the incident report |

## 8. Hand back readiness and start testing

Use a short, non-secret update such as:

> YouTube / OpenTechnology: sign-in tested today on macOS; vault and recovery ready;
> app connection pending developer setup. AI Content and Gaming: not checked yet.
> Next task: help configure the YouTube callback; I will perform sign-in and consent.

The agent can add dated readiness summaries to the **private** reporting workflow. This guide
and template have no automatic synchronization, and the editorial report does not ingest these
manual readiness states. Link the private note from your private adapter when adopting it.

After account-read checks pass, choose an explicit bounded action test from
[manual acceptance](manual.md#verification): synthetic media, exact destination and scope.
YouTube can use a private upload; a restricted Discord test channel can contain an approved
message. Do not assume Twitch, X or another live/post destination has a private test mode.
Use local recording/dry-run checks until the owner deliberately authorizes the external test.
Record actual results and failures. Keep failed/pending rows visible so the next session can
resume from the first missing step.
