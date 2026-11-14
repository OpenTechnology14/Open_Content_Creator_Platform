"""The wireframe set says only what the code says, and shows only what the app shows.

Every click path under `marketing/content-creator-wireframe/` cites the real component, function or command it describes,
and every picture in the set is a real screenshot of the running app. This re-reads both promises.

* **Code references.** A link into a repository file with a line anchor,
  `[Check readiness](../../apps/shared/ui/ModuleSetup.svelte#L533)`, must resolve to a tracked file, and its link text (the
  label a person sees, or the function or command name, with emphasis marks stripped) must occur **on the anchored lines**.
  A label wrapped onto a second line needs both lines anchored: `#L10-L11`. Every other relative link must resolve.
* **Screenshots are never reconstructed.** The set holds no mermaid, no ASCII-art diagram, no SVG and no image except a
  PNG or JPG under `screenshots/`. Where a screen belongs, a click path carries a placeholder:

      *Caption:* <what the screenshot must show>
      [screenshot: marketing/content-creator-wireframe/screenshots/<feature>/step-NN.png]

  The path names the feature's own folder, numbers run 01, 02, 03 … with no gaps in reading order, each placeholder has a
  caption of at most 25 words directly above it, and every `## Path` section has at least one. Each feature's `visual.md`
  is the index of those placeholders: one row each, same order, same caption, with a capture note. Once a file exists, its
  placeholder must become an image embed `![Caption](...)`, and an embed must point at a real file under `screenshots/`.
* **Shape.** Each feature folder holds exactly `click-paths.md` and `visual.md`; the README and the overview link to every
  feature's click paths; every `## Path` section cites the code at least once.

Offline and read-only. Line numbers drift whenever someone edits the cited files, so this fails on a drifted anchor and
there is a one-command repair that moves each anchor to where its label now is:

    python tests/docs/test_wireframe_refs.py --fix

It rewrites only anchors whose label still exists in the file (nearest occurrence, within 400 lines); a label that is gone
or renamed needs a person, who updates the document, not the test.
"""
from __future__ import annotations

import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SET = REPO / "marketing" / "content-creator-wireframe"
SET_REL = "marketing/content-creator-wireframe"
FIX_RANGE = 400  # how far --fix looks for a label that moved
CAPTION_WORDS = 25

TEXT = r"(?:[^\[\]\n]|\[[^\[\]\n]*\])+"  # link text, allowing one level of square brackets, as in a label like ['png', 'jpg']
LINK = re.compile(rf"\[({TEXT})\]\(([^)\s#]+)#L(\d+)(?:-L?(\d+))?\)")
ANY_LINK = re.compile(rf"(?<!!)\[(?:{TEXT})?\]\(([^)\s]+)\)")
IMAGE = re.compile(r"!\[([^\]\n]*)\]\(([^)\s]+)\)")
PLACEHOLDER = re.compile(r"^[ \t]*\[screenshot: ([^\]\s]+)\][ \t]*$")
PLACEHOLDER_ANY = re.compile(r"\[screenshot:[^\]]*\]")
CAPTION = re.compile(r"^[ \t]*\*Caption:\*[ \t]+(\S.*?)[ \t]*$")
PLACEHOLDER_PATH = re.compile(rf"^{re.escape(SET_REL)}/screenshots/([a-z0-9-]+)/step-(\d\d)\.(png|jpg)$")
INDEX_ROW = re.compile(r"^\|[ \t]*`([^`]+)`[ \t]*\|[ \t]*(Path \d+)[ \t]*\|[ \t]*(.+?)[ \t]*\|[ \t]*(.+?)[ \t]*\|[ \t]*$")
DRAWING = re.compile(r"```mermaid|<svg|data:image|[┌┐└┘│─├┤┬┴┼]")
FIX_HINT = "if the code moved, run: python tests/docs/test_wireframe_refs.py --fix"


def without_code(text: str) -> str:
    """The text with fenced blocks and inline code spans removed, so a documented example is not mistaken for a real embed."""
    return re.sub(r"`[^`\n]*`", "", re.sub(r"```.*?```", "", text, flags=re.S))


@lru_cache(maxsize=1)
def tracked_files() -> tuple[str, ...]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, check=True, capture_output=True).stdout.decode("utf-8")
    return tuple(sorted(p for p in out.split("\0") if p))


@lru_cache(maxsize=None)
def lines_of(relative: str) -> tuple[str, ...]:
    return tuple((REPO / relative).read_text(encoding="utf-8", errors="replace").split("\n"))


def window(relative: str, start: int, end: int) -> str:
    return "\n".join(lines_of(relative)[start - 1 : end])


def plain(text: str) -> str:
    return text.replace("*", "").replace("`", "").strip()


def contains_label(haystack: str, label: str) -> bool:
    """Whole-word match for plain words and phrases (so "Back" does not match "callback"); substring for code-like labels."""
    if re.fullmatch(r"[A-Za-z0-9 ]+", label):
        return re.search(rf"(?<![A-Za-z0-9]){re.escape(label)}(?![A-Za-z0-9])", haystack) is not None
    return label in haystack


def markdown_files() -> list[Path]:
    return sorted(SET.rglob("*.md")) if SET.exists() else []


def feature_dirs() -> list[Path]:
    return sorted(p for p in (SET / "features").glob("*") if p.is_dir()) if SET.exists() else []


def check_link(doc: Path, text: str, href: str, start: int, end: int) -> str | None:
    target = (doc.parent / href).resolve()
    try:
        relative = target.relative_to(REPO).as_posix()
    except ValueError:
        return f"{href} leaves the repository"
    if relative not in tracked_files():
        return f"{relative} is not a tracked repository file (git add it, or fix the path)"
    n = len(lines_of(relative))
    if end > n or start > end:
        return f"{relative}#L{start}-L{end}: the file has {n} lines"
    if not contains_label(window(relative, start, end), plain(text)):
        return f"{relative}#L{start}-L{end} does not contain {plain(text)!r}"
    return None


# ── repair ─────────────────────────────────────────────────────────────────────────────────────────────────────────

def locate(relative: str, anchor: str, near: int) -> int | None:
    """The line nearest `near` that contains `anchor`, within FIX_RANGE lines, else None."""
    hits = [i for i, line in enumerate(lines_of(relative), start=1) if contains_label(line, anchor)]
    if not hits:
        return None
    best = min(hits, key=lambda i: (abs(i - near), i))
    return best if abs(best - near) <= FIX_RANGE else None


def fix_text(doc: Path, text: str) -> tuple[str, list[str]]:
    """Move each failing anchor to where its label now is. Returns the new text and what could not be moved."""
    unresolved: list[str] = []

    def fix_link(m: re.Match) -> str:
        label, href, start, end = m.group(1), m.group(2), int(m.group(3)), int(m.group(4) or m.group(3))
        problem = check_link(doc, label, href, start, end)
        if problem is None:
            return m.group(0)
        try:
            rel = (doc.parent / href).resolve().relative_to(REPO).as_posix()
        except ValueError:
            unresolved.append(problem)
            return m.group(0)
        new = locate(rel, plain(label), start) if rel in tracked_files() else None
        if new is None:
            unresolved.append(problem)
            return m.group(0)
        anchor = f"#L{new}" if end == start else f"#L{new}-L{new + (end - start)}"
        return f"[{label}]({href}{anchor})"

    return LINK.sub(fix_link, text), unresolved


# ── screenshot placeholders ────────────────────────────────────────────────────────────────────────────────────────

def placeholders_in(text: str) -> list[dict]:
    """Each `[screenshot: path]` line in reading order, with its caption (or None) and the `## ` section it sits in."""
    lines = text.split("\n")
    section, found = "", []
    for i, line in enumerate(lines):
        if line.startswith("## "):
            section = line[3:].strip()
        match = PLACEHOLDER.match(line)
        if match:
            previous = next((lines[k] for k in range(i - 1, -1, -1) if lines[k].strip()), "")
            caption = CAPTION.match(previous)
            found.append({"line": i + 1, "path": match.group(1), "caption": caption.group(1) if caption else None, "section": section})
    return found


def placeholder_problems(folder: str, text: str) -> list[str]:
    found, problems = placeholders_in(text), []
    stray = len(PLACEHOLDER_ANY.findall(text)) - len(found)
    if stray:
        problems.append(f"{stray} `[screenshot: ...]` marker(s) are not on a line of their own or have a malformed path")
    for n, item in enumerate(found, start=1):
        match = PLACEHOLDER_PATH.match(item["path"])
        if not match:
            problems.append(f"line {item['line']}: {item['path']!r} is not {SET_REL}/screenshots/{folder}/step-NN.png")
            continue
        if match.group(1) != folder:
            problems.append(f"line {item['line']}: {item['path']} names feature {match.group(1)!r}, this folder is {folder!r}")
        if int(match.group(2)) != n:
            problems.append(f"line {item['line']}: expected step-{n:02d}, found step-{match.group(2)} (numbers run 01, 02, … with no gaps)")
        if not item["caption"]:
            problems.append(f"line {item['line']}: no `*Caption:*` line directly above the placeholder")
        elif len(item["caption"].split()) > CAPTION_WORDS:
            problems.append(f"line {item['line']}: the caption is over {CAPTION_WORDS} words")
    sections = [s for s in re.split(r"(?m)^## ", text)[1:] if s.startswith("Path ")]
    problems += [f"'{s.splitlines()[0]}' has no screenshot placeholder" for s in sections if not any(PLACEHOLDER.match(line) for line in s.splitlines())]
    return problems


def index_rows(text: str) -> list[tuple[str, str, str, str]]:
    return [m.groups() for m in map(INDEX_ROW.match, text.split("\n")) if m]


def index_problems(folder: str, click_text: str, index_text: str) -> list[str]:
    found, rows, problems = placeholders_in(click_text), index_rows(index_text), []
    if not re.search(r"(?m)^> \*\*Status:\*\*", index_text):
        problems.append("visual.md has no '> **Status:**' line")
    if len(rows) != len(found):
        problems.append(f"the index has {len(rows)} row(s), click-paths.md has {len(found)} placeholder(s)")
    for n, (item, row) in enumerate(zip(found, rows), start=1):
        file, path_label, caption, note = row
        expected = item["path"].removeprefix(SET_REL + "/")
        if file != expected:
            problems.append(f"row {n}: file {file!r}, expected {expected!r}")
        number = re.match(r"Path (\d+)", item["section"])
        if not number or path_label != f"Path {number.group(1)}":
            problems.append(f"row {n}: path column {path_label!r} does not match the section {item['section']!r}")
        if caption != item["caption"]:
            problems.append(f"row {n}: caption differs from click-paths.md")
        if not note.strip():
            problems.append(f"row {n}: no capture note")
    return problems


# ── the tests ──────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_set_exists():
    assert (SET / "README.md").is_file() and (SET / "overview.md").is_file() and feature_dirs(), "marketing/content-creator-wireframe is incomplete"


@pytest.mark.parametrize("doc", markdown_files(), ids=lambda p: p.relative_to(SET).as_posix())
def test_every_line_linked_citation_still_matches_the_code(doc):
    problems = []
    for text, href, start, end in LINK.findall(doc.read_text(encoding="utf-8")):
        if href.startswith(("http://", "https://")):
            continue
        problem = check_link(doc, text, href, int(start), int(end or start))
        if problem:
            problems.append(problem)
    assert not problems, f"{doc.relative_to(REPO)} ({FIX_HINT}):\n  " + "\n  ".join(problems)


@pytest.mark.parametrize("doc", markdown_files(), ids=lambda p: p.relative_to(SET).as_posix())
def test_no_line_anchored_link_escapes_the_checker(doc):
    """The checker must see every `](path#Lnn)` anchor; a regex blind spot would let a citation drift unnoticed."""
    text = doc.read_text(encoding="utf-8")
    anchors = len(re.findall(r"\]\([^)\s#]+#L\d+", text))
    assert anchors == len(LINK.findall(text)), f"{doc.relative_to(REPO)}: {anchors} anchored links, the checker matched {len(LINK.findall(text))}"


@pytest.mark.parametrize("doc", markdown_files(), ids=lambda p: p.relative_to(SET).as_posix())
def test_every_relative_link_resolves(doc):
    broken = []
    for href in ANY_LINK.findall(doc.read_text(encoding="utf-8")):
        if href.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if not (doc.parent / href.split("#")[0]).resolve().exists():
            broken.append(href)
    assert not broken, f"{doc.relative_to(REPO)} links to missing: {broken}"


@pytest.mark.parametrize("doc", [d for d in markdown_files() if d.name == "click-paths.md"], ids=lambda p: p.parent.name)
def test_every_path_cites_the_code(doc):
    sections = re.split(r"(?m)^## ", doc.read_text(encoding="utf-8"))[1:]
    paths = [s for s in sections if s.startswith("Path ")]
    assert paths, f"{doc.relative_to(REPO)} has no '## Path' section"
    bare = [s.splitlines()[0] for s in paths if not LINK.search(s)]
    assert not bare, f"{doc.relative_to(REPO)}: these paths cite no line-anchored link: {bare}"


@pytest.mark.parametrize("doc", [d for d in markdown_files() if d.name == "click-paths.md"], ids=lambda p: p.parent.name)
def test_every_click_path_carries_well_formed_screenshot_placeholders(doc):
    problems = placeholder_problems(doc.parent.name, doc.read_text(encoding="utf-8"))
    assert not problems, f"{doc.relative_to(REPO)}:\n  " + "\n  ".join(problems)


@pytest.mark.parametrize("folder", feature_dirs(), ids=lambda p: p.name)
def test_each_visual_index_matches_its_click_paths(folder):
    problems = index_problems(folder.name, (folder / "click-paths.md").read_text(encoding="utf-8"), (folder / "visual.md").read_text(encoding="utf-8"))
    assert not problems, f"{(folder / 'visual.md').relative_to(REPO)}:\n  " + "\n  ".join(problems)


def test_the_set_holds_no_reconstructed_visuals():
    """The owner's rule: screens are real screenshots of the running app, never drawn."""
    def scanned(doc: Path) -> str:
        text = doc.read_text(encoding="utf-8")
        # the README's layout tree is a plain fenced block of box-drawing characters; a mermaid fence is never plain
        return re.sub(r"```\n.*?```", "", text, flags=re.S) if doc.name == "README.md" else text

    offenders = [f"{d.relative_to(REPO)}: {m.group(0)!r}" for d in markdown_files() for m in [DRAWING.search(scanned(d))] if m]
    stray = [p.relative_to(REPO).as_posix() for p in SET.rglob("*")
             if p.is_file() and p.suffix != ".md" and not (p.relative_to(SET).parts[0] == "screenshots" and p.suffix.lower() in {".png", ".jpg", ".jpeg"})]
    assert not offenders and not stray, f"drawings or stray files in the wireframe set: {offenders + stray}"


def test_a_captured_screenshot_replaces_its_placeholder_with_an_embed():
    problems = []
    for doc in markdown_files():
        text = doc.read_text(encoding="utf-8")
        for item in placeholders_in(text):
            if (REPO / item["path"]).exists():
                problems.append(f"{doc.relative_to(REPO)}:{item['line']}: {item['path']} exists; replace the placeholder with an image embed")
        for alt, href in IMAGE.findall(without_code(text)):
            target = (doc.parent / href).resolve()
            if not target.is_file() or SET / "screenshots" not in target.parents:
                problems.append(f"{doc.relative_to(REPO)}: image {href} is not a file under screenshots/")
    shots = SET / "screenshots"
    if shots.exists():
        embedded = {(d.parent / h).resolve() for d in markdown_files() for _a, h in IMAGE.findall(without_code(d.read_text(encoding="utf-8")))}
        problems += [f"{p.relative_to(REPO)} is not embedded anywhere" for p in shots.rglob("*") if p.is_file() and p.resolve() not in embedded]
    assert not problems, "\n  ".join(problems)


def linked(doc: Path) -> set[str]:
    return {href.split("#")[0] for href in ANY_LINK.findall(doc.read_text(encoding="utf-8"))}


@pytest.mark.parametrize("folder", feature_dirs(), ids=lambda p: p.name)
def test_each_feature_folder_has_exactly_the_two_documents_and_is_linked_from_both_indexes(folder):
    assert sorted(p.name for p in folder.iterdir()) == ["click-paths.md", "visual.md"]
    target = f"features/{folder.name}/click-paths.md"
    assert target in linked(SET / "README.md"), f"README.md does not link {target}"
    assert target in linked(SET / "overview.md"), f"overview.md does not link {target}"


# ── the checkers themselves, so a regression in them cannot pass silently ─────────────────────────────────────────

GOOD = "apps/shared/ui/ModuleSetup.svelte"
P = f"{SET_REL}/screenshots/demo/step-%02d.png"


def line_of(needle: str, path: str = GOOD) -> int:
    return next(i for i, line in enumerate(lines_of(path), start=1) if needle in line and "<button" in line)


def sample(*steps: int, caption: str = "The panel after the click.") -> str:
    body = "\n".join(f"1. A step.\n   *Caption:* {caption}\n   [screenshot: {P % n}]\n" for n in steps)
    return f"# Demo — click paths\n\n## Path 1 — One\n\n{body}"


def test_the_link_checker_accepts_a_true_link_and_rejects_the_wrong_label_the_wrong_line_and_a_missing_file():
    doc, start = SET / "README.md", line_of("Check readiness")
    assert check_link(doc, "**Check readiness**", f"../../{GOOD}", start, start) is None
    assert "does not contain" in (check_link(doc, "Check everything", f"../../{GOOD}", start, start) or "")
    assert "does not contain" in (check_link(doc, "Check readiness", f"../../{GOOD}", start + 1, start + 1) or "")
    assert "not a tracked repository file" in (check_link(doc, "x", "../../apps/shared/ui/NoSuchFile.svelte", 1, 1) or "")
    assert "leaves the repository" in (check_link(doc, "x", "../../../../../etc/hosts", 1, 1) or "")


def test_link_text_may_contain_square_brackets():
    text = "[`extensions: ['png', 'jpg']`](../../apps/x.svelte#L3) and [plain](../../apps/y.svelte#L4)"
    assert [m[0] for m in LINK.findall(text)] == ["`extensions: ['png', 'jpg']`", "plain"]
    assert len(ANY_LINK.findall(text)) == 2


def test_plain_word_labels_match_whole_words_only():
    assert contains_label("<label>Back</label>", "Back") and not contains_label("function callback()", "Back")
    assert contains_label("}, 1500);", "1500") and not contains_label("}, 15000);", "1500")
    assert contains_label("const x = ['a', 'b'];", "['a', 'b']")


def test_a_label_wrapped_onto_a_second_line_needs_both_lines_anchored():
    doc, first = SET / "README.md", line_of("Check readiness")
    assert check_link(doc, "Check readiness", f"../../{GOOD}", first, first + 1) is None


def test_fix_moves_a_drifted_anchor_and_reports_a_label_that_is_gone():
    doc, start = SET / "README.md", line_of("Check readiness")
    fixed, unresolved = fix_text(doc, f"see [Check readiness](../../{GOOD}#L{start + 2}) here")
    assert not unresolved and f"#L{start})" in fixed
    gone = f"[A label nobody wrote](../../{GOOD}#L{start})"
    still, unresolved = fix_text(doc, gone)
    assert still == gone and unresolved and "does not contain" in unresolved[0]


def test_the_placeholder_checker_accepts_a_well_formed_file_and_rejects_every_malformed_one():
    assert placeholder_problems("demo", sample(1, 2, 3)) == []
    assert any("expected step-02" in p for p in placeholder_problems("demo", sample(1, 3)))
    assert any("expected step-01" in p for p in placeholder_problems("demo", sample(2)))
    assert any("names feature" in p for p in placeholder_problems("other", sample(1)))
    assert any("not " + SET_REL in p for p in placeholder_problems("demo", sample(1).replace("step-01.png", "one.png")))
    assert any("no `*Caption:*`" in p for p in placeholder_problems("demo", sample(1).replace("*Caption:*", "Note:")))
    assert any("over 25 words" in p for p in placeholder_problems("demo", sample(1, caption=" ".join(["word"] * 26))))
    assert any("no screenshot placeholder" in p for p in placeholder_problems("demo", sample(1) + "\n## Path 2 — Two\n\n1. Another step.\n"))
    assert any("not on a line of their own" in p for p in placeholder_problems("demo", sample(1) + "\ninline [screenshot: x] marker\n"))


def test_the_index_checker_accepts_a_matching_index_and_rejects_drift():
    click = sample(1, 2)
    row = "| `screenshots/demo/step-%02d.png` | Path 1 | The panel after the click. | Open the panel first. |"
    good = "# Demo — screenshot index\n\n> **Status:** Placeholders only.\n\n| File | Path | Caption | Capture note |\n|---|---|---|---|\n" + row % 1 + "\n" + row % 2 + "\n"
    assert index_problems("demo", click, good) == []
    assert any("1 row(s)" in p for p in index_problems("demo", click, good.replace(row % 2 + "\n", "")))
    assert any("caption differs" in p for p in index_problems("demo", click, good.replace("The panel after the click.", "Something else.", 1)))
    assert any("expected 'screenshots/demo/step-02.png'" in p for p in index_problems("demo", click, good.replace("step-02", "step-09")))
    assert any("no capture note" in p or "row 1" in p for p in index_problems("demo", click, good.replace("Open the panel first.", " ", 1)))
    assert any("no '> **Status:**'" in p for p in index_problems("demo", click, good.replace("> **Status:**", "Status")))
    assert any("does not match the section" in p for p in index_problems("demo", click, good.replace("Path 1", "Path 7", 1)))


def test_a_documented_embed_example_is_not_mistaken_for_a_real_embed():
    assert IMAGE.findall("Replace it with `![Caption](path/step-01.png)` once captured.") != []
    assert IMAGE.findall(without_code("Replace it with `![Caption](path/step-01.png)` once captured.")) == []
    assert IMAGE.findall(without_code("![Caption](../../screenshots/x/step-01.png)")) != []


def test_the_drawing_detector_catches_mermaid_svg_and_box_drawing():
    for sample_text in ("```mermaid\nflowchart TD\n```", "<svg width='1'></svg>", "data:image/png;base64,AAAA", "┌──┐\n│ x │\n└──┘"):
        assert DRAWING.search(sample_text), sample_text
    assert not DRAWING.search("A plain sentence with an arrow → and a pipe | in a table.")


if __name__ == "__main__":
    if "--fix" not in sys.argv:
        raise SystemExit("usage: python tests/docs/test_wireframe_refs.py --fix")
    stuck = 0
    for document in markdown_files():
        original = document.read_text(encoding="utf-8")
        updated, unresolved = fix_text(document, original)
        if updated != original:
            document.write_text(updated, encoding="utf-8")
            print(f"re-anchored {document.relative_to(REPO)}")
        for problem in unresolved:
            stuck += 1
            print(f"needs a person: {document.relative_to(REPO)}: {problem}")
    print("done" if not stuck else f"{stuck} anchor(s) need a person")
    raise SystemExit(1 if stuck else 0)
