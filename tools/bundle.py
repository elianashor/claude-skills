#!/usr/bin/env python3
"""Package every skill as an uploadable .zip, and every plugin as a .zip, into dist/.

    python tools/bundle.py [--out dist]

Each skill zip holds one top-level folder named after the skill (SKILL.md plus
its references/ and scripts/), the layout Claude expects for a custom skill
upload. Archives are reproducible: fixed timestamps and sorted entries, so the
same commit always yields byte-identical bundles and a SHA256SUMS file to match.
"""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPOCH = (2020, 1, 1, 0, 0, 0)
SKIP = {"__pycache__", ".DS_Store"}


def _zip(folder: Path, arcroot: str, out: Path) -> None:
    files = sorted(p for p in folder.rglob("*") if p.is_file() and not SKIP & set(p.parts))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            info = zipfile.ZipInfo(f"{arcroot}/{f.relative_to(folder).as_posix()}", EPOCH)
            info.external_attr = (0o755 if f.suffix == ".py" else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, f.read_bytes())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="dist")
    a = ap.parse_args()
    out = ROOT / a.out
    (out / "skills").mkdir(parents=True, exist_ok=True)
    (out / "plugins").mkdir(parents=True, exist_ok=True)
    made = []
    for skill in sorted((ROOT / "plugins").glob("*/skills/*/SKILL.md")):
        target = out / "skills" / f"{skill.parent.name}.zip"
        _zip(skill.parent, skill.parent.name, target)
        made.append(target)
    for plugin in sorted((ROOT / "plugins").glob("*/.claude-plugin/plugin.json")):
        pdir = plugin.parent.parent
        target = out / "plugins" / f"{pdir.name}-plugin.zip"
        _zip(pdir, pdir.name, target)
        made.append(target)
    sums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out).as_posix()}\n" for p in made)
    (out / "SHA256SUMS").write_text(sums)
    for p in made:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
