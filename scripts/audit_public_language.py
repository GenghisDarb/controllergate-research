from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    ROOT / "controllergate/runtime/candidate_execution_authorization.py",
    ROOT / "controllergate/runtime/candidate_execution_plan.py",
    ROOT / "controllergate/runtime/authorized_candidate_dispatcher.py",
    ROOT / "controllergate/runtime/generic_patch_plan.py",
    ROOT / "controllergate/runtime/evidence_ownership.py",
    ROOT / "outputs/post_v2_37_hardening_batch072_count5_authorized_amds_memory_wave1/batch072_summary.md",
)
FORBIDDEN = ("self-maintaining software: true", "full scoring: pass", "memory lift: demonstrated")


def main() -> int:
    failures: list[str] = []
    for path in FILES:
        if not path.is_file():
            failures.append(f"missing:{path.relative_to(ROOT)}")
            continue
        lowered = path.read_text(encoding="utf-8").lower()
        for phrase in FORBIDDEN:
            if phrase in lowered:
                failures.append(f"overclaim:{path.relative_to(ROOT)}:{phrase}")
    print("Public language audit:", "PASS" if not failures else "FAIL")
    if failures:
        print("\n".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
