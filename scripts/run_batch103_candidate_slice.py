"""Run one real Batch103 candidate slice through the shared exact harness."""

from __future__ import annotations

import sys

from run_batch102_candidate_slice import main


if __name__ == "__main__":
    if "--campaign-label" not in sys.argv:
        sys.argv.extend(["--campaign-label", "batch103"])
    raise SystemExit(main())
