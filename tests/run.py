#!/usr/bin/env python3
"""Run luce-regex's Luce Base tests in native and C comparison modes."""
import argparse
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--base", type=Path, default=ROOT.parent / ("luce-base/build/luce-base.exe" if os.name == "nt" else "luce-base/build/luce-base"))
args = parser.parse_args()
module = ROOT / "src/luce_regex/regex.lucb"
for flags in [["--native"], ["--backend=c"]]:
    subprocess.run([str(args.base.resolve()), "test", str(module), *flags],
                   check=True, env=dict(os.environ), timeout=240)
print("PASS luce-regex engine, native and comparison modes")
