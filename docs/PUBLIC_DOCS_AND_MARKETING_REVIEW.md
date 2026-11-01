# Public documentation and marketing review

> **Status:** Dated review · **Last reviewed:** 2026-10-05 · **Owner:** OpenTechnology14

**Reviewed:** 2026-10-05. **Scope:** owner-requested P-071 documentation and P-070
walkthrough extension; P-002/P-001 retain release decisions. Reference repositories were
read only. This is a source review, not a usability study or a claim that deployed pages
match the local files. The [documentation website](public/index.html) is the resulting local preview.

## Recommendation

Use a task-first documentation front door with three paths: first recording, recording to
clip, and engineering. Retain the detailed module references behind those paths. Reuse the
existing marketing-crosswalk module for this app's own material through its `stream-extend`
and `content-extend` consumers. Their presence means no new top-level marketing module is
needed. The shared walkthrough format also supports `task-management`, so improvements
benefit OpenTechnologyApp's material without editing that application in this project.

OpenTechnologyApp is a useful benchmark, not a proven best-in-class documentation system.
Its strongest pattern is explaining a real task in plain language and linking to a deeper
reference. Its weakest pattern is duplicated facts that age independently. Copy the former;
use revision-linked evidence and a release review to reduce the latter.

## References and findings

| Reference inspected | Strength to reuse | Weakness or missing proof | Applied here |
|---|---|---|---|
| Public `OpenTechnology14/Job-Hunter`, HEAD `ffa2cd64bd28a17e303ecc94b093b1fe36e02882`; repository metadata, README, LICENSE and root inventory. *(2026-10-28 note: that repository is now the private archive `job-hunter-archive`, so this SHA resolves only there; the public repository was re-created on 2026-10-27 at `0fd2fca`, with clone URLs and the license holder corrected.)* | Public MIT license; example-profile setup; security, contribution, testing and nontechnical guide entry points | README still uses `YOUR_USERNAME` in clone instructions; license names `Example Moody`, whose identity was not verified. No `.github/workflows` directory was returned by the contents API; this does not prove all forms of CI are absent | Verify real clone/download destinations and copyright holder before release; separate beginner and contributor paths |
| `OpenTechnologyApp` at `752b972`, `MARKETING.md` | Defined audiences; one content source reused across channels; practical coverage and launch tracking | June launch states remain in an October checkout; static prices and directory rules need rechecking. “All-in-one alternative” is broad positioning rather than proof of feature parity | One audience and demonstrated result per walkthrough; no copied prices, directory promises or performance claims |
| Same checkout, `OpenTechnologyApp:docs/readable/BLOG_MARKETING_CONNECTION.md` | Distinguishes app sources, blog coverage and technical integration; explicitly separates scripted course material from produced videos | Its personality table still calls blog PRs #38/#49 unmerged while the platform registry records their merge; its final sync note is August 19 | Record source revision plus independent capture/publication state; do not infer publication from source presence |
| Same checkout, `OpenTechnologyApp:docs/readable/README.md`, `APP_PLAYBOOK.md`, `TEMPLATE_REPO_CROSSWALK.md` | Readable prose separated from generated inventories; architecture, templates and upstream sources discoverable | The playbook's dense implementation history is difficult for beginners. The same feature section contains older default-off wording and later default-on clarification | Keep beginner tasks short; engineering links carry architecture, contracts and verification depth |
| `OpenTechnologyBlog` at `0397072`, `src/app/open-technology-app/docs/page.tsx` | Task groups: Evaluate, Start, Run it yourself, Integrate, Trust | Local source alone establishes neither public availability nor link correctness after deployment | Use task-based navigation; explicitly label local preview and validate signed-out links before publishing |
| Same checkout, `OpenTechnologyBlog:src/app/open-technology-app/docs/getting-started/page.tsx` | Numbered path; optional portal and AI steps; shared product-data imports reduce duplicated template names | Eight steps mix a first success with dashboards, invitations and plan gates. The inspected page lacks a concrete final result and per-step recovery | First exercise ends at a saved, replayed recording; each step has a check and recovery |
| Same checkout, `content/blog/project-management-for-beginners.mdx` | Defines terms at first use; familiar example; explicit limitations; links to technical companion | Useful explanation, but not an observed walkthrough of the current UI | Add exact screen actions and capture evidence before treating prose as a walkthrough |
| Same checkout, `content/blog/content-extend-template.mdx` | Honest bridge limitation; concrete queues and automation examples | Calls the app's template set “five” while the marketing registry has six. Its subject is the OpenTechnologyApp operations template, which can be confused with the Creator desktop app | Keep `task-management/extend_platform` separate from this app's two product consumers; do not commission a duplicate template introduction |
| This repository, `docs/architecture/product-spec.md`, README and release checklist | Local-first boundaries and explicit release gates already exist | README/spec asserted BSL and paid-source terms despite no root license, conflicting with the owner's new open-source direction | Updated those policy statements to intended open-source distribution with license/scope pending |

A private local working copy of JobHunter was empty, so JobHunter verification used the
public GitHub repository, not inferred contents of that directory. The similarly named
`OpenTechApp` directory contains design assets; the app reference was `OpenTechnologyApp`.
Only the named reference surfaces were reviewed; this is not an exhaustive audit of either sibling.

## Open-source release direction

[JobHunter](https://github.com/OpenTechnology14/job-hunter) is public and its
[license file](https://github.com/OpenTechnology14/job-hunter/blob/0fd2fcaf523e430cca2bd81c6e251ce0183ab928/LICENSE)
contains MIT terms (re-pinned 2026-10-28: the repository was re-created on 2026-10-27, and the earlier
`ffa2cd6` link resolves only in the private archive). GitHub metadata identifies this platform as private with no detected
license; no root `LICENSE` is present locally. Neither a public README nor an intent statement
substitutes for that file.

The previous BSL plan is materially different: the
[BSL 1.1 text](https://mariadb.com/bsl11/) explicitly states it is not an open-source license.
The owner has supplied the new direction, but not a specific license or copyright holder.
Record those decisions before issuing a license. Do not inherit `Example Moody` from JobHunter.
OpenTechnologyApp's paid self-host/source-access marketing is not the distribution model to
copy for this goal.

P-001 owns release engineering and the [release checklist](OPEN_SOURCE_RELEASE_CHECKLIST.md).
P-002 retains the license/distribution and companion decisions. Before publication, establish
release scope, dependency/model/plugin notices, secret-history scan evidence, clean-clone
build evidence, versioned artifacts and public support links. Those are existing release
requirements, not new prerequisites to writing these docs. No release gate is marked passed here.

## Material delivered in this change

- A self-contained, responsive [documentation website](public/index.html), with beginner OBS
  practice, troubleshooting, current recording/clip boundaries, engineering links and release
  status. It works from a local checkout without JavaScript or external assets.
- A `walkthrough-brief` asset in the existing generator, enabled for all 26 subjects across
  `stream-extend`, `content-extend` and `task-management`. It generates an editorial brief;
  it does not automate screenshots, narration, recording or publication.
- Source/status provenance, exact action/result/recovery rows, capture record, accessibility
  deliverables and a technical companion in every brief. Existing claim/private-link gates
  remain in place. No subject or platform module is promoted by adding this format.
- Release-direction corrections in the README, product spec, P-002 and release checklist.

The website's internal source links assume it is served from this repository's root or opened
locally. Public deployment must render or export the referenced documents, preserve relative
paths or rewrite them to versioned public destinations, and verify them without authentication.
Do not publish only `docs/public/` and leave the reference links broken.

To preview locally from the repository root:

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/docs/public/`. The server exposes the checkout only on loopback;
stop it with Ctrl-C after review. Do not reuse this preview command as public hosting.

## Publication sequence and remaining gaps

| Order | Material | Acceptance evidence | Existing owner |
|---|---|---|---|
| 1 | First private recording walkthrough | Clean supported OS, actual UI capture, saved file played back, one failure/recovery; captions/transcript | P-063/P-070 |
| 2 | Recording to reviewed clip | Correct inbox ownership, real trim/review/render, inspected MP4; disclose current CLI handoff until adapter exists | P-056/P-072 |
| 3 | Engineering companion | Pinned commit, reproducible setup, contracts, failure tests, hardware limits and safe sample data | P-071 documentation; owning feature proposal |
| 4 | Public docs site and release page | Chosen public route/hosting, versioned docs, signed-out links, accessible mobile/keyboard review, verified download/checksum/support targets | P-001/P-002 |
| 5 | Blog and short-form material | Reuse existing template articles; review current counts, source scope and product names; capture and publication recorded separately | P-070; blog's coverage ledger |

For OpenTechnologyApp's next documentation pass, prioritize the stale merge notes/template count,
then split the first-success tutorial from optional administration and add error/recovery examples.
Audit the public-docs data against the app before reusing pricing or feature claims. Its
engineering depth should stay available through specific task links rather than a long playbook
as the beginner front door. Findings above are recorded for that repository; it was not modified.

## Verification

- `PATH="$PWD/.venv-stream-autopilot/bin:$PATH" make test`: reached 100%, exit 0;
  output `/tmp/hcp-public-docs-tests.log`. Required offline suite, not device acceptance.
- `pytest -q tests/marketing_crosswalk/test_walkthrough_briefs.py`: four cases passed,
  including incomplete-subject output and refusal to render a private repository URL.
- Marketing CLI `validate`: 55 anchor checks and 47 status claims passed. `selftest`:
  238 subject/asset pairs rendered with no failures. Both exited 0.
- Real CLI generation wrote 11 Stream, 9 Content and 6 OpenTechnologyApp walkthrough briefs
  to ignored `output/public-docs-walkthroughs/`; all three commands exited 0. No sibling writes.
- Headless Chromium: 1280, 768, 390 and 320px layouts had no horizontal overflow;
  troubleshooting disclosure and engineering anchor navigation passed; no page errors.
  Desktop/mobile screenshots inspected. All 24 local href targets/HTML anchors exist.
- Ruff passed for the generator and new test; `git diff --check` passed.
- After staging new documents, `pytest -q tests/docs` reached 100%, exit 0.
  The first pass caught three sibling-source citations written as local paths; qualifying
  them with their owning repository fixed the ambiguity. Log: `/tmp/hcp-public-docs-integrity.log`.

No real OBS/device session, finished walkthrough recording, public website deployment,
license issuance, or live beginner usability test was performed in this documentation change.
