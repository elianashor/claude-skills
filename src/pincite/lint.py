#!/usr/bin/env python3
"""
Lint the skills, the plugin manifests and the marketplace before anyone installs them.

Skill checks (every SKILL.md under the root):
  * frontmatter parses; `name` and `description` present
  * name is kebab-case, at most 64 characters, matches its folder, and avoids
    reserved words
  * description at most 1024 characters with no angle brackets (it is what the
    model reads to decide when to load the skill)
  * every relative file the body points at (`references/x.md`, `scripts/y.py`)
    exists, so a skill never sends the model to a missing file
  * body length warning past 500 lines (move detail into references/)

Plugin and marketplace checks:
  * .claude-plugin/marketplace.json has name, owner.name, plugins[]
  * every entry has a name and a relative source without "..", the source
    exists, and its plugin.json `name` equals the entry name
  * plugin versions are semantic versions

Vendored-script checks:
  * every script listed in tools/sync.json is byte-identical to its canonical
    copy in src/, so a skill uploaded on its own runs the tested code

Usage:  python -m pincite.lint [ROOT]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Issue", "lint", "main", "parse_frontmatter"]

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
RESERVED = ("anthropic", "claude")
REF_RE = re.compile(r"`((?:references|scripts|assets|templates|examples)/[\w./-]+)`")


@dataclass
class Issue:
    where: str
    level: str  # error | warning
    message: str

    def __str__(self) -> str:
        return f"{self.level:<7} {self.where}: {self.message}"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse the YAML frontmatter block. Uses PyYAML when present, else a strict subset."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        raise ValueError("no frontmatter block")
    raw, body = m.group(1), m.group(2)
    try:
        import yaml

        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            raise ValueError("frontmatter is not a mapping")
        return data, body
    except ImportError:  # pragma: no cover - exercised only without PyYAML
        pass
    data: dict = {}
    key, block = None, []
    for line in [*raw.splitlines(), "__end__: x"]:
        km = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if km:
            if key is not None and block:
                data[key] = " ".join(s.strip() for s in block).strip()
            key, val = km.group(1), km.group(2).strip()
            block = []
            if val in (">", ">-", "|", "|-"):
                continue
            data[key] = val.strip("'\"")
            key = None if val else key
        elif key is not None:
            block.append(line)
    data.pop("__end__", None)
    return data, body


def lint_skill(skill_md: Path, root: Path) -> list[Issue]:
    rel = str(skill_md.relative_to(root))
    issues: list[Issue] = []
    try:
        meta, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except Exception as e:
        return [Issue(rel, "error", f"frontmatter: {e}")]
    name, desc = str(meta.get("name", "")).strip(), str(meta.get("description", "")).strip()
    folder = skill_md.parent.name
    if not name:
        issues.append(Issue(rel, "error", "missing name"))
    else:
        if not NAME_RE.match(name) or len(name) > 64:
            issues.append(Issue(rel, "error", f"name {name!r} must be kebab-case, ≤64 chars"))
        if name != folder:
            issues.append(Issue(rel, "error", f"name {name!r} does not match folder {folder!r}"))
        if any(w in name for w in RESERVED):
            issues.append(Issue(rel, "error", f"name {name!r} uses a reserved word"))
    if not desc:
        issues.append(Issue(rel, "error", "missing description"))
    else:
        if len(desc) > 1024:
            issues.append(Issue(rel, "error", f"description is {len(desc)} chars (max 1024)"))
        if "<" in desc or ">" in desc:
            issues.append(Issue(rel, "error", "description contains angle brackets"))
    for ref in sorted(set(REF_RE.findall(body))):
        target = skill_md.parent / ref.rstrip("/")
        if "*" not in ref and "<" not in ref and not target.exists():
            issues.append(Issue(rel, "error", f"references missing file {ref}"))
    nlines = body.count("\n")
    if nlines > 500:
        issues.append(Issue(rel, "warning", f"body is {nlines} lines; move detail into references/"))
    return issues


def lint_marketplace(root: Path) -> list[Issue]:
    mp = root / ".claude-plugin" / "marketplace.json"
    if not mp.exists():
        return []
    where = str(mp.relative_to(root))
    try:
        data = json.loads(mp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [Issue(where, "error", f"invalid JSON: {e}")]
    issues: list[Issue] = []
    for k in ("name", "owner", "plugins"):
        if k not in data:
            issues.append(Issue(where, "error", f"missing {k!r}"))
    if not isinstance(data.get("owner"), dict) or not data.get("owner", {}).get("name"):
        issues.append(Issue(where, "error", "owner.name is required"))
    if data.get("name") and not NAME_RE.match(data["name"]):
        issues.append(Issue(where, "error", f"marketplace name {data['name']!r} must be kebab-case"))
    names = set()
    for i, entry in enumerate(data.get("plugins", [])):
        ew = f"{where} plugins[{i}]"
        name, src = entry.get("name"), entry.get("source")
        if not name or not src:
            issues.append(Issue(ew, "error", "entry needs name and source"))
            continue
        if name in names:
            issues.append(Issue(ew, "error", f"duplicate plugin name {name!r}"))
        names.add(name)
        if isinstance(src, str):
            if ".." in Path(src).parts:
                issues.append(Issue(ew, "error", f"source {src!r} contains '..'"))
                continue
            pdir = (root / src).resolve()
            manifest = pdir / ".claude-plugin" / "plugin.json"
            if not pdir.is_dir():
                issues.append(Issue(ew, "error", f"source {src!r} does not exist"))
                continue
            if not manifest.exists():
                issues.append(Issue(ew, "error", f"{src}/.claude-plugin/plugin.json missing"))
                continue
            pj = json.loads(manifest.read_text(encoding="utf-8"))
            if pj.get("name") != name:
                issues.append(Issue(ew, "error", f"plugin.json name {pj.get('name')!r} != entry name {name!r}"))
            if pj.get("version") and not SEMVER.match(pj["version"]):
                issues.append(Issue(ew, "error", f"version {pj['version']!r} is not semver"))
            if not list((pdir / "skills").glob("*/SKILL.md")):
                issues.append(Issue(ew, "warning", "plugin ships no skills"))
    return issues


def lint_sync(root: Path) -> list[Issue]:
    manifest = root / "tools" / "sync.json"
    if not manifest.exists():
        return []
    issues = []
    for src, dests in json.loads(manifest.read_text()).items():
        s = root / src
        for d in dests:
            dp = root / d
            if not dp.exists():
                issues.append(Issue(d, "error", f"vendored copy of {src} is missing (run tools/sync_scripts.py)"))
            elif dp.read_bytes() != s.read_bytes():
                issues.append(Issue(d, "error", f"drifted from {src} (run tools/sync_scripts.py)"))
    return issues


def lint(root: str | Path = ".") -> list[Issue]:
    root = Path(root).resolve()
    issues: list[Issue] = []
    skills = sorted(p for p in root.rglob("SKILL.md") if ".git" not in p.parts and "build" not in p.parts)
    if not skills:
        issues.append(Issue(str(root), "error", "no SKILL.md files found"))
    seen: dict[str, Path] = {}
    for s in skills:
        issues += lint_skill(s, root)
        n = s.parent.name
        if n in seen:
            issues.append(Issue(str(s.relative_to(root)), "error", f"skill name {n!r} also used by {seen[n]}"))
        seen[n] = s.relative_to(root)
    return issues + lint_marketplace(root) + lint_sync(root)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--strict", action="store_true", help="warnings also fail")
    a = ap.parse_args(argv)
    issues = lint(a.root)
    for i in issues:
        print(i)
    errors = sum(i.level == "error" for i in issues)
    print(f"-- {errors} error(s), {len(issues) - errors} warning(s)")
    return 1 if errors or (a.strict and issues) else 0


if __name__ == "__main__":
    sys.exit(main())
