import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from conftest import ROOT
from pincite import cli, guard, lint

# ------------------------------------------------------------------ guard


def test_denylist_matches_normalized_variants(monkeypatch):
    monkeypatch.setenv("PINCITE_DENYLIST", "acme corp\nwidgetco")
    terms = guard.load_denylist(None)
    text = "Acme_Corp filed.\nSee AcmeCorp v. X.\nWidgetCo LLC\nacme corporate is fine? no\nclean line"
    hits = guard.scan_text(text, "f.md", terms)
    assert [h.line for h in hits if h.code == "DENYLIST"] == [1, 2, 3, 4]


def test_builtin_patterns_need_no_secrets():
    text = "\n".join(
        [
            "Case No. 1:23-cv-04567 is pending.",  # synthetic leak sample. pincite-guard: allow
            "Produced at ABC0001234.",  # synthetic leak sample. pincite-guard: allow
            "HIGHLY CONFIDENTIAL — subject to protective order",  # synthetic leak sample. pincite-guard: allow
            "Open Report Draft - Matter - 2026.08.17.docx first.",  # synthetic leak sample. pincite-guard: allow
            "Saved under /Users/someone/Documents/case.",  # synthetic leak sample. pincite-guard: allow
            "Write to person@lawfirm.com or noreply@github.com.",  # synthetic leak sample. pincite-guard: allow
            "Ordinary text with 2019 data and Section-3-Cheat-Sheet.pdf.",
            "Allowed line person@lawfirm.com  pincite-guard: allow",
        ]
    )
    codes = [(h.line, h.code) for h in guard.scan_text(text, "f.md", [])]
    assert codes == [
        (1, "CASE-NUMBER"),
        (2, "BATES"),
        (3, "PROTECTIVE-ORDER"),
        (4, "DATED-DRAFT"),
        (5, "HOME-PATH"),
        (6, "EMAIL"),
    ]


def test_masked_output_never_echoes_the_term(tmp_path, monkeypatch, capsys):
    f = tmp_path / "leak.md"
    f.write_text("A note about Acme Corp.\n")
    monkeypatch.setenv("PINCITE_DENYLIST", "acme corp")
    assert guard.main([str(f), "--mask", "--denylist", str(tmp_path / "none")]) == 1
    out = capsys.readouterr().out
    assert "acme" not in out.lower() and "a*** c***" in out


def test_require_denylist(tmp_path, monkeypatch):
    monkeypatch.delenv("PINCITE_DENYLIST", raising=False)
    clean = tmp_path / "ok.md"
    clean.write_text("nothing here\n")
    assert guard.main([str(clean), "--denylist", str(tmp_path / "none")]) == 0
    assert guard.main([str(clean), "--denylist", str(tmp_path / "none"), "--require-denylist"]) == 2


def test_repository_is_clean_under_builtin_patterns():
    files = [
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and ".git" not in p.parts
        and "tests" not in p.parts
        and p.suffix in {".md", ".py", ".json", ".toml", ".yml", ".yaml", ".txt"}
    ]
    hits = [h for p in files for h in guard.scan_text(p.read_text(encoding="utf-8"), str(p), [])]
    assert hits == [], [h.render(False) for h in hits]


# ------------------------------------------------------------------- lint


def test_repository_lints_clean():
    issues = lint.lint(ROOT)
    assert [str(i) for i in issues if i.level == "error"] == []


def test_lint_catches_broken_skill_and_drift(tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(ROOT / "plugins", root / "plugins")
    shutil.copytree(ROOT / ".claude-plugin", root / ".claude-plugin")
    shutil.copytree(ROOT / "tools", root / "tools")
    shutil.copytree(ROOT / "src", root / "src")
    skill = root / "plugins/cheat-sheets/skills/prep-sheet/SKILL.md"
    skill.write_text(
        skill.read_text().replace("name: prep-sheet", "name: Prep_Sheet") + "\nSee `references/missing.md`.\n"
    )
    (root / "plugins/cheat-sheets/skills/cheat-sheet/scripts/pincheck.py").write_text("# drifted\n")
    mp = json.loads((root / ".claude-plugin/marketplace.json").read_text())
    mp["plugins"][0]["source"] = "./../elsewhere"
    (root / ".claude-plugin/marketplace.json").write_text(json.dumps(mp))
    msgs = "\n".join(str(i) for i in lint.lint(root))
    assert "kebab-case" in msgs and "does not match folder" in msgs
    assert "references missing file references/missing.md" in msgs
    assert "drifted from src/pincite/pincheck.py" in msgs
    assert "contains '..'" in msgs


def test_frontmatter_folded_description():
    meta, body = lint.parse_frontmatter("---\nname: x\ndescription: >-\n  one\n  two\n---\nbody\n")
    assert meta == {"name": "x", "description": "one two"} and body == "body\n"


# -------------------------------------------------------------------- cli


def test_cli_dispatch(capsys, report_docx):
    assert cli.main([]) == 0 and "commands:" in capsys.readouterr().out
    assert cli.main(["--version"]) == 0
    assert cli.main(["nope"]) == 2
    assert cli.main(["units", str(report_docx)]) == 0
    assert "para: 5 units" in capsys.readouterr().out


def test_bundles_are_reproducible(tmp_path):
    out1, out2 = tmp_path / "a", tmp_path / "b"
    for out in (out1, out2):
        subprocess.run(
            [sys.executable, str(ROOT / "tools/bundle.py"), "--out", str(out)], check=True, capture_output=True
        )
    assert (out1 / "SHA256SUMS").read_text() == (out2 / "SHA256SUMS").read_text()
    with zipfile.ZipFile(out1 / "skills" / "citation-table.zip") as z:
        names = z.namelist()
    assert "citation-table/SKILL.md" in names
    assert "citation-table/scripts/build_workbook.py" in names
    assert not any("__pycache__" in n for n in names)
    assert sorted(Path(p).name for p in (out1 / "plugins").iterdir()) == [
        "cheat-sheets-plugin.zip",
        "citation-table-plugin.zip",
    ]
