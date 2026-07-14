from .orientation import Orientation


def traverse(value: Orientation) -> Orientation:
    value.validate()
    return Orientation(value.incident_role, value.reference_role, value.patched_role, value.normal_role,
                       value.time_role, value.source_hash, value.provider_hash, value.proof_parent)


def double_traversal(value: Orientation) -> Orientation:
    return traverse(traverse(value))
