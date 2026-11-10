#!/usr/bin/env python3
"""Copy the canonical modules in src/pincite/ into every skill that vendors them.

A skill uploaded to Claude on its own cannot import a package, so each skill
carries its scripts. The package is the single source of truth: edit src/, run
this, commit both. CI (pincite lint) fails if any vendored copy drifts.

    python tools/sync_scripts.py           # write copies
    python tools/sync_scripts.py --check   # exit 1 if any copy differs
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    mapping = json.loads((ROOT / "tools" / "sync.json").read_text())
    stale = 0
    for src, dests in mapping.items():
        s = ROOT / src
        for d in dests:
            dp = ROOT / d
            same = dp.exists() and dp.read_bytes() == s.read_bytes()
            if a.check:
                if not same:
                    print(f"drift: {d} != {src}")
                    stale += 1
            elif not same:
                dp.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(s, dp)
                dp.chmod(0o755)
                print(f"synced {d}")
    if a.check:
        print(f"-- {stale} drifted file(s)")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
