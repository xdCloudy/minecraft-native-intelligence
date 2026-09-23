#!/usr/bin/env python3
"""Synthetic experiment-runner smoke trial; not capability evidence."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    seed = int(os.environ["MNI_SEED"])
    attempt = int(os.environ["MNI_ATTEMPT"])
    trial_dir = Path(os.environ["MNI_TRIAL_DIR"])
    trial_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "synthetic_fixture": True,
        "variant_id": os.environ["MNI_VARIANT_ID"],
        "seed": seed,
        "repetition_index": int(os.environ["MNI_REPETITION_INDEX"]),
        "attempt": attempt,
    }
    (trial_dir / "fixture-output.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"synthetic fixture seed={seed} attempt={attempt}")

    if seed == 202 and attempt == 0:
        print("intentional synthetic failure for retry-preservation test", file=sys.stderr)
        return 23
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
