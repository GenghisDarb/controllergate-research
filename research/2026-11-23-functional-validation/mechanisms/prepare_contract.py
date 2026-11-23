"""Pure normalization of the independently transcribed official source."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def normalize(source: dict) -> dict:
    resources = []
    for key, row in source["participants"].items():
        resources.append({"key": key, "source_entity": row["id"], "chemical": row["name"],
                          "compartment": source["compartments"][row["compartment"]], "role": "metabolite_count"})
    for key, row in source["catalysts"].items():
        resources.append({"key": "active_" + key, "source_entity": row["id"], "chemical": "active_role:" + key,
                          "compartment": source["compartments"][row["compartment"]],
                          "role": "asserted_active_catalytic_role", "source_abstraction": row["abstraction"]})
    reactions = []
    for row in source["events"]:
        reactions.append({"id": row["id"], "title": row["source_title"], "direction": "curated_forward",
                          "inputs": row["inputs"], "outputs": row["outputs"],
                          "active_catalysts": ["active_" + row["catalyst"]],
                          "reverse_event": row["reverse_event"], "source_urls": [row["source"]]})
    return {"schema": "reactome_token_contract.v1", "authority": "shadow_non_authorizing",
            "temporal_semantics": "untimed", "resources": resources, "reactions": reactions,
            "coefficient_source": source["coefficient_status"],
            "unmodeled": ["kinetics and concentration-dependent rates", "activity inferred from enzyme abundance",
                          "internal assembly or alternatives of the three aggregate catalytic roles",
                          "quantitative negative regulation", "uncurated alternative physical pathways",
                          "continuous space, crowding, diffusion, pH, electrochemical potential, temperature",
                          "whole-cell behavior", "ControllerGate source ownership or provider execution"],
            "source_contract_sha256": hashlib.sha256((ROOT / "reactome_event_contract.source.json").read_bytes()).hexdigest()}


if __name__ == "__main__":
    source = json.loads((ROOT / "reactome_event_contract.source.json").read_text())
    (ROOT / "token_contract.json").write_text(json.dumps(normalize(source), indent=2, sort_keys=True) + "\n")
