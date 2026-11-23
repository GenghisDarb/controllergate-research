from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest

from token_translation import (ContractError, FaithfulTranslation, GenericIncidence, ablated_step,
                              independent_snapshot_batch, load_model, rate_or_deadline_query,
                              sequential_batch, source_step, state_from)

ROOT = Path(__file__).resolve().parent


class TranslationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((ROOT / "token_contract.json").read_text())
        cls.model = load_model(cls.payload)
        cls.faithful, cls.generic = FaithfulTranslation(cls.model), GenericIncidence(cls.model)
        cls.by_id = {r.identifier: r for r in cls.model.reactions}
        cls.ldh, cls.reverse = cls.by_id["R-HSA-71849"], cls.by_id["R-HSA-70510"]
        cls.gapdh = cls.by_id["R-HSA-70449"]
        cls.inward = cls.by_id["R-HSA-373867"]

    def ready(self, amount=1):
        return state_from(self.model, {"PYR_c": amount, "NADH_c": amount, "H_c": amount, "active_LDH": 1})

    def test_01_source_generic_and_archived_guard_adapter_agree(self):
        s = self.ready()
        expected = source_step(self.model, self.ldh, s)
        for step in (self.faithful.step, self.generic.step):
            got = step(self.ldh, s)
            self.assertEqual((got.status, got.inventory), (expected.status, expected.inventory))

    def test_02_catalyst_reuse_is_required_for_two_firings(self):
        s = self.ready(2)
        statuses, final = sequential_batch(self.faithful.step, (self.ldh, self.ldh), s)
        self.assertEqual(statuses, ["PASS", "PASS"])
        self.assertEqual(final[self.model.places.index("active_LDH")], 1)
        wrong = ablated_step(self.model, self.ldh, s, "consume_catalyst")
        self.assertEqual(ablated_step(self.model, self.ldh, wrong.inventory, "consume_catalyst").status, "BLOCK")

    def test_03_missing_input_blocks_without_partial_commit(self):
        s = state_from(self.model, {"PYR_c": 1, "H_c": 1, "active_LDH": 1})
        got = self.faithful.step(self.ldh, s)
        self.assertEqual((got.status, got.inventory), ("BLOCK", s))

    def test_04_remote_proton_requires_real_transport_transition(self):
        s = state_from(self.model, {"PYR_c": 1, "NADH_c": 1, "H_e": 1, "LACT_e": 1, "active_LDH": 1, "active_BSG_MCT": 1})
        self.assertEqual(self.faithful.step(self.ldh, s).status, "BLOCK")
        moved = self.faithful.step(self.inward, s)
        self.assertEqual(self.faithful.step(self.ldh, moved.inventory).status, "PASS")
        self.assertEqual(ablated_step(self.model, self.ldh, s, "pool_compartments").status, "PASS")

    def test_05_distinct_curated_reverse_restores_source_state(self):
        s = self.ready()
        statuses, final = sequential_batch(self.faithful.step, (self.ldh, self.reverse), s)
        self.assertEqual(statuses, ["PASS", "PASS"])
        self.assertEqual(final, s)

    def test_06_cofactor_return_is_not_full_state_return(self):
        s = state_from(self.model, {"GA3P_c": 1, "Pi_c": 1, "NAD_c": 1, "PYR_c": 1, "active_GAPDH": 1, "active_LDH": 1})
        statuses, final = sequential_batch(self.faithful.step, (self.gapdh, self.ldh), s)
        self.assertEqual(statuses, ["PASS", "PASS"])
        for p in ("NAD_c", "NADH_c", "H_c"):
            i = self.model.places.index(p)
            self.assertEqual(final[i], s[i])
        self.assertNotEqual(final, s)

    def test_07_unknown_is_not_false_or_success(self):
        s = list(self.ready())
        s[self.model.places.index("NADH_c")] = None
        for step in (self.faithful.step, self.generic.step):
            self.assertEqual(step(self.ldh, tuple(s)).status, "UNRESOLVED")
        s[self.model.places.index("PYR_c")] = 0
        self.assertEqual(self.faithful.step(self.ldh, tuple(s)).status, "BLOCK")

    def test_08_unknown_output_baseline_blocks_exact_successor_claim(self):
        s = list(self.ready())
        s[self.model.places.index("LACT_c")] = None
        self.assertEqual(self.faithful.step(self.ldh, tuple(s)).status, "UNRESOLVED")

    def test_09_unrelated_unknown_is_retained(self):
        s = list(self.ready())
        s[self.model.places.index("GA3P_c")] = None
        got = self.faithful.step(self.ldh, tuple(s))
        self.assertEqual(got.status, "PASS")
        self.assertIsNone(got.inventory[self.model.places.index("GA3P_c")])

    def test_10_atomic_rollback_if_inner_guard_fails(self):
        instance = FaithfulTranslation(self.model)
        actual, calls = instance.apply, []
        def adversarial(primitive, state, event):
            calls.append(primitive)
            return {"status": "BLOCK"} if len(calls) == 2 else actual(primitive, state, event)
        instance.apply = adversarial
        s = self.ready()
        got = instance.step(self.ldh, s)
        self.assertEqual((got.status, got.inventory), ("BLOCK", s))

    def test_11_concurrent_independent_approvals_can_overcommit(self):
        s = self.ready()
        statuses, final = sequential_batch(self.faithful.step, (self.ldh, self.ldh), s)
        self.assertEqual(statuses, ["PASS", "BLOCK"])
        bad_status, bad = independent_snapshot_batch(self.model, (self.ldh, self.ldh), s)
        self.assertEqual(bad_status, ["PASS", "PASS"])
        self.assertTrue(any(x < 0 for x in bad))
        self.assertTrue(all(x >= 0 for x in final))

    def test_12_place_mapping_cannot_merge_compartments(self):
        mapping = {p: p for p in self.model.places}
        mapping["H_e"] = "H_c"
        with self.assertRaises(ContractError):
            FaithfulTranslation(self.model, mapping)

    def test_13_boolean_fractional_and_nonfinite_counts_rejected(self):
        for value in (True, 0.5, float("nan"), float("inf"), -1):
            with self.subTest(value=str(value)), self.assertRaises(ContractError):
                self.faithful.step(self.ldh, state_from(self.model, {"PYR_c": value}))

    def test_14_unsupported_contract_is_not_silently_coerced(self):
        for field, value in (("inputs", {"PYR_c": True}), ("direction", "inferred_reverse"), ("active_catalysts", ["PYR_c"])):
            changed = copy.deepcopy(self.payload)
            changed["reactions"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ContractError):
                load_model(changed)

    def test_15_rates_and_deadlines_remain_unresolved(self):
        self.assertEqual(rate_or_deadline_query()["status"], "UNRESOLVED")

    def test_16_archived_float_guard_exact_range_is_explicit(self):
        s = self.ready(2**53)
        got = self.faithful.step(self.ldh, s)
        self.assertEqual((got.status, got.inventory), ("UNRESOLVED", s))


if __name__ == "__main__":
    unittest.main(verbosity=2)
