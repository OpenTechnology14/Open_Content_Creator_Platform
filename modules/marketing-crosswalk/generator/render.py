"""Render a subject into a channel asset.

Templates are markdown with `{{ placeholder }}` slots. There is deliberately no loop or
conditional syntax: anything list-shaped is flattened into a string by build_context() so
a template stays readable as the thing it produces. An unknown placeholder is an error,
never a silent blank — a half-filled draft that reaches a published page is worse than a
failed run.
"""

from __future__ import annotations

import datetime as dt
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .crosswalk import Crosswalk, CrosswalkError
from .status import STATUS_MEANING, coverage_gaps, satisfies

PLACEHOLDER = re.compile(r"\{\{\s*([a-z0-9_]+)\s*\}\}")

# TEMPLATE_REPO_CROSSWALK.md: "Job Hunter is public; everything else is private. Linking a
# Hybrid_Creator_Platform doc in any public-facing material (the blog, the course) produces
# a 404 for readers." Generated copy is public-facing, so a private repo URL in a draft is
# a defect the generator refuses to emit.
PRIVATE_REPO_URL = re.compile(r"github\.com/OpenTechnology14/([A-Za-z0-9_.-]+)")


class RenderError(RuntimeError):
    """Raised when a template cannot be filled honestly."""


class ClaimBlocked(RenderError):
    """Raised when an asset would claim more than the subject's verified status supports."""


class PrivateLinkLeak(RenderError):
    """Raised when a draft would publish a link to a private repository."""


def source_commit(repo_root: Path) -> str:
    """Short SHA the draft was generated from, so a stale draft is identifiable."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10, check=True,
        )
        return out.stdout.strip() or "unknown"
    except (subprocess.SubprocessError, OSError):
        return "unknown"


def _bullets(items: List[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- _(none listed)_"


def _coverage_cell(value) -> str:
    if value is False:
        return "**no — gap**"
    if value is True:
        return "yes"
    return str(value)


def build_context(cw: Crosswalk, module: str, subject: dict, asset: str) -> Dict[str, str]:
    """Flatten a subject into template placeholders."""
    if asset not in cw.assets:
        raise RenderError(f"unknown asset {asset!r}")
    if asset not in subject.get("assets", []):
        raise RenderError(
            f"subject {subject['id']!r} does not declare asset {asset!r}. "
            f"Declared: {', '.join(subject.get('assets', []))}"
        )

    spec = cw.assets[asset]
    entry = cw.module(module)
    status = subject["status"]

    if not satisfies(status, spec["claim_level"]):
        evidence = subject.get("status_evidence", {})
        raise ClaimBlocked(
            f"{subject['id']} is '{status}' ({STATUS_MEANING[status]}), but '{asset}' is a "
            f"claim_level={spec['claim_level']} asset that asserts the template works today.\n"
            f"  Evidence for that status: {evidence.get('file')} contains "
            f"{evidence.get('contains')!r}\n"
            f"  Either that changes in the target repo — update `status` and `status_evidence` "
            f"together — or generate a roadmap-level asset instead "
            f"({', '.join(sorted(k for k, v in cw.assets.items() if v['claim_level'] == 'roadmap'))})."
        )

    target_key = entry["target"]
    evidence_key = (subject.get("status_evidence") or {}).get("target", target_key)
    evidence_root = cw.evidence_root(module, subject)
    tgt = cw.targets[target_key]
    landing = cw.module_meta.get(module, {}).get("asset_landing", {}).get(asset)
    if not landing:
        raise RenderError(
            f"module {module!r} declares asset {asset!r} but no `asset_landing:` entry for it. "
            "Landings are per-module because each target repo has a different doc set — add "
            f"`{asset}: {{doc: ..., anchor: ...}}` to its subjects file."
        )
    doc_key, anchor_key = landing["doc"], landing["anchor"]
    if doc_key not in tgt["docs"]:
        raise RenderError(
            f"asset_landing for {asset!r} names doc {doc_key!r}, which target {target_key!r} "
            f"does not declare. Known: {', '.join(sorted(tgt['docs']))}"
        )
    doc = tgt["docs"][doc_key]
    if anchor_key not in doc.get("anchors", {}):
        raise RenderError(
            f"asset_landing for {asset!r} names anchor {anchor_key!r} in {doc_key!r}, which is "
            f"not declared. Known: {', '.join(sorted(doc.get('anchors', {})))}"
        )
    anchor_heading = doc["anchors"][anchor_key]

    product = cw.product_for(module)

    module_icps = cw.icps.get(module, {})
    icps = [(k, module_icps[k]) for k in subject.get("icps", []) if k in module_icps]
    primary_key, primary = icps[0] if icps else ("", {})

    module_channels = cw.channels.get(module, {})
    channel_labels = [module_channels[c] for c in subject.get("channels", []) if c in module_channels]

    competitors = subject.get("competitors", [])
    keywords = subject.get("keywords", [])
    coverage = subject.get("coverage", {})
    gaps = coverage_gaps(subject)

    upstream = subject.get("upstream", "none")
    public = subject.get("visibility") == "public"
    if upstream in (None, "none"):
        upstream_link = "_(no upstream repo — native to the app)_"
    elif public:
        upstream_link = f"https://github.com/{upstream}"
    else:
        upstream_link = (
            f"_**Do not link.** `{upstream}` is private; a link 404s for readers "
            "(TEMPLATE_REPO_CROSSWALK.md § Known gaps)._"
        )

    # Plan semantics differ per product — OpenTechnology's queue caps mean nothing to Stream
    # Extend's cloud tiers — so the note text comes from the module's own subjects file.
    plan = subject.get("plan", "")
    plan_notes = cw.module_meta.get(module, {}).get("plan_notes", {})
    if plan not in plan_notes:
        raise RenderError(
            f"subject {subject['id']!r} declares plan {plan!r}, which has no entry in this "
            f"module's `plan_notes:` block. Known: {', '.join(sorted(plan_notes)) or '(none)'}"
        )
    plan_note = plan_notes[plan]

    context = {
        "module": module,
        "subject_id": subject["id"],
        "subject_name": subject["name"],
        "what_it_is": " ".join(subject["what_it_is"].split()),

        "status": status,
        "status_meaning": STATUS_MEANING[status],
        "status_evidence_file": subject.get("status_evidence", {}).get("file", ""),
        "status_evidence_text": subject.get("status_evidence", {}).get("contains", ""),
        "status_evidence_target": evidence_key,
        "status_evidence_commit": source_commit(evidence_root) if evidence_root else "unknown",

        "plan": subject.get("plan", "starter"),
        "plan_note": plan_note,

        "coverage_table": "\n".join(
            f"| {k.replace('_', ' ')} | {_coverage_cell(v)} |" for k, v in coverage.items()
        ) or "| _(no ledger)_ | |",
        "coverage_gaps": ", ".join(g.replace("_", " ") for g in gaps) if gaps else "none",

        "upstream": upstream,
        "upstream_link": upstream_link,
        "visibility": subject.get("visibility", "private"),

        "product_name": product["name"],
        "product_alias": product.get("alias", ""),
        # A product with a declared `alias` has an unresolved rename. Public-facing copy must not
        # pick a name silently, so the caveat travels with every draft that could be published.
        "product_naming_note": (
            f"> ⚠️ **The product name is unsettled.** This draft says *{product['name']}*, but "
            f"`docs/REPOSITORY_ALIGNMENT.md` §\"Naming decision\" states the product and repository "
            f"are **{product['alias']}**. The marketing surfaces have not been migrated and a "
            "rename needs an approved proposal covering bundle IDs, URLs, and store listings. "
            "**Do not publish under either name until that resolves.**"
        ) if product.get("alias") else "",
        "product_link": product["link"],
        "product_tagline": product["tagline"],
        "product_one_liner": " ".join(product["one_liner"].split()),
        "product_pricing": product["pricing"],
        "product_wedge": _bullets(product["wedge"]),

        "icp_primary": primary_key or "unassigned",
        "icp_primary_who": primary.get("who", "_(unassigned)_"),
        "icp_primary_why": primary.get("why_they_switch", "_(unassigned)_"),
        "icp_primary_where": primary.get("where", "_(unassigned)_"),
        "icp_table": "\n".join(
            f"| {v['rank']} | {v['who']} | {v['why_they_switch']} | {v['where']} |"
            for _, v in icps
        ) or "| | _(none)_ | | |",
        "icp_list": ", ".join(k for k, _ in icps) or "_(none)_",

        "channels": " · ".join(channel_labels) or "_(none)_",
        "keyword_primary": keywords[0] if keywords else "_(none)_",
        # Secondary = everything after the primary, so a brief does not list the primary twice.
        "keywords_inline": ", ".join(f"`{k}`" for k in keywords[1:]) or "_(none beyond the primary)_",
        "keywords_all_inline": ", ".join(f"`{k}`" for k in keywords) or "_(none)_",
        "keywords_bullets": _bullets(keywords),
        "competitors_inline": ", ".join(competitors) or "_(none)_",
        "comparison_rows": "\n".join(
            f"| {c} | _TODO: verify_ | _TODO: verify_ |" for c in competitors
        ) or "| _(none listed)_ | | |",

        "asset": asset,
        "claim_level": spec["claim_level"],
        "engine_step": str(spec.get("engine_step", "—")),

        "target_repo": tgt["repo"],
        "target_doc": doc["path"],
        "target_anchor": anchor_heading,

        "generated_at": dt.date.today().isoformat(),
        "source_commit": source_commit(cw.root),
    }
    for key, value in coverage.items():
        context[f"coverage_{key}"] = _coverage_cell(value)
    return context


def check_private_links(body: str, subject: dict) -> None:
    """Refuse to emit a draft containing a link to a private OpenTechnology14 repo."""
    public_repo = subject.get("upstream") if subject.get("visibility") == "public" else None
    leaked = {
        name for name in PRIVATE_REPO_URL.findall(body)
        if not (public_repo and public_repo.endswith(name))
    }
    if leaked:
        raise PrivateLinkLeak(
            f"draft links private repo(s) {sorted(leaked)}. TEMPLATE_REPO_CROSSWALK.md: "
            "'Job Hunter is public; everything else is private' — a link to any other repo "
            "404s for readers. Remove the link from the template."
        )


def render(cw: Crosswalk, module: str, subject: dict, asset: str) -> str:
    """Render one asset. Raises rather than emitting a partial or unpublishable draft."""
    spec = cw.assets.get(asset)
    if spec is None:
        raise RenderError(f"unknown asset {asset!r}")

    template_path = cw.module_root / "templates" / spec["template"]
    if not template_path.is_file():
        raise RenderError(f"template not found: {template_path}")

    context = build_context(cw, module, subject, asset)
    missing: List[str] = []

    def substitute(match: "re.Match[str]") -> str:
        key = match.group(1)
        if key not in context:
            missing.append(key)
            return match.group(0)
        return context[key]

    filled = PLACEHOLDER.sub(substitute, template_path.read_text(encoding="utf-8"))
    if missing:
        raise RenderError(
            f"{spec['template']} uses placeholder(s) the context does not provide: "
            f"{sorted(set(missing))}. Available: {sorted(context)}"
        )

    check_private_links(filled, subject)
    return filled


def draft_filename(module: str, subject: dict, asset: str) -> str:
    return f"{module}--{subject['id']}--{asset}.md"


def assets_for(cw: Crosswalk, subject: dict, only: Optional[List[str]] = None) -> List[str]:
    """Assets declared by a subject, optionally filtered, ordered by the content engine."""
    declared = list(subject.get("assets", []))
    if only:
        unknown = [a for a in only if a not in cw.assets]
        if unknown:
            raise CrosswalkError(
                f"unknown asset(s) {unknown}. Known: {', '.join(sorted(cw.assets))}"
            )
        declared = [a for a in only if a in declared]

    order = cw.engine_order
    return sorted(declared, key=lambda a: (order.index(a) if a in order else len(order), a))


def selftest(cw: Crosswalk) -> Tuple[int, List[str]]:
    """Render every declared (subject, asset) pair in memory, ignoring claim gating.

    Assets with claim_level: shipped are blocked for any subject whose verified status is
    lower, so they would otherwise never execute for those subjects — a typo in one of
    those templates would surface for the first time on the day a status changes. This
    renders them all, in memory, and writes nothing. It proves the templates work; it does
    not authorise any claim.

    Returns (pairs_attempted, grouped_failures).
    """
    from collections import OrderedDict

    grouped: "OrderedDict[str, List[str]]" = OrderedDict()
    pairs = 0
    for entry in cw.modules:
        module = entry["module"]
        for subject in cw.subjects.get(module, []):
            for asset in subject.get("assets", []):
                pairs += 1
                problem = None
                try:
                    body = _render_ignoring_claims(cw, module, subject, asset)
                except Exception as exc:  # noqa: BLE001 - reported, not swallowed
                    problem = str(exc)
                else:
                    leftover = sorted(set(PLACEHOLDER.findall(body)))
                    if leftover:
                        problem = f"unfilled placeholders {leftover}"
                if problem is not None:
                    grouped.setdefault(f"{asset}: {problem}", []).append(subject["id"])

    failures = [
        f"{problem}\n    affects {len(ids)} subject(s): {', '.join(ids)}"
        for problem, ids in grouped.items()
    ]
    return pairs, failures


def _render_ignoring_claims(cw: Crosswalk, module: str, subject: dict, asset: str) -> str:
    """render() with the claim gate lifted, for selftest only."""
    probe = dict(subject)
    probe["status"] = "shipped"
    return render(cw, module, probe, asset)
