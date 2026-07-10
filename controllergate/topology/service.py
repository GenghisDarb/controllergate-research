from __future__ import annotations

from .activation_ring import evaluate_activation_ring
from .brot_local import build_local_brot
from .contact_ledger import build_contact_ledger
from .proof_matrix import build_proof_matrix
from .reference_core import build_reference_core
from .tld_metrology import run_shadow_assay
from .tot_brot_coupled import build_coupled_tot_brot
from .tot_bulb_volume import build_tot_bulb_volume
from .twist_return import validate_twist_return


class TopologyService:
    build_reference_core = staticmethod(build_reference_core)
    build_contact_ledger = staticmethod(build_contact_ledger)
    build_local_brot = staticmethod(build_local_brot)
    build_coupled_tot_brot = staticmethod(build_coupled_tot_brot)
    build_tot_bulb_volume = staticmethod(build_tot_bulb_volume)
    run_tld_shadow_assay = staticmethod(run_shadow_assay)
    evaluate_activation_ring = staticmethod(evaluate_activation_ring)
    build_proof_matrix = staticmethod(build_proof_matrix)
    validate_twist_return = staticmethod(validate_twist_return)
