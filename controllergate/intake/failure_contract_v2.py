from __future__ import annotations

from dataclasses import dataclass


FAILURE_CLASSES = {
    "candidate_assertion", "candidate_exception", "provider_failure", "environment_failure",
    "platform_failure", "harness_failure", "collection_failure", "target_missing",
    "resource_timeout", "expected_pass", "insufficient_evidence",
}


@dataclass(frozen=True)
class FailureContractV2:
    classification: str
    target_present: bool
    structured_collection_valid: bool
    source_immutable: bool
    tests_immutable: bool
    timeout_seconds: int | None = None

    def validate(self) -> dict[str, object]:
        errors = []
        if self.classification not in FAILURE_CLASSES:
            errors.append("unknown_failure_class")
        if self.classification in {"candidate_assertion", "candidate_exception"} and not (self.target_present and self.structured_collection_valid):
            errors.append("candidate_failure_without_structured_target")
        if self.classification == "resource_timeout":
            errors.append("timeout_not_candidate_failure_evidence")
        if not self.source_immutable or not self.tests_immutable:
            errors.append("pre_repair_tree_mutated")
        return {"status": "PASS" if not errors else "BLOCK", "classification": self.classification, "errors": errors}
