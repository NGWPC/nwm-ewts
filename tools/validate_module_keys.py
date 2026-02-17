#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec-dir", default="spec")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    spec_dir = repo_root / args.spec_dir

    mk = json.loads((spec_dir / "module_keys.json").read_text(encoding="utf-8"))
    levels = json.loads((spec_dir / "log_levels.json").read_text(encoding="utf-8"))

    modules = mk.get("modules", {})
    if not isinstance(modules, dict) or not modules:
        raise SystemExit("module_keys.json: missing/empty 'modules' map")

    ewts_ids = set()
    for key, info in modules.items():
        ewts_id = info.get("ewts_id", "")
        width = info.get("width", 8)
        if not ewts_id:
            raise SystemExit(f"module '{key}': missing ewts_id")
        if len(ewts_id) > width:
            raise SystemExit(f"module '{key}': ewts_id '{ewts_id}' exceeds width {width}")
        if ewts_id in ewts_ids:
            raise SystemExit(f"Duplicate ewts_id: {ewts_id}")
        ewts_ids.add(ewts_id)

    lv = levels.get("levels", {})
    if not isinstance(lv, dict) or not lv:
        raise SystemExit("log_levels.json: missing/empty 'levels' map")

    # enforce required canonical levels exist
    required = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "FATAL": 50}
    for name, num in required.items():
        if lv.get(name) != num:
            raise SystemExit(f"log_levels.json: expected {name}={num} but got {lv.get(name)}")

    print("Spec validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
