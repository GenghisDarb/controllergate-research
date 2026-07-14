from __future__ import annotations


VIEWS = ("CUMULATIVE_HISTORICAL_MATURITY", "CURRENT_BATCH_EVIDENCE_DELTA", "PRODUCTION_READINESS_MATURITY")


def validate_model(model: dict[str, object]) -> dict[str, object]:
    errors: list[str] = []
    if set(model.get("views", {})) != set(VIEWS):
        errors.append("maturity_views_missing_or_conflated")
    dimensions = model.get("dimensions", [])
    for view, rows in model.get("views", {}).items():
        if set(rows) != set(dimensions):
            errors.append(f"dimension_coverage:{view}")
        for dimension, record in rows.items():
            if not record.get("level"):
                errors.append(f"level_missing:{view}:{dimension}")
            if view == "CUMULATIVE_HISTORICAL_MATURITY" and int(record["level"].split("_")[1]) > 0 and not record.get("evidence_paths"):
                errors.append(f"historical_evidence_missing:{dimension}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "dimension_count": len(dimensions)}
