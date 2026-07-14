from __future__ import annotations


WRITE_LEVELS = {
    0: "WRITE_LEVEL_0_DISABLED",
    1: "WRITE_LEVEL_1_LOCAL_SANDBOX",
    2: "WRITE_LEVEL_2_ISOLATED_LOCAL_WORKTREE",
    3: "WRITE_LEVEL_3_OPERATOR_APPROVED_REMOTE_BRANCH",
    4: "WRITE_LEVEL_4_OPERATOR_APPROVED_PULL_REQUEST",
    5: "WRITE_LEVEL_5_AUTOMATIC_MERGE",
}


def authorize(level: int) -> dict[str, object]:
    if level not in WRITE_LEVELS:
        return {"status": "BLOCK", "blocker": "unknown_write_level"}
    enabled = level in {1, 2}
    return {"status": "PASS" if enabled else "BLOCK", "level": WRITE_LEVELS[level], "public_remote_mutation": False, "demonstrated_in_batch085": enabled}
