"""Public-facing drafts may link the public edition, and only files it contains.

`targets.yml` names the Content Creator Platform's public edition with `public_repo`. The private
development repository is still refused, and a link into the public edition has to name a path the
exporter could have published (it exists, and it is outside `private/`).
"""

from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "modules/marketing-crosswalk"
sys.path.insert(0, str(MODULE))

from generator.crosswalk import load, validate  # noqa: E402
from generator.render import PrivateLinkLeak, public_edition_repos, render  # noqa: E402

PUBLIC = "https://github.com/OpenTechnology14/Open_Content_Creator_Platform"
PRIVATE = "https://github.com/OpenTechnology14/Open_Content_Creator_Platform"


def _private_edition() -> bool:
    """The exporter rewrites the private repository's name to the public edition's, so the guards that prove the private
    name is refused only mean something in the private edition. In the public edition they are skipped, not failed."""
    return load(MODULE, ROOT).targets["hybrid-creator-platform"]["repo"].endswith("_Private")


private_edition_only = pytest.mark.skipif(not _private_edition(), reason="public edition: the private repository name is rewritten at export")


def draft_with(text):
    cw = load(MODULE, ROOT)
    subject = deepcopy(cw.subjects["stream-extend"][0])
    subject["what_it_is"] = text
    return cw, subject


@private_edition_only
def test_the_platform_target_names_its_public_edition():
    cw = load(MODULE, ROOT)
    assert public_edition_repos(cw) == {"Open_Content_Creator_Platform": "hybrid-creator-platform"}
    assert cw.targets["hybrid-creator-platform"]["repo"].endswith("_Private")


def test_a_link_to_a_file_the_public_edition_contains_is_allowed():
    cw, subject = draft_with(f"Read {PUBLIC}/blob/main/README.md and {PUBLIC}")
    body = render(cw, "stream-extend", subject, "walkthrough-brief")
    assert f"{PUBLIC}/blob/main/README.md" in body


@private_edition_only
@pytest.mark.parametrize("url", [PRIVATE, f"{PRIVATE}/blob/main/README.md", "https://github.com/OpenTechnology14/Hybrid_Creator_Platform"])
def test_the_private_repository_is_still_refused_under_either_name(url):
    cw, subject = draft_with(f"See {url}")
    with pytest.raises(PrivateLinkLeak):
        render(cw, "stream-extend", subject, "walkthrough-brief")


def test_a_name_that_only_ends_the_same_way_is_not_the_public_edition():
    cw, subject = draft_with("See https://github.com/OpenTechnology14/Platform")
    with pytest.raises(PrivateLinkLeak):
        render(cw, "stream-extend", subject, "walkthrough-brief")


@pytest.mark.parametrize("path", ["docs/does-not-exist.md", "private/release/export-policy.json"])
def test_a_link_to_a_path_the_public_edition_cannot_contain_is_refused(path):
    cw, subject = draft_with(f"See {PUBLIC}/blob/main/{path}")
    with pytest.raises(PrivateLinkLeak, match="does not contain"):
        render(cw, "stream-extend", subject, "walkthrough-brief")


def test_a_public_subjects_own_upstream_is_still_allowed():
    cw = load(MODULE, ROOT)
    subject = deepcopy(cw.subjects["stream-extend"][0])
    subject["visibility"] = "public"
    subject["upstream"] = "OpenTechnology14/job-hunter"
    subject["what_it_is"] = "Source: https://github.com/OpenTechnology14/job-hunter"
    assert "job-hunter" in render(cw, "stream-extend", subject, "walkthrough-brief")


@pytest.mark.parametrize("bad", ["Elsewhere/Open_Content_Creator_Platform", "OpenTechnology14/Open_Content_Creator_Platform"])
def test_validate_rejects_a_public_repo_that_is_not_a_distinct_public_name(bad):
    cw = load(MODULE, ROOT)
    cw.targets["hybrid-creator-platform"]["public_repo"] = bad
    problems = [f for f in validate(cw) if f.where == "targets.yml: hybrid-creator-platform"]
    assert problems and all(f.severity == "error" for f in problems)


def test_the_social_catalog_links_this_repositorys_brands_to_the_public_edition():
    """The catalog's brand `website` is a link a person can open. For the three brands built in this repository it
    must be the public edition: the private repository's slug, old or new, 404s for everyone but its collaborators."""
    import yaml

    brands = yaml.safe_load((ROOT / "modules/social-management/catalog.yaml").read_text(encoding="utf-8"))["brands"]
    own = {b["id"]: b["website"] for b in brands if b["id"] in {"hybrid-platform", "stream-extend", "creator-extend"}}
    assert set(own) == {"hybrid-platform", "stream-extend", "creator-extend"}
    assert set(own.values()) == {PUBLIC}, own
    for brand in brands:
        assert "hybrid-creator-platform" not in brand["website"].lower()
        assert not brand["website"].rstrip("/").endswith("_Private")
