"""Offline structural checks for the observability module (P-025).

No service required — everything here is static analysis of committed
YAML/JSON: parse validity, and the two classes of "silently never fires /
silently shows no data" bug this module is prone to:

  - An alert rule's PromQL references a metric name nothing actually
    exports. The rule is syntactically valid YAML and looks correct; it
    just never matches anything.
  - A dashboard panel references a datasource uid the provisioning file
    never assigns. Grafana auto-generates a uid on provisioning that will
    not equal the dashboard's hardcoded one, and the panel silently shows
    "Datasource not found" instead of an error anyone notices immediately.

Both classes were found by hand while scoping this module's tests, not by
these tests catching a regression — they are the first line of defence
against the same mistake recurring.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
OBS = REPO / "modules" / "observability"

PROM_DIR = OBS / "prometheus"
GRAFANA_DIR = OBS / "grafana"
LOKI_DIR = OBS / "loki"
EXPORTER_DIR = OBS / "source-health-exporter"


def _yaml_files() -> list[Path]:
    return sorted(OBS.rglob("*.yml")) + sorted(OBS.rglob("*.yaml"))


def _json_files() -> list[Path]:
    return sorted(OBS.rglob("*.json"))


@pytest.mark.parametrize("f", _yaml_files(), ids=lambda p: str(p.relative_to(OBS)))
def test_yaml_files_parse(f: Path) -> None:
    yaml.safe_load(f.read_text(encoding="utf-8"))


@pytest.mark.parametrize("f", _json_files(), ids=lambda p: str(p.relative_to(OBS)))
def test_json_files_parse(f: Path) -> None:
    json.loads(f.read_text(encoding="utf-8"))


def _rule_files() -> list[Path]:
    return sorted((PROM_DIR / "rules").glob("*.yml"))


@pytest.mark.parametrize("f", _rule_files(), ids=lambda p: p.name)
def test_rule_files_have_well_formed_groups(f: Path) -> None:
    """Every alert has the fields Prometheus requires, so a typo in the YAML
    shape fails here instead of silently loading zero rules."""
    doc = yaml.safe_load(f.read_text(encoding="utf-8"))
    assert "groups" in doc and doc["groups"], f"{f.name}: no rule groups"
    for group in doc["groups"]:
        assert group.get("rules"), f"{f.name}: group {group.get('name')!r} has no rules"
        for rule in group["rules"]:
            assert "alert" in rule, f"{f.name}: a rule in {group['name']!r} has no `alert` name"
            assert "expr" in rule, f"{f.name}: {rule.get('alert')} has no `expr`"
            assert "severity" in rule.get("labels", {}), (
                f"{f.name}: {rule['alert']} has no severity label"
            )


# ── Metric-name cross-check ──────────────────────────────────────────────
# What each rule file's alerts are allowed to reference, verified by hand
# against the actual metric source, not assumed:
#   - host/services: node-exporter, DCGM, and prometheus-fastapi-instrumentator's
#     real default metric names, confirmed 2026-09-01 by instantiating the
#     exact `Instrumentator().instrument(app).expose(app)` call main.py uses
#     and reading its real /metrics output — not by reading the library's
#     source, which under-reported what it actually emits.
#   - source-health: every `hcp_*` name is grepped directly out of
#     exporter.py's own metric registration calls below.

KNOWN_METRIC_PREFIXES = {
    # node-exporter (host.rules.yml)
    "node_cpu_seconds_total", "node_memory_MemAvailable_bytes", "node_memory_MemTotal_bytes",
    "node_filesystem_avail_bytes",
    # DCGM (host.rules.yml, gpu group)
    "DCGM_FI_DEV_GPU_TEMP", "DCGM_FI_DEV_GPU_UTIL",
    # prometheus-fastapi-instrumentator defaults (services.rules.yml) — verified
    # empirically 2026-09-01, see the docstring above
    "up", "http_requests_total", "http_request_duration_seconds_bucket",
}


def _exporter_metric_names() -> set[str]:
    """Every `hcp_*` metric name exporter.py actually registers."""
    body = (EXPORTER_DIR / "exporter.py").read_text(encoding="utf-8")
    return set(re.findall(r'"(hcp_[a-z_]+)"', body))


_PROMQL_FUNCTIONS = {
    "rate", "avg", "avg_over_time", "sum", "count", "predict_linear",
    "histogram_quantile", "by", "without", "and", "or", "unless", "on",
    "ignoring", "group_left", "group_right", "offset", "bool", "le",
    "instance",
}


def _metric_names_in_expr(expr: str) -> set[str]:
    """Extract the metric names an expr reads from, ignoring label matcher
    contents (`{source="obs"}` — `source`/`obs` are not metric names) and
    PromQL function/keyword calls."""
    # Label matcher bodies contain identifiers (label names, label values)
    # that look exactly like metric names but are not — strip them first.
    stripped = re.sub(r"\{[^}]*\}", "", expr)
    candidates = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b(?!\s*\()", stripped)
    return {c for c in candidates if c not in _PROMQL_FUNCTIONS and not c.isupper()}


@pytest.mark.parametrize("f", _rule_files(), ids=lambda p: p.name)
def test_alert_expressions_reference_real_metrics(f: Path) -> None:
    """A PromQL expr referencing a metric nothing exports is valid YAML and
    never fires — the exact bug class this test exists to catch."""
    known = KNOWN_METRIC_PREFIXES | _exporter_metric_names()
    doc = yaml.safe_load(f.read_text(encoding="utf-8"))

    for group in doc["groups"]:
        for rule in group["rules"]:
            referenced = _metric_names_in_expr(rule["expr"])
            unknown = [
                m for m in referenced
                if m not in known and not any(m.startswith(k) for k in known)
            ]
            assert not unknown, (
                f"{f.name}: alert {rule['alert']!r} references metric-shaped names "
                f"not in the known set: {unknown}. Either it is a real metric missing "
                f"from KNOWN_METRIC_PREFIXES above, or the alert will never fire."
            )


def test_dashboard_datasource_uids_are_provisioned() -> None:
    """Every uid a dashboard panel references must be pinned in
    datasources.yml, or Grafana's auto-generated uid will not match and the
    panel silently shows 'Datasource not found'."""
    ds_doc = yaml.safe_load(
        (GRAFANA_DIR / "provisioning" / "datasources" / "datasources.yml").read_text()
    )
    provisioned_uids = {ds.get("uid") for ds in ds_doc["datasources"] if ds.get("uid")}
    assert provisioned_uids, (
        "datasources.yml pins no uids at all — every dashboard reference will drift"
    )

    referenced: set[tuple[str, str]] = set()

    def walk(obj) -> None:
        if isinstance(obj, dict):
            ds = obj.get("datasource")
            if isinstance(ds, dict) and "uid" in ds:
                referenced.add((ds["uid"], "?"))
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    for f in (GRAFANA_DIR / "dashboards").glob("*.json"):
        before = len(referenced)
        walk(json.loads(f.read_text()))
        for uid, _ in list(referenced)[before:]:
            referenced.discard((uid, "?"))
            referenced.add((uid, f.name))

    missing = [(uid, fname) for uid, fname in referenced if uid not in provisioned_uids]
    assert not missing, (
        f"dashboard(s) reference a datasource uid never pinned in datasources.yml: {missing}"
    )


def test_alertmanager_routes_reference_real_receivers() -> None:
    """A route naming a receiver that does not exist in `receivers:` is
    accepted by YAML and rejected by Alertmanager at container start —
    catch it offline instead of on a failed `docker compose up`."""
    doc = yaml.safe_load((PROM_DIR / "alertmanager.yml").read_text())
    receiver_names = {r["name"] for r in doc["receivers"]}

    named = {doc["route"]["receiver"]}
    for route in doc["route"].get("routes", []):
        named.add(route["receiver"])

    missing = named - receiver_names
    assert not missing, f"alertmanager.yml routes to undefined receiver(s): {missing}"


def test_prometheus_scrapes_every_rule_file() -> None:
    """A committed rule file Prometheus never loads is dead weight — or
    worse, someone assumes it is active when it is not."""
    prom = yaml.safe_load((PROM_DIR / "prometheus.yml").read_text())
    rule_globs = prom.get("rule_files", [])
    rule_names = {f.name for f in _rule_files()}
    referenced = set()
    for pattern in rule_globs:
        referenced.add(Path(pattern).name)

    # Every committed rule file's name must appear in at least one configured
    # rule_files glob/path.
    for name in rule_names:
        assert any(name == r or name.endswith(r.lstrip("*")) for r in referenced) or any(
            "*" in r for r in rule_globs
        ), f"{name} is committed but prometheus.yml's rule_files does not load it: {rule_globs}"


def test_the_voicemeeter_requirement_names_the_real_distribution() -> None:
    """`voicemeeterlib` is the import name; the PyPI distribution is `voicemeeter-api`.

    The requirements file once said `voicemeeterlib>=0.8`, which pip cannot resolve, so on a
    clean Windows install the collector's import failed and it reported "not installed".
    """
    lines = (EXPORTER_DIR / "requirements.txt").read_text(encoding="utf-8").splitlines()
    names = {
        re.split(r"[<>=!~\[; ]", line.split("#")[0].strip(), maxsplit=1)[0].lower().replace("_", "-")
        for line in lines
        if line.split("#")[0].strip()
    }
    assert "voicemeeterlib" not in names
    assert "voicemeeter-api" in names
