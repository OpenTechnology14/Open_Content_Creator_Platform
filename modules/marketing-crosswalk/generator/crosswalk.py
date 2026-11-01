"""Load and validate the crosswalk against both repositories.

The Content Platform (this repository) generates content for the modules listed in
crosswalk/modules.yml. Each module names a subjects file describing what the content
is about, and a target whose marketing docs receive it.

Validation is the module's primary value. BLOG_MARKETING_CONNECTION.md §1 states that
the product/content relationship is "kept in sync by hand" with "no code dependency in
either direction", and that "nothing here alerts on drift". This is that alert: the
marketing-doc anchors, the per-template coverage ledger, and every status claim are all
re-checked against the target repo before anything renders.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .status import EvidenceResult, StatusError, verify_evidence

CROSSWALK_FILES = ("targets.yml", "products.yml", "assets.yml", "modules.yml")

log = logging.getLogger("marketing-crosswalk")


class CrosswalkError(RuntimeError):
    """Raised when the crosswalk does not match observed repository state."""


@dataclass
class Finding:
    """One validation problem. Never suppressed — surfaced with a fix hint."""

    severity: str  # "error" | "warning"
    where: str
    problem: str
    fix: str

    def render(self) -> str:
        mark = "ERROR" if self.severity == "error" else "warn "
        return f"  [{mark}] {self.where}\n          {self.problem}\n          fix: {self.fix}"


@dataclass
class Crosswalk:
    root: Path
    module_root: Path
    targets: dict
    products: dict
    icps: Dict[str, dict]                    # module name -> its ICP set
    channels: Dict[str, dict]                # module name -> its channel set
    assets: dict
    engine_order: List[str]
    modules: List[dict]
    subjects: Dict[str, List[dict]]          # module name -> subject rows
    module_meta: Dict[str, dict]             # module name -> its subjects file's top-level keys
    target_paths: Dict[str, Optional[Path]]  # target key -> local checkout
    findings: List[Finding] = field(default_factory=list)

    # -- lookups -----------------------------------------------------------
    def module(self, name: str) -> dict:
        for entry in self.modules:
            if entry["module"] == name:
                return entry
        known = ", ".join(sorted(m["module"] for m in self.modules))
        raise CrosswalkError(
            f"no module row for {name!r}. Onboarded: {known}. "
            "Add a row to crosswalk/modules.yml plus a subjects file to onboard one."
        )

    def subject(self, module: str, subject_id: str) -> dict:
        for row in self.subjects.get(module, []):
            if row["id"] == subject_id:
                return row
        known = ", ".join(r["id"] for r in self.subjects.get(module, []))
        raise CrosswalkError(f"no subject {subject_id!r} in module {module!r}. Known: {known}")

    def product_for(self, module: str) -> dict:
        key = self.module_meta.get(module, {}).get("product")
        if key not in self.products:
            known = ", ".join(sorted(self.products))
            raise CrosswalkError(
                f"module {module!r} declares product {key!r}, which is not in products.yml. "
                f"Known: {known}"
            )
        return self.products[key]

    def target_for(self, module: str) -> str:
        return self.module(module)["target"]

    def target_path(self, module: str) -> Optional[Path]:
        return self.target_paths.get(self.target_for(module))

    def evidence_root(self, module: str, subject: dict) -> Optional[Path]:
        """Checkout a subject's status evidence is read from.

        Defaults to the module's target. `status_evidence.target` overrides it, for a module
        whose content is delivered to one repo but whose subjects are authored in another
        (the ai-learning lessons live here and are delivered to the blog).
        """
        key = (subject.get("status_evidence") or {}).get("target")
        if key is None:
            return self.target_path(module)
        if key not in self.target_paths:
            raise StatusError(
                f"subject {subject.get('id')!r} status_evidence.target {key!r} is not in "
                f"targets.yml. Known: {', '.join(sorted(self.target_paths))}"
            )
        return self.target_paths[key]

    def evidence(self, module: str, subject: dict) -> EvidenceResult:
        return verify_evidence(subject, self.evidence_root(module, subject))

    @property
    def errors(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "error"]


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise CrosswalkError(f"missing crosswalk file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CrosswalkError(f"{path} did not parse to a mapping")
    if data.get("schema_version") != 1:
        raise CrosswalkError(
            f"{path} declares schema_version {data.get('schema_version')!r}; "
            "this generator understands version 1"
        )
    return data


def resolve_target_path(spec: dict, override: Optional[str], repo_root: Path) -> Path:
    """--target-path > $ENV_VAR > default_path relative to repo root."""
    if override:
        return Path(override).expanduser().resolve()
    env_value = os.getenv(spec["path_env"])
    if env_value:
        return Path(env_value).expanduser().resolve()
    return (repo_root / spec["default_path"]).resolve()


def load(module_root: Path, repo_root: Path, target_path: Optional[str] = None) -> Crosswalk:
    """Load the registry, every subjects file, and resolve each target checkout."""
    data = {name: _load_yaml(module_root / "crosswalk" / name) for name in CROSSWALK_FILES}
    assets_doc = data["assets.yml"]

    modules = data["modules.yml"]["modules"]
    subjects: Dict[str, List[dict]] = {}
    module_meta: Dict[str, dict] = {}
    icps: Dict[str, dict] = {}
    channels: Dict[str, dict] = {}
    for entry in modules:
        doc = _load_yaml(module_root / "crosswalk" / entry["subjects"])
        name = entry["module"]
        subjects[name] = doc["subjects"]
        icps[name] = doc.get("icps", {})
        channels[name] = doc.get("channels", {})
        module_meta[name] = {
            k: v for k, v in doc.items() if k not in ("subjects", "icps", "channels")
        }
        if not icps[name]:
            raise CrosswalkError(
                f"{entry['subjects']} declares no `icps:` block. ICPs are module-scoped so each "
                "set keeps the provenance of the doc it was transcribed from."
            )

    targets = data["targets.yml"]["targets"]
    paths = {
        key: resolve_target_path(spec, target_path, repo_root)
        for key, spec in targets.items()
    }

    return Crosswalk(
        root=repo_root,
        module_root=module_root,
        targets=targets,
        products=data["products.yml"]["products"],
        icps=icps,
        channels=channels,
        assets=assets_doc["assets"],
        engine_order=assets_doc.get("engine_order", []),
        modules=modules,
        subjects=subjects,
        module_meta=module_meta,
        target_paths=paths,
    )


def validate(cw: Crosswalk) -> List[Finding]:
    """Check the crosswalk against both repositories. Returns findings; also stored on cw."""
    findings: List[Finding] = []

    # 1. Every asset has a template on disk.
    for name, spec in cw.assets.items():
        if not (cw.module_root / "templates" / spec["template"]).is_file():
            findings.append(Finding(
                "error", f"assets.yml: {name}",
                f"template {spec['template']} does not exist",
                f"create templates/{spec['template']}",
            ))

    # 2. Each module's target resolves, and its declared docs + anchors still exist.
    for entry in cw.modules:
        findings.extend(_validate_target(cw, entry))

    # 3. Subject rows resolve, and every status claim is re-verified against the target.
    for entry in cw.modules:
        findings.extend(_validate_subjects(cw, entry))

    # 4. Private modules stay discoverable but inert, and public rows never name them.
    findings.extend(_validate_visibility(cw))

    cw.findings = findings
    return findings


def _validate_visibility(cw: Crosswalk) -> List[Finding]:
    """`visibility: private` means findable by the owner, never claimable, never mentioned publicly."""
    findings: List[Finding] = []
    private_targets = {k for k, spec in cw.targets.items() if spec.get("visibility") == "private"}
    private = [m for m in cw.modules if m.get("visibility") == "private"]
    for entry in cw.modules:
        name, is_private = entry["module"], entry.get("visibility") == "private"
        where = f"modules.yml: {name}"
        if is_private and entry["target"] not in private_targets:
            findings.append(Finding(
                "error", where, "private module targets a target that is not `visibility: private`",
                "point it at a private target in targets.yml",
            ))
        if not is_private and entry["target"] in private_targets:
            findings.append(Finding(
                "error", where, "public module targets a private target",
                "private targets are for `visibility: private` modules only",
            ))
        if is_private and cw.subjects.get(name):
            findings.append(Finding(
                "error", where, "private module declares subjects, so it could generate content",
                "keep `subjects: []` — a private module is never a content target",
            ))
    # Match registry ids only. A list of forbidden names committed to a repository would itself be
    # the leak, and topic names ("device audit") legitimately appear in public subjects.
    names = {m["module"].lower() for m in private}
    for entry in cw.modules:
        if entry.get("visibility") == "private":
            continue
        name = entry["module"]
        haystack = json.dumps(
            [entry, cw.subjects.get(name), cw.module_meta.get(name)], default=str
        ).lower()
        for private_name in sorted(names):
            if private_name in haystack:
                findings.append(Finding(
                    "error", f"modules.yml: {name}",
                    f"public module mentions the private module id {private_name!r}",
                    "private rows may point at public modules, never the other way round",
                ))
    return findings


def _validate_target(cw: Crosswalk, entry: dict) -> List[Finding]:
    findings: List[Finding] = []
    target = entry["target"]
    if target not in cw.targets:
        return [Finding(
            "error", f"modules.yml: {entry['module']}",
            f"unknown target {target!r}",
            f"use one of: {', '.join(sorted(cw.targets))}",
        )]

    spec = cw.targets[target]
    path = cw.target_paths.get(target)
    if path is None or not path.is_dir():
        if spec.get("optional"):
            # Discovery-only targets declare no docs to verify, so an absent checkout loses nothing.
            log.info("  target %s is optional and not checked out (set $%s to verify it)",
                     target, spec["path_env"])
            return []
        return [Finding(
            "error", f"target {target}",
            f"target repository not found at {path}",
            f"clone {spec['repo']}, or set ${spec['path_env']}, or pass --target-path",
        )]

    for doc_key, doc in spec["docs"].items():
        doc_path = path / doc["path"]
        if not doc_path.is_file():
            findings.append(Finding(
                "error", f"{target}:{doc['path']}",
                "declared marketing doc does not exist in the target repo",
                f"the doc moved or was renamed — update docs.{doc_key}.path in targets.yml",
            ))
            continue
        lines = {line.rstrip() for line in doc_path.read_text(encoding="utf-8").splitlines()}
        for anchor_key, heading in doc.get("anchors", {}).items():
            if heading not in lines:
                findings.append(Finding(
                    "error", f"{target}:{doc['path']} → {anchor_key}",
                    f"anchor heading not found: {heading!r}",
                    "the heading was edited in the target repo — update the anchor in "
                    "targets.yml to the new text before generating against it",
                ))
    return findings


def _validate_subjects(cw: Crosswalk, entry: dict) -> List[Finding]:
    findings: List[Finding] = []
    module = entry["module"]

    seen = set()
    for subject in cw.subjects.get(module, []):
        where = f"{entry['subjects']}: {subject.get('id')}"

        if subject["id"] in seen:
            findings.append(Finding("error", where, "duplicate subject id", "make ids unique"))
        seen.add(subject["id"])

        known_icps = cw.icps.get(module, {})
        for icp in subject.get("icps", []):
            if icp not in known_icps:
                findings.append(Finding(
                    "error", where, f"unknown ICP {icp!r} for module {module!r}",
                    f"use one of: {', '.join(sorted(known_icps))}, or add it to this "
                    "file's `icps:` block",
                ))
        known_channels = cw.channels.get(module, {})
        for channel in subject.get("channels", []):
            if channel not in known_channels:
                findings.append(Finding(
                    "error", where, f"unknown channel {channel!r} for module {module!r}",
                    f"use one of: {', '.join(sorted(known_channels))}, or add it to this "
                    "file's `channels:` block",
                ))
        landings = cw.module_meta.get(module, {}).get("asset_landing", {})
        for asset in subject.get("assets", []):
            if asset not in cw.assets:
                findings.append(Finding(
                    "error", where, f"unknown asset {asset!r}",
                    f"use one of: {', '.join(sorted(cw.assets))}",
                ))
            elif asset not in landings:
                findings.append(Finding(
                    "error", where,
                    f"asset {asset!r} has no `asset_landing:` entry for module {module!r}",
                    "each module maps its assets onto its own target's docs — add "
                    f"`{asset}: {{doc: ..., anchor: ...}}` to this file's asset_landing block",
                ))

        # The status claim must still be backed by the line it cites.
        try:
            root = cw.evidence_root(module, subject)
            result = (
                verify_evidence(subject, root) if root is not None and root.is_dir() else None
            )
        except StatusError as exc:
            findings.append(Finding("error", where, str(exc), "add or correct status_evidence"))
        else:
            if result is not None and not result.verified:
                findings.append(Finding(
                    "error", where,
                    f"status {result.status!r} cites {result.file} containing "
                    f"{result.contains!r} — {result.detail}",
                    "re-read that file and update `status` and `status_evidence` to match "
                    "what it says now, before generating any claim about this template",
                ))
    return findings
