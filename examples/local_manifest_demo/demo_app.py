def normalize_project_name(value: str) -> str:
    """Return a deterministic project identifier."""
    return value.strip().lower().replace(" ", "_")
