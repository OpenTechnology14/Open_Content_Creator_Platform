# Channel portfolio and AgentWorkflows controls

P-062 extends Social Management with local channel routing, source-backed video concepts,
revision-bound review and a production-brief handoff. The public
[AgentWorkflows library](https://github.com/OpenTechnology14/AgentWorkflows) supplies the
generic procedure. Its [content approval workflow](https://github.com/OpenTechnology14/AgentWorkflows/blob/fae0ee8/workflows/CONTENT_APPROVAL.md)
is prepared in [draft PR #3](https://github.com/OpenTechnology14/AgentWorkflows/pull/3),
not claimed released or installed. This page is the platform adapter and remains usable independently.

## Ownership and channel structure

[`social-channels.yaml`](../../../configs/local/social-channels.yaml) starts with:

| Logical channel | Social profile | Purpose |
|---|---|---|
| OpenTechnology | OpenTechMarketing | All eligible project walkthroughs, with playlists by project |
| AI Content Studio | Main Content | Original explainers, experiments and stories from reviewed Blog concepts |
| Gaming | Main Stream | Gaming shows and highlights; add separate configured channels as needed |

Names are editable configuration, not created YouTube channels. Adding another gaming
channel needs a unique ID and a valid social profile with YouTube `post-video` capability.
Use the existing private profile commands when another profile is needed; public config
must not contain account IDs or credentials. Existing starter profiles are unchanged.

Prepare the real identities with [account setup, passwords and agent access](accounts.md).
Its [private readiness template](account-readiness.template.md) covers all catalog providers,
including those whose adapters are pending. Browser sign-in readiness is a manual record;
the editorial report does not automatically import it or prove live token health.

Marketing Crosswalk still owns its registry and supported claims; Blog supplies ideas;
Content Creation owns rendering; Automation Control owns shows; Social owns identity and
the external-action gate. AgentWorkflows facilitates decisions and private Agent reporting
reads the current state. It is not an OpenTechnologyApp dashboard integration.

## Run the controls

From the repository root, use a Python environment installed with this module's
`requirements.txt`. The following prefix is used for every example:

```bash
PYTHONPATH=modules/social-management python3 -m social_management portfolio --help
PYTHONPATH=modules/social-management python3 -m social_management portfolio channels
PYTHONPATH=modules/social-management python3 -m social_management portfolio report
```

State is private under `~/.hybrid-creator-platform/social/editorial.sqlite3`. There are no
tokens in that database. `--state-dir` selects isolated test state; `--channels` selects a
different channel configuration. These options precede the action. No service starts and
no model/provider call is made. The desktop Social tabs retain their existing account UI;
these editorial controls are CLI/agent-operated, not new native buttons.

The agent reads actual Blog/marketing sources and fills a JSON concept matching
[`social-concept.example.json`](../../../configs/local/social-concept.example.json).
That example is synthetic and must not be presented as researched or owner-approved.
Source fields record provenance; the CLI validates structure and channel source kind,
not truth, copyright, marketing eligibility or source existence. The reviewing agent must
check those against the actual source and canonical marketing registry.

```bash
PYTHONPATH=modules/social-management python3 -m social_management portfolio submit concept.json
PYTHONPATH=modules/social-management python3 -m social_management portfolio report --format markdown
```

Read back the returned concept ID/revision and show up to three short concept cards.
Persist the owner's actual approval, rejection or revision request against that version:

```bash
PYTHONPATH=modules/social-management python3 -m social_management portfolio decide CONCEPT_ID approve \
  --revision 1 --confirm CONCEPT_ID@1 --actor owner --reason 'The actual owner answer'
PYTHONPATH=modules/social-management python3 -m social_management portfolio history CONCEPT_ID
PYTHONPATH=modules/social-management python3 -m social_management portfolio brief CONCEPT_ID --revision 2
```

Replace placeholders with returned values; use the latest read-back revision, not always
`2`. Every decision/edit increments revision. The command records an operator assertion
of owner consent; it is not an authentication system. An agent must not invent the answer.
Stale decisions fail instead of silently approving newer content. Edits invalidate approval:

```bash
PYTHONPATH=modules/social-management python3 -m social_management portfolio edit CONCEPT_ID revised.json --revision 2
PYTHONPATH=modules/social-management python3 -m social_management portfolio pause ai-content
PYTHONPATH=modules/social-management python3 -m social_management portfolio resume ai-content
```

Pause blocks new production briefs, not running render jobs, broadcasts or uploads.
Cancel those through their existing owners. A changed channel configuration also blocks
old briefs until the concept is edited and reviewed again. Brief files are snapshots;
the agent must recheck current revision/pause state before starting or resuming production.
There is no automatic renderer launch or scheduler in this slice.

## Bind real accounts separately

Use the existing Social tab/OAuth flow and let the owner complete consent. Read redacted
connection IDs with the existing `connections` command, then select the right one:

```bash
PYTHONPATH=modules/social-management python3 -m social_management portfolio bind ai-content CONNECTION_ID
PYTHONPATH=modules/social-management python3 -m social_management portfolio unbind ai-content
```

The connection must be YouTube and match the configured profile. The same remote YouTube
channel cannot be bound to two logical channels even through different connection records.
Disconnecting or changing a bound account produces `reconnect-required`; `locally-bound`
means only that the current local record matches. Live OAuth health, scopes and channel
eligibility remain existing provider acceptance. Unbind removes only the editorial route;
it does not revoke OAuth. Use the existing Social disconnect control for that.

Concept approval produces a brief with `publication_approved: false`. Finished-video review
and the existing approved-job/exact-ID publishing gate are separate. No content is posted,
uploaded or scheduled by the portfolio commands. CT-D19 tracks the unanswered automatic
publishing policy; existing final review remains in force.

## Agent reporting adapter

The facilitator resolves the checkout/interpreter from the local project installation,
reads this page and the actual CLI help, and records these controls in its private content
adapter. Never put workstation paths or live portfolio records into public AgentWorkflows.
Use `report` JSON (schema version 1) for structured status or Markdown for an owner view.
Refresh on request and after a decision. Save only an owned private report file, preserve
unrelated records, and timestamp the snapshot. No background polling or external send.

Reports include channels, cached binding readiness, concept versions/states, configuration
freshness and the final approval requirement. They omit remote account IDs and credentials.
Draft text and source references are private creative material: do not publish the report.
The command does not edit shared reporting indexes automatically. Analytics explicitly
reports `not-connected`; views/subscribers and revenue are never invented.

If the CLI or library is unavailable, keep the prompt prepared and label the report stale.
Writing a prompt or Markdown answer does not mean the target applied a decision. Read back
the result/history before claiming it did. SQLite transactions preserve history and reject
conflicting revisions; unknown database versions/corruption fail without resetting data.
Retain the database/history if rolling back the feature.

## Verification

Run `python3 -m pytest tests/social_management -q`, Ruff, the full offline suite and a real
CLI submit → approve → brief → edit → stale-approval rejection round trip in isolated state.
Exercise separate account bindings using synthetic connection records. Production media,
real provider accounts, native/Windows acceptance and audience performance remain separate.
