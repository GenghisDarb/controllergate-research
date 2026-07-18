from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

RETIRED=(
 '.github/workflows/post_v2_37_hardening_batch096_repository_genome_topology_compiled_amds_unification.yml',
 'scripts/run_batch096_materialization_and_topology.py',
 'scripts/run_batch096_amds_and_release.py',
 'scripts/audit_batch096_repository_genome_topology_compiled_amds.py',
 'tests/core/test_batch096_amds_release.py',
)

def test_batch096_synthetic_shortcuts_are_not_current_files():
 assert all(not (ROOT/path).exists() for path in RETIRED)

def test_batch096_raw_outputs_are_preserved():
 output=ROOT/'outputs/post_v2_37_hardening_batch096_repository_genome_topology_compiled_amds_unification'
 assert (output/'batch096_consolidated_state.json').is_file()
 assert (output/'ARTIFACT_SHA256SUMS.txt').is_file()
