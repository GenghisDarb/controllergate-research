from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from controllergate.state.integrity import canonical_hash


SCHEMA_VERSION = "neutral-observation-v1"
NEUTRAL_FIELDS = {
    "ast_contact_paths",
    "exception_type",
    "first_divergent_event_hash",
    "harness_origin_hash",
    "import_origin_paths",
    "incident_output_hash",
    "installed_distribution_graph_hash",
    "network_ledger_hash",
    "normal_output_hash",
    "resource_state",
    "return_code",
    "runner_origin_hash",
    "source_tree_hash_after",
    "source_tree_hash_before",
    "stderr_hash",
    "stdout_hash",
    "structured_collection_count",
    "structured_collection_hash",
    "test_tree_hash_after",
    "test_tree_hash_before",
    "timeout_state",
    "workspace_diff_paths",
}
FORBIDDEN_ALIASES = {
    "candidate_source",
    "environment_failure",
    "environment_owned",
    "harness_failure",
    "harness_owned",
    "non_source_terminal",
    "provider_failure",
    "provider_owned",
    "source_contact",
    "source_owned",
    "terminal_class",
}


def semantic_alias_hits(value: object, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            for alias in FORBIDDEN_ALIASES:
                if re.search(rf"(^|[^a-z0-9]){re.escape(alias)}([^a-z0-9]|$)", key_text):
                    hits.append(f"{path}.{key}")
            hits.extend(semantic_alias_hits(item, f"{path}.{key}"))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            hits.extend(semantic_alias_hits(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        for alias in FORBIDDEN_ALIASES:
            if re.search(rf"(^|[^a-z0-9]){re.escape(alias)}([^a-z0-9]|$)", lowered):
                hits.append(path)
    return sorted(set(hits))


@dataclass(frozen=True)
class NeutralObservation:
    values: dict[str, Any]
    schema_version: str = SCHEMA_VERSION

    @property
    def observation_hash(self) -> str:
        return canonical_hash({"schema_version": self.schema_version, "values": self.values})

    def record(self) -> dict[str, object]:
        return {
            "observation_hash": self.observation_hash,
            "schema_version": self.schema_version,
            "values": self.values,
        }


def parse_neutral_observation(text: str) -> NeutralObservation:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError("neutral observation must be one JSON object") from error
    if not isinstance(value, dict) or not value:
        raise ValueError("neutral observation object required")
    unknown = sorted(set(value) - NEUTRAL_FIELDS)
    if unknown:
        raise ValueError(f"unregistered neutral observation fields: {','.join(unknown)}")
    aliases = semantic_alias_hits(value)
    if aliases:
        raise ValueError(f"semantic aliases rejected: {','.join(aliases)}")
    if "return_code" not in value:
        raise ValueError("return_code field required")
    return NeutralObservation(values=value)
