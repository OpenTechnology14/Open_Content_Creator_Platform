"""Walkthrough drafts retain evidence and cannot bypass public-claim boundaries."""

from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "modules/marketing-crosswalk"
sys.path.insert(0, str(MODULE))

from generator.crosswalk import load  # noqa: E402
from generator.render import PrivateLinkLeak, render  # noqa: E402


@pytest.mark.parametrize("module", ["stream-extend", "content-extend", "task-management"])
def test_unfinished_subjects_produce_preparation_not_demonstration_claims(module):
    cw = load(MODULE, ROOT)
    for original in cw.subjects[module]:
        subject = deepcopy(original)
        subject["status"] = "scaffolded"
        body = render(cw, module, subject, "walkthrough-brief")
        assert "Status: **scaffolded**" in body
        assert "No demonstration, recording or publication is established" in body
        assert subject["status_evidence"]["file"] in body
        assert "Not demonstrated" in body
        assert "_TODO" in body
        assert "{{" not in body
        assert original["status"] == cw.subject(module, original["id"])["status"]


def test_walkthrough_source_text_cannot_leak_private_repo_links():
    cw = load(MODULE, ROOT)
    subject = deepcopy(cw.subjects["stream-extend"][0])
    subject["what_it_is"] = "See https://github.com/OpenTechnology14/Open_Content_Creator_Platform"
    with pytest.raises(PrivateLinkLeak):
        render(cw, "stream-extend", subject, "walkthrough-brief")
