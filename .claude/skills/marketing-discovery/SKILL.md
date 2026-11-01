---
name: marketing-discovery
description: Identify which marketing module a request belongs to, in this repo or when referenced from OpenTechnologyApp or OpenTechnologyBlog. Use before writing marketing content, before creating a marketing module, and whenever a request names a module that has "AI", "learning", "control", "chatbot" or a product name in it.
when_to_use: "Examples: 'write marketing content for…', 'which module is this about?', 'create a marketing module', or any request that names a registered module or product (AI Learning, AI Control Layer, Chatbot Routing, Task Management, Stream Extend, Content Extend, MyFeed, Ironfall, AnimalHouse, Gist)."
---

# Marketing module discovery

**Read the registry before answering.** Do not identify a marketing module from memory or from a
name match — that is how the AI Learning Series got routed to AI Control Layer twice.

## Step 1 — enumerate the modules

```bash
cat modules/marketing-crosswalk/crosswalk/modules.yml
```

This is the canonical registry for all three repositories. There is no second list. If you are
invoked from OpenTechnologyApp or OpenTechnologyBlog, that repo holds only a pointer
(`MARKETING_CROSSWALK_POINTER.md`) — the registry itself lives here.

Each target's go-to-market playbook is a registered doc (`targets.yml` → `marketing_playbook`):
OpenTechnologyApp's `MARKETING.md`, and this repo's `MARKETING.md` (the `stream-extend` and
`content-extend` rows list it as `files.marketing_doc`).

Can't find the checkout:

```bash
find ~ -maxdepth 4 -path '*/marketing-crosswalk/crosswalk/modules.yml' 2>/dev/null
```

## Step 2 — match intent against two fields, not the name

| Field | Use |
|---|---|
| `discovery_keywords` | Search terms, synonyms, spelling variants, proposal IDs |
| `notes` | Plain-language description of what the module **is** and what routes to it |

```bash
rg -i -B2 -A18 "<term>" modules/marketing-crosswalk/crosswalk/modules.yml
```

## Step 3 — always read `not_to_be_confused_with`

Three modules have "AI" in the name. **A name match is not a match.** Check this field on any
candidate before acting:

| Request is about | Module | Commonly mistaken for |
|---|---|---|
| Four lessons teaching how to use AI (model choice, prompting, app building, cost) | `ai-learning` | `ai-control-layer` |
| Ongoing AI governance and practice library — intent, docs, permissions, evidence | `ai-control-layer` | `ai-learning` |
| How OpenTechApp routes chat requests between vendors; thresholds, kill switch | `chatbot-routing` | `ai-control-layer` |
| Project templates, queues, client portal, Jira/Monday comparisons | `task-management` | — |
| OBS, streaming, overlays, encoders | `stream-extend` | `content-extend` |
| ComfyUI, Blender, Krita, generation, render pipelines | `content-extend` | `stream-extend` |

If two modules still look plausible, **ask** rather than picking. A misrouted module produces
content filed against the wrong product.

## Step 4 — check whether the module can actually generate

Some modules are registered for discovery only, with `subjects: []` and a `pending_pr`. They are
findable but not claimable: `generate` produces nothing for them, and their status cannot be cited.
Read the subjects file's `promotion:` block for what unblocks them.

## Step 5 — treat counts as navigation, not evidence

`counts` is hand-maintained with a `basis` line and drifts silently. When it disagrees with the
repository, **the repository wins.** A public claim needs a subject's `status_evidence`, which the
validator re-reads — never a count.

## Before generating anything

```bash
cd modules/marketing-crosswalk && python3 -m generator.cli validate
```

`validate` re-checks every marketing-doc anchor and status claim against the target repos. If it
reports findings, fix them before generating: the module's whole value is that it refuses to
generate a claim it cannot evidence.

## Adding a module

Registering one is an explicit act — a row in `modules.yml` plus a subjects file. `crosswalk/schema.md`
has the field reference, and README § "Onboarding the next module" has the procedure. Every new row
needs `notes`, `discovery_keywords` and `not_to_be_confused_with`, or the next session will not
find it.
