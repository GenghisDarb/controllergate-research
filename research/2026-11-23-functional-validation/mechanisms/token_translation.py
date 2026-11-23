"""Local, untimed, nonauthorizing reaction-to-resource translation.

This module preserves a declared token model. It neither supplies kinetics nor
turns source annotations into measured catalyst activity or biological proof.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
from typing import Any, Mapping


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class Reaction:
    identifier: str
    inputs: tuple[tuple[str, int], ...]
    outputs: tuple[tuple[str, int], ...]
    catalysts: tuple[str, ...]


@dataclass(frozen=True)
class Model:
    places: tuple[str, ...]
    chemical: Mapping[str, str]
    compartment: Mapping[str, str]
    reactions: tuple[Reaction, ...]


@dataclass(frozen=True)
class Result:
    status: str
    inventory: tuple[int | None, ...]
    reason: str


def _pairs(raw: Any, places: set[str]) -> tuple[tuple[str, int], ...]:
    if not isinstance(raw, dict) or not raw:
        raise ContractError("a nonempty coefficient object is required")
    pairs = []
    for key, amount in raw.items():
        if key not in places or type(amount) is not int or amount <= 0:
            raise ContractError("unknown place or nonpositive/noninteger coefficient")
        pairs.append((key, amount))
    return tuple(sorted(pairs))


def load_model(payload: Any) -> Model:
    if not isinstance(payload, dict) or payload.get("schema") != "reactome_token_contract.v1":
        raise ContractError("unsupported model schema")
    if payload.get("temporal_semantics") != "untimed" or payload.get("authority") != "shadow_non_authorizing":
        raise ContractError("only untimed nonauthorizing token contracts are supported")
    resources = payload.get("resources")
    if not isinstance(resources, list) or not resources:
        raise ContractError("resource declarations required")
    keys, chemical, compartment = [], {}, {}
    for item in resources:
        if not isinstance(item, dict):
            raise ContractError("resource must be an object")
        key = item.get("key")
        if not isinstance(key, str) or not key or key in keys:
            raise ContractError("unique nonempty resource key required")
        for field in ("chemical", "compartment", "source_entity"):
            if not isinstance(item.get(field), str) or not item[field]:
                raise ContractError("explicit identity, chemical and compartment required")
        keys.append(key)
        chemical[key], compartment[key] = item["chemical"], item["compartment"]
    reactions, seen = [], set()
    for raw in payload.get("reactions", []):
        if not isinstance(raw, dict) or not isinstance(raw.get("id"), str) or raw["id"] in seen:
            raise ContractError("unique reaction identifier required")
        if raw.get("direction") != "curated_forward":
            raise ContractError("each direction must be a separately curated event")
        if not raw.get("source_urls"):
            raise ContractError("source URLs required")
        catalysts = raw.get("active_catalysts")
        if not isinstance(catalysts, list) or any(p not in keys for p in catalysts) or len(set(catalysts)) != len(catalysts):
            raise ContractError("declared catalyst read places required")
        incoming, outgoing = _pairs(raw.get("inputs"), set(keys)), _pairs(raw.get("outputs"), set(keys))
        if set(catalysts) & (dict(incoming).keys() | dict(outgoing).keys()):
            raise ContractError("this bounded contract requires catalysts distinct from consumed/produced places")
        reactions.append(Reaction(raw["id"], incoming, outgoing, tuple(catalysts)))
        seen.add(raw["id"])
    if not reactions:
        raise ContractError("reaction declarations required")
    return Model(tuple(keys), chemical, compartment, tuple(reactions))


def checked_inventory(model: Model, inventory: Any) -> tuple[int | None, ...]:
    if not isinstance(inventory, (tuple, list)) or len(inventory) != len(model.places):
        raise ContractError("inventory has wrong shape")
    if any(x is not None and (type(x) is not int or x < 0) for x in inventory):
        raise ContractError("counts must be nonnegative exact integers or explicit unknown")
    return tuple(inventory)


def state_from(model: Model, supplied: Mapping[str, int | None], default: int | None = 0) -> tuple[int | None, ...]:
    if set(supplied) - set(model.places):
        raise ContractError("unknown inventory place")
    return checked_inventory(model, [supplied.get(p, default) for p in model.places])


def source_step(model: Model, reaction: Reaction, inventory: tuple[int | None, ...]) -> Result:
    """Direct source-contract oracle, written separately from both backends."""
    values = dict(zip(model.places, checked_inventory(model, inventory)))
    demands = list(reaction.inputs) + [(p, 1) for p in reaction.catalysts]
    if any(values[p] is not None and values[p] < n for p, n in demands):
        return Result("BLOCK", inventory, "known joint prerequisite absent")
    touched = {p for p, _ in reaction.inputs + reaction.outputs} | set(reaction.catalysts)
    if any(values[p] is None for p in touched):
        return Result("UNRESOLVED", inventory, "required state or successor count unknown")
    result = dict(values)
    for place, count in reaction.inputs:
        result[place] -= count
    for place, count in reaction.outputs:
        result[place] += count
    return Result("PASS", tuple(result[p] for p in model.places), "declared forward token transition")


def load_archived_primitive():
    path = Path(__file__).parent / "source_snapshot/controllergate/isomorphism/primitives.py"
    spec = importlib.util.spec_from_file_location("archived_resource_primitive", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.apply_primitive


class FaithfulTranslation:
    """Injective qualified-place mapping + joint check + atomic commit.

    The actual archived RESOURCE_FLUX primitive is invoked separately for each
    consumption and production in private working state. An operation commits
    only after the entire transition succeeds; catalyst places are read only.
    """
    def __init__(self, model: Model, resource_mapping: Mapping[str, str] | None = None):
        self.model = model
        self.mapping = dict(resource_mapping or {p: f"resource/{i}" for i, p in enumerate(model.places)})
        if set(self.mapping) != set(model.places) or len(set(self.mapping.values())) != len(model.places):
            raise ContractError("place mapping must be total and injective")
        self.apply = load_archived_primitive()
        self.position = {p: i for i, p in enumerate(model.places)}
        self.compiled = {}
        for reaction in model.reactions:
            self.compiled[reaction.identifier] = {
                "consume": {self.mapping[p]: n for p, n in reaction.inputs},
                "produce": {self.mapping[p]: n for p, n in reaction.outputs},
                "read": {self.mapping[p]: 1 for p in reaction.catalysts},
            }

    def step(self, reaction: Reaction, inventory: tuple[int | None, ...]) -> Result:
        raw = checked_inventory(self.model, inventory)
        stock = {self.mapping[p]: raw[i] for i, p in enumerate(self.model.places)}
        contract = self.compiled[reaction.identifier]
        required = {**contract["consume"], **contract["read"]}
        for place, count in required.items():
            if stock[place] is not None and stock[place] < count:
                return Result("BLOCK", raw, "atomic prerequisite unmet")
        if any(stock[p] is None for p in set(required) | set(contract["produce"])):
            return Result("UNRESOLVED", raw, "atomic state incomplete")
        working = dict(stock)
        for role, sign in (("consume", -1), ("produce", 1)):
            for place, quantity in contract[role].items():
                # Exact integer handling is retained before/after the archived
                # float-valued guard, whose supported exact range is bounded.
                if abs(working[place]) + quantity > 2**53:
                    return Result("UNRESOLVED", raw, "outside exact archived-guard integer range")
                response = self.apply(
                    "RESOURCE_FLUX",
                    {"primitive_trace": [], "resource_balance": {"balance": working[place]}},
                    {"source_occurrence_identity": reaction.identifier, "resource_delta": sign * quantity},
                )
                if response["status"] != "PASS":
                    return Result("BLOCK", raw, "archived per-resource underflow guard blocked")
                observed = response["state"]["resource_balance"]["balance"]
                expected = working[place] + sign * quantity
                if observed != expected:
                    return Result("UNRESOLVED", raw, "archived primitive arithmetic disagreement")
                working[place] = expected
        return Result("PASS", tuple(working[self.mapping[p]] for p in self.model.places), "atomic resource transaction")


class GenericIncidence:
    """Independent generic pre/incidence/read-arc implementation, same data."""
    def __init__(self, model: Model):
        self.model = model
        self.index = {p: i for i, p in enumerate(model.places)}
        self.transitions = {}
        for reaction in model.reactions:
            pre, post, read = [0] * len(model.places), [0] * len(model.places), [0] * len(model.places)
            for p, value in reaction.inputs:
                pre[self.index[p]] = value
            for p, value in reaction.outputs:
                post[self.index[p]] = value
            for p in reaction.catalysts:
                read[self.index[p]] = 1
            self.transitions[reaction.identifier] = (pre, post, read)

    def step(self, reaction: Reaction, inventory: tuple[int | None, ...]) -> Result:
        raw = checked_inventory(self.model, inventory)
        pre, post, read = self.transitions[reaction.identifier]
        if any(value is not None and value < max(a, c) for value, a, c in zip(raw, pre, read)):
            return Result("BLOCK", raw, "generic pre/read arc unsatisfied")
        if any(value is None and (a or b or c) for value, a, b, c in zip(raw, pre, post, read)):
            return Result("UNRESOLVED", raw, "generic marked place unknown")
        updated = tuple(None if value is None else value - a + b for value, a, b in zip(raw, pre, post))
        return Result("PASS", updated, "generic incidence update")


def ablated_step(model: Model, reaction: Reaction, inventory: tuple[int | None, ...], mechanism: str) -> Result:
    """Deliberately lossy controls, not proposed competent baselines."""
    if any(x is None for x in inventory):
        return Result("UNRESOLVED", inventory, "ablations only evaluated on known states")
    index = {p: i for i, p in enumerate(model.places)}
    if mechanism == "edge_only":
        # Graph adjacency admits any one incoming resource instead of all.
        enabled = any(inventory[index[p]] >= n for p, n in reaction.inputs)
        enabled = enabled and all(inventory[index[p]] >= 1 for p in reaction.catalysts)
        if not enabled:
            return Result("BLOCK", inventory, "no incoming edge available")
        updated = list(inventory)
        for p, amount in reaction.inputs:
            updated[index[p]] -= amount
        for p, amount in reaction.outputs:
            updated[index[p]] += amount
        return Result("PASS", tuple(updated), "ablated joint enabling")
    if mechanism == "consume_catalyst":
        correct = source_step(model, reaction, inventory)
        if correct.status != "PASS":
            return correct
        updated = list(correct.inventory)
        for p in reaction.catalysts:
            updated[index[p]] -= 1
        return Result("PASS", tuple(updated), "wrongly consumed reusable catalyst")
    if mechanism == "pool_compartments":
        # Pool availability by chemical identity, then debit the actual pool.
        # Deterministic source-place-first allocation makes the ablation
        # reproducible; it still admits remote matter without transport.
        pools = {}
        for place, value in zip(model.places, inventory):
            pools[model.chemical[place]] = pools.get(model.chemical[place], 0) + value
        demand = {}
        for p, count in reaction.inputs:
            c = model.chemical[p]
            demand[c] = demand.get(c, 0) + count
        if any(pools[c] < amount for c, amount in demand.items()) or any(inventory[index[p]] < 1 for p in reaction.catalysts):
            return Result("BLOCK", inventory, "pooled count absent")
        updated = list(inventory)
        for p, count in reaction.inputs:
            choices = [p] + [q for q in model.places if q != p and model.chemical[q] == model.chemical[p]]
            remaining = count
            for q in choices:
                take = min(remaining, updated[index[q]])
                updated[index[q]] -= take
                remaining -= take
        for p, count in reaction.outputs:
            updated[index[p]] += count
        return Result("PASS", tuple(updated), "compartment identity collapsed")
    raise ContractError("unknown mechanism ablation")


def sequential_batch(step, reactions: tuple[Reaction, ...], inventory: tuple[int | None, ...]) -> tuple[list[str], tuple[int | None, ...]]:
    statuses, state = [], inventory
    for reaction in reactions:
        result = step(reaction, state)
        statuses.append(result.status)
        if result.status == "PASS":
            state = result.inventory
    return statuses, state


def independent_snapshot_batch(model: Model, reactions: tuple[Reaction, ...], inventory: tuple[int | None, ...]) -> tuple[list[str], tuple[int | None, ...]]:
    """Ablation: each operation approves against an unchanged initial snapshot.

    Updates are then combined without a joint reservation/commit check. The
    returned invalid marking is diagnostic data, never an actual mutation.
    """
    statuses, state = [], list(inventory)
    for reaction in reactions:
        result = source_step(model, reaction, inventory)
        statuses.append(result.status)
        if result.status == "PASS":
            for i, (old, new) in enumerate(zip(inventory, result.inventory)):
                if old is not None and new is not None:
                    state[i] += new - old
    return statuses, tuple(state)


def rate_or_deadline_query() -> dict[str, str]:
    return {"status": "UNRESOLVED", "reason": "no kinetic law, rate constants, duration or measured environmental dynamics supplied"}
