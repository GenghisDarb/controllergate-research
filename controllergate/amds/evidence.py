from controllergate.core.evidence import hash_record


def evidence_hash(value: object) -> str:
    return hash_record(value)
