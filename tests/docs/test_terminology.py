"""The project is the Content Creator Platform; the working name it had before is retired.

Owner rule, 2026-11-10: text a person reads says Content Creator, Content Creator Platform or content-creator,
never the earlier working name. Identifiers that merely contain the old spelling are persisted names and stay;
`docs/REPOSITORY_ALIGNMENT.md#names-that-stay` lists them and says why.

What this bans, in the **contents** of every text file the repository holds (file names are not scanned): the
capitalised word "Hybrid" (also all capitals), and "hybrid creator" or "hybrid platform" in any case, even when a
line break splits the phrase. What it leaves alone: one-token identifiers (`HybridCreatorPlatform`,
`hybrid-creator-platform`, `Hybrid_Creator_Platform`), the lower-case word on its own, the phrases in
TECHNICAL_SENSE, and, in the two files in TTS_OPTION_FILES, the bare word that labels the hybrid-TTS option.

Dated log entries are the one exception: under a heading dated before the 2026-11-10 rename, in a file listed in DATED_LOGS,
the wording the entry was written with stays (owner decision 2026-11-12).

Offline and read-only.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SELF = "tests/docs/test_terminology.py"
MAX_BYTES = 2_000_000

# The word in its technical sense (local plus cloud), not the project's name. Whole words only.
TECHNICAL_SENSE = re.compile(r"\bHybrid (?:TTS|Networking|Stack)\b")

# Files where the bare word labels one decision's option, "Hybrid" against "fully local" for text-to-speech
# (P-068 D1, CT-D04). The phrase rule still applies there, so the old display name cannot hide in them.
TTS_OPTION_FILES = {
    "docs/proposals/PROPOSAL_LOCAL_TTS_STACK.md",
    "docs/todo/CONTENT_CREATE_TODO.md",
}

# Logs of dated entries. An entry under a heading dated before the rename keeps the wording it was written with
# (owner decision 2026-11-12: leave dated historical records as written). Entries dated on or after CUTOFF are
# checked like any other text, so a new entry cannot reintroduce the old name.
DATED_LOGS = {"docs/proposals/PROPOSAL_DOCUMENT_GAPS.md"}
CUTOFF = "2026-11-10"
DATED_HEADING = re.compile(r"^#{2,6} .*?(\d{4}-\d{2}-\d{2})\s*$")

WORD = re.compile(r"\b(?:Hybrid|HYBRID)\b")
PHRASE = re.compile(r"hybrid\s+(?:creator|platform)\b", re.IGNORECASE)


def tracked_text_files() -> list[str]:
    """Tracked files plus new untracked ones that are not ignored, so a local run sees a file before it is committed."""
    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=REPO, check=True, capture_output=True,
    ).stdout.decode("utf-8")
    return sorted(set(p for p in out.split("\0") if p))


def dated_before_cutoff(text: str) -> set[int]:
    """Line numbers under a heading whose date is before CUTOFF; any other heading ends the section."""
    exempt, current, in_fence = set(), None, False
    for number, line in enumerate(text.split("\n"), start=1):
        if line.startswith("```"):
            in_fence = not in_fence  # a "# comment" inside a fenced block is not a heading
        elif not in_fence and re.match(r"#{1,6} ", line):
            match = DATED_HEADING.match(line)
            current = match.group(1) if match else None
        if current is not None and current < CUTOFF:
            exempt.add(number)
    return exempt


def violations(text: str, allow_bare_word: bool = False, dated_log: bool = False) -> list[tuple[int, str]]:
    """Return (line number, line) for each use of the retired display name."""
    masked = TECHNICAL_SENSE.sub(lambda m: "·" * len(m.group(0)), text)  # same length, so lines still line up
    original = text.split("\n")
    hits: dict[int, str] = {}
    if not allow_bare_word:
        for number, line in enumerate(masked.split("\n"), start=1):
            if WORD.search(line):
                hits[number] = original[number - 1].strip()
    for match in PHRASE.finditer(masked):
        number = masked.count("\n", 0, match.start()) + 1
        hits.setdefault(number, original[number - 1].strip())
    exempt = dated_before_cutoff(text) if dated_log else set()
    return sorted((n, line) for n, line in hits.items() if n not in exempt)


def scan_repo() -> dict[str, list[tuple[int, str]]]:
    found: dict[str, list[tuple[int, str]]] = {}
    for relative in tracked_text_files():
        path = REPO / relative
        if relative == SELF or not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_BYTES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # a binary file
        hits = violations(text, allow_bare_word=relative in TTS_OPTION_FILES, dated_log=relative in DATED_LOGS)
        if hits:
            found[relative] = hits
    return found


def test_no_file_uses_the_retired_display_name():
    found = scan_repo()
    detail = "\n".join(f"  {path}:{n}: {line[:110]}" for path, hits in found.items() for n, line in hits[:3])
    assert not found, (
        "The project is the Content Creator Platform; the old working name is retired as a display name.\n"
        "Rename the words below, or, if one is a persisted identifier, see docs/REPOSITORY_ALIGNMENT.md#names-that-stay.\n" + detail
    )


@pytest.mark.parametrize("relative", sorted(TTS_OPTION_FILES))
def test_each_file_with_the_tts_option_label_still_exists_and_uses_it(relative):
    path = REPO / relative
    assert path.is_file(), f"{relative} moved or went: update TTS_OPTION_FILES"
    assert WORD.search(path.read_text(encoding="utf-8")), f"{relative} no longer uses the bare word: drop it from TTS_OPTION_FILES"


@pytest.mark.parametrize(
    "text, hit",
    [
        ("The Hybrid Creator Platform repository", True),
        ("Hybrid's own vocabularies stay as they are", True),
        ("adds a shortcut under Start → Hybrid Creator\nPlatform", True),
        ("select Hybrid Platform or MyFeed", True),
        ("the hybrid platform", True),
        ("the Hybrid-platform brand", True),
        ("HYBRID repo", True),
        ("HybridCreatorPlatform/module-setup", False),
        ("docker network inspect hybrid-creator-platform_hcp-net", False),
        ("renamed from Hybrid_Creator_Platform", False),
        ("Hybrid TTS: your own voice locally, Games on ElevenLabs", False),
        ("Operations — Hybrid Networking", False),
        ("## Full Hybrid Stack Architecture", False),
        ("confirm the hybrid strategy", False),
        ("Content Creator Platform", False),
    ],
)
def test_the_scanner_separates_the_name_from_identifiers_and_technical_use(text, hit):
    assert bool(violations(text)) is hit


@pytest.mark.parametrize("relative", sorted(DATED_LOGS))
def test_each_dated_log_exists_and_still_needs_its_allowance(relative):
    path = REPO / relative
    assert path.is_file(), f"{relative} moved or went: update DATED_LOGS"
    assert violations(path.read_text(encoding="utf-8")), f"{relative} no longer holds the old wording: drop it from DATED_LOGS"


def test_a_dated_entry_before_the_cutoff_keeps_its_wording_and_a_later_one_does_not():
    log = "### Selector — 2026-10-12\nThe Hybrid queue.\n\n### Selector — 2026-11-10\nThe Hybrid queue.\n\n### Selector — 2026-11-12\nThe Hybrid queue.\n"
    assert [n for n, _ in violations(log)] == [2, 5, 8]
    assert [n for n, _ in violations(log, dated_log=True)] == [5, 8]


def test_an_undated_heading_ends_the_dated_section_and_the_heading_itself_is_covered():
    log = "### Old entry — 2026-10-12\nHybrid.\n### Summary\nHybrid.\n"
    assert [n for n, _ in violations(log, dated_log=True)] == [4]
    assert [n for n, _ in violations("### Hybrid Platform — 2026-10-12\n", dated_log=True)] == []


def test_a_shell_comment_in_a_fenced_block_does_not_end_the_dated_section():
    log = "### Old entry — 2026-10-12\n```bash\n# build the thing\nmake\n```\nThe Hybrid queue.\n"
    assert [n for n, _ in violations(log, dated_log=True)] == []
    assert [n for n, _ in violations(log)] == [6]


def test_the_allowance_only_applies_to_the_listed_logs():
    assert violations("### Selector — 2026-10-12\nThe Hybrid queue.\n", dated_log=False)


def test_a_technical_phrase_does_not_hide_the_name_on_the_same_line():
    assert violations("Hybrid TTS for the Hybrid repo")
    assert violations("Hybrid Networking and the Hybrid Platform")


def test_the_tts_option_allowance_covers_the_bare_word_only():
    assert not violations("Hybrid. Fully local means voice-acting three registers", allow_bare_word=True)
    assert violations("the Hybrid Creator Platform", allow_bare_word=True)
    assert violations("hybrid platform", allow_bare_word=True)
    assert violations("Hybrid. Fully local means voice-acting three registers")


def test_the_record_of_names_that_stay_exists_and_lists_each_identifier_class():
    record = (REPO / "docs/REPOSITORY_ALIGNMENT.md").read_text(encoding="utf-8")
    assert "## Names that stay" in record
    for identifier in ("HybridCreatorPlatform", "hybrid-creator-platform_hcp-net", "HCP_*", "com.hybridcreator.extend.preview", "Dated historical records"):
        assert identifier in record, f"the record of names that stay omits {identifier}"
