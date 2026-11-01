"""Load the committed dropdown catalog and reject stale asset/reference entries."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import Catalog

MODULE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = MODULE_ROOT / "catalog.yaml"


def load_catalog(path: Path = DEFAULT_CATALOG, module_root: Path = MODULE_ROOT) -> Catalog:
    catalog = Catalog.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    root = module_root.resolve()
    for brand in catalog.brands:
        logo = (root / brand.logo_path).resolve()
        if not logo.is_relative_to(root) or not logo.is_file() or logo.stat().st_size == 0:
            raise ValueError(f"brand logo is missing or outside the module: {brand.id}")
    return catalog


def profile_options(catalog: Catalog) -> list[dict]:
    """Stable JSON-ready options for desktop/mobile profile and logo dropdowns."""
    brands = {item.id: item for item in catalog.brands}
    return [
        {
            "value": profile.id,
            "label": profile.display_name,
            "kind": profile.kind,
            "show_profile_ids": profile.show_profile_ids,
            "default_brand_id": profile.default_brand_id,
            "brands": [
                {
                    "value": brand_id,
                    "label": brands[brand_id].display_name,
                    "logo_path": brands[brand_id].logo_path,
                }
                for brand_id in profile.brand_ids
            ],
        }
        for profile in catalog.profiles
    ]


def provider_options(catalog: Catalog, profile_id: str) -> list[dict]:
    profile = next((item for item in catalog.profiles if item.id == profile_id), None)
    if profile is None:
        raise ValueError("unknown social profile")
    providers = {item.id: item for item in catalog.providers}
    return [
        {
            "value": item.provider_id,
            "label": providers[item.provider_id].display_name,
            "connection_status": providers[item.provider_id].connection_status,
            "capabilities": item.capabilities,
            "default_visibility": item.default_visibility,
            "account_label": item.account_label,
        }
        for item in profile.destinations
    ]
