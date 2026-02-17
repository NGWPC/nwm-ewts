#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

try:
    import yaml  # pyyaml
except ImportError as e:
    raise SystemExit("Missing dependency: pyyaml. Install with: pip install pyyaml") from e


EWTS_ID_WIDTH = 8

DEFAULT_LEVELS = {
    "NOTSET": 0,
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "SEVERE": 40,
    "FATAL": 50,
    "CRITICAL": 50,
}
CANONICAL_NAMES = {
    0: "NOTSET",
    10: "DEBUG",
    20: "INFO",
    30: "WARNING",
    40: "SEVERE",
    50: "FATAL",
}


@dataclass(frozen=True)
class Module:
    key: str
    ewts_id: str
    description: str = ""


def utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_registry(path: Path) -> List[Module]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "modules" not in data:
        raise ValueError("Registry must be a mapping with a 'modules' list.")
    mods = []
    for item in data["modules"]:
        mods.append(Module(
            key=str(item["key"]).strip(),
            ewts_id=str(item["ewts_id"]).strip(),
            description=str(item.get("description", "")).strip(),
        ))
    return mods


def validate_modules(mods: List[Module]) -> None:
    keys = set()
    ids = set()
    for m in mods:
        if not m.key:
            raise ValueError("Empty module key.")
        if m.key in keys:
            raise ValueError(f"Duplicate module key: {m.key}")
        keys.add(m.key)

        if not m.ewts_id:
            raise ValueError(f"Empty ewts_id for key={m.key}")
        if len(m.ewts_id) > EWTS_ID_WIDTH:
            raise ValueError(f"ewts_id too long (> {EWTS_ID_WIDTH}): {m.key} -> {m.ewts_id}")
        if m.ewts_id in ids:
            raise ValueError(f"Duplicate ewts_id: {m.ewts_id}")
        ids.add(m.ewts_id)

        # Optional: enforce uppercase token for log uniformity
        if m.ewts_id.upper() != m.ewts_id:
            raise ValueError(f"ewts_id must be uppercase: {m.key} -> {m.ewts_id}")


def write_module_keys_json(mods: List[Module], out_path: Path) -> None:
    payload: Dict[str, object] = {
        "version": 1,
        "generated_utc": utc_now_z(),
        "modules": {
            m.key: {
                "ewts_id": m.ewts_id,
                "width": EWTS_ID_WIDTH,
                "description": m.description,
            }
            for m in sorted(mods, key=lambda x: x.key)
        },
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_log_levels_json(out_path: Path) -> None:
    payload = {
        "version": 1,
        "generated_utc": utc_now_z(),
        "levels": DEFAULT_LEVELS,
        "canonical_names": {str(k): v for k, v in CANONICAL_NAMES.items()},
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="tools/module_registry.yaml")
    ap.add_argument("--spec-dir", default="spec")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    registry_path = repo_root / args.registry
    spec_dir = repo_root / args.spec_dir
    spec_dir.mkdir(parents=True, exist_ok=True)

    mods = load_registry(registry_path)
    validate_modules(mods)

    write_module_keys_json(mods, spec_dir / "module_keys.json")
    write_log_levels_json(spec_dir / "log_levels.json")
    print("Wrote spec/module_keys.json and spec/log_levels.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
