"""Coverage report: what content exists per subject, what is missing, and what is blocked.

Two different kinds of gap, deliberately reported separately:

  ledger gaps — BLOG_MARKETING_CONNECTION.md §2 says no blog post / course lab / lead email
    exists for this template. This is work to do.

  blocked assets — the subject's verified status is too low for an asset that asserts the
    template works today. This is not work to do; it is a claim we are not entitled to make
    until the target repo's own docs say otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from .crosswalk import Crosswalk
from .status import coverage_gaps, satisfies


@dataclass
class SubjectCoverage:
    module: str
    subject_id: str
    name: str
    status: str
    plan: str
    icps: List[str]
    channels: List[str]
    renderable: List[str]
    blocked: List[str]
    ledger_gaps: List[str]


def build(cw: Crosswalk, module: Optional[str] = None) -> List[SubjectCoverage]:
    report: List[SubjectCoverage] = []
    for entry in cw.modules:
        name = entry["module"]
        if module and name != module:
            continue
        for subject in cw.subjects.get(name, []):
            declared = list(subject.get("assets", []))
            renderable = [
                a for a in declared
                if satisfies(subject["status"], cw.assets[a]["claim_level"])
            ]
            report.append(SubjectCoverage(
                module=name,
                subject_id=subject["id"],
                name=subject["name"],
                status=subject["status"],
                plan=subject.get("plan", "starter"),
                icps=list(subject.get("icps", [])),
                channels=list(subject.get("channels", [])),
                renderable=renderable,
                blocked=[a for a in declared if a not in renderable],
                ledger_gaps=coverage_gaps(subject),
            ))
    return sorted(report, key=lambda c: (-len(c.ledger_gaps), -len(c.blocked), c.subject_id))


def channel_coverage(cw: Crosswalk, module: str, only: Optional[Set[str]] = None) -> Dict[str, List[str]]:
    """Which subjects feed each MARKETING.md channel. Empty list = an unfed channel."""
    result: Dict[str, List[str]] = {key: [] for key in cw.channels.get(module, {})}
    for subject in cw.subjects.get(module, []):
        if only is not None and subject["id"] not in only:
            continue
        for channel in subject.get("channels", []):
            if channel in result:
                result[channel].append(subject["id"])
    return result


def format_report(cw: Crosswalk, rows: List[SubjectCoverage], module: str) -> str:
    target = cw.targets[cw.target_for(module)]
    meta = cw.module_meta.get(module, {})
    out: List[str] = []
    out.append(f"Content coverage — Content Platform → {target['repo']} ({module})")
    out.append(f"Subjects from {meta.get('source_docs', {}).get('subjects', '?')}")
    out.append(f"Ledger    from {meta.get('source_docs', {}).get('coverage', '?')}")
    out.append("=" * 92)
    out.append(f"{'subject':<24}{'status':<21}{'plan':<9}{'render':>7}{'blocked':>9}{'  ledger gaps'}")
    out.append("-" * 92)
    for cov in rows:
        gaps = ",".join(g.replace("_", " ") for g in cov.ledger_gaps) or "—"
        out.append(
            f"{cov.subject_id:<24}{cov.status:<21}{cov.plan:<9}"
            f"{len(cov.renderable):>7}{len(cov.blocked):>9}  {gaps}"
        )
    out.append("-" * 92)
    out.append(
        f"{'TOTAL':<24}{'':<21}{'':<9}"
        f"{sum(len(c.renderable) for c in rows):>7}{sum(len(c.blocked) for c in rows):>9}"
    )
    out.append("")

    blocked_by_asset: Dict[str, List[str]] = {}
    for cov in rows:
        for asset in cov.blocked:
            blocked_by_asset.setdefault(asset, []).append(cov.subject_id)
    if blocked_by_asset:
        out.append("Blocked — status too low to assert the template works today")
        out.append("-" * 92)
        for asset, subjects in sorted(blocked_by_asset.items(), key=lambda kv: -len(kv[1])):
            out.append(f"  {asset:<20} {', '.join(subjects)}")
        out.append("")
        out.append("  Not defects. Each subject's status is verified against a named line in the")
        out.append("  target repo; when that line changes, update `status` + `status_evidence`")
        out.append("  together and these unblock.")
        out.append("")

    channels = channel_coverage(cw, module, only={c.subject_id for c in rows})
    channel_src = meta.get("source_docs", {}).get("channels", "per-module channel set")
    out.append(f"Channel coverage ({channel_src})")
    out.append("-" * 92)
    for channel, subjects in channels.items():
        marker = "  ← no subject feeds this channel" if not subjects else ""
        out.append(f"  {channel:<14}{len(subjects):>3} subject(s){marker}")
    return "\n".join(out)
