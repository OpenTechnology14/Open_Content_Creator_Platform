# Third-party notices

This file carries the notices that a license requires this repository to keep. It is **not** the project's license
(that is [`LICENSE`](LICENSE), MIT) and it is **not** a license review (that is
[`docs/THIRD_PARTY_PROVENANCE.md`](docs/THIRD_PARTY_PROVENANCE.md), which lists every component with its license and any
flag for the owner). Read on 2026-10-23.

## Material in this repository

### Contributor Covenant 2.1

[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) is the Contributor Covenant, version 2.1, © the Contributor Covenant authors,
available at <https://www.contributor-covenant.org/version/2/1/code_of_conduct.html> and licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The only change is the contact method in the enforcement
section, which this project supplies.

### Soundboard audio

Eight files under `modules/soundboard/sounds/` are from Kenney.nl's
[Interface Sounds](https://kenney.nl/assets/interface-sounds), released under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) (a public-domain dedication). No attribution is required;
Kenney is credited here as a courtesy. Each file's source and license is recorded in
[`modules/soundboard/sounds/manifest.yaml`](modules/soundboard/sounds/manifest.yaml).

## Components compiled into the desktop apps

`apps/stream-extend`, `apps/creator-extend` and `apps/extend` compile third-party Rust crates and bundle built frontend
assets. Today their installers are private, unsigned CI artifacts. Across the three apps there are 614 third-party crates,
all under permissive licenses (MIT, Apache-2.0, BSD, ISC, Zlib, Unicode, Unlicense, CC0) except the following.

| Crate | Version | License | What it means here |
|---|---|---|---|
| `cssparser`, `cssparser-macros`, `dtoa-short`, `option-ext`, `selectors` | 0.36.0, 0.6.1, 0.3.5, 0.2.0, 0.36.1 | MPL-2.0 | Copyleft applies to those files only. They are used unmodified, and their source is available on [crates.io](https://crates.io) under each crate name |
| `webpki-roots` | 1.0.9 | CDLA-Permissive-2.0 | Certificate data under a permissive data license |
| `r-efi` | 5.3.0, 6.0.0 | MIT OR Apache-2.0 OR LGPL-2.1-or-later | Taken here under MIT or Apache-2.0 |

The complete per-crate and per-package notice text, the copyright lines and license texts that MIT, BSD and Apache-2.0 require
to travel with a binary, is a **release artifact**. It is generated when a public installer is built (for example with
`cargo about` for the Rust crates and a Node license reporter for the frontend), not before: no public installer exists
yet. See `OSS-D15` in [`docs/proposals/PROPOSAL_OPEN_SOURCE_RELEASE_PLAN.md`](docs/proposals/PROPOSAL_OPEN_SOURCE_RELEASE_PLAN.md).

## Components this repository does not redistribute

Python libraries, services, plugin hosts, models and external tools are installed or pulled by the user and are not
committed here. Their licenses, including the copyleft and non-commercial ones, are listed in
[`docs/THIRD_PARTY_PROVENANCE.md`](docs/THIRD_PARTY_PROVENANCE.md). MIT, the license of this repository's own code, does not
change any of their terms.
