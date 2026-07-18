import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/post_v2_37_hardening_batch097_evidence_reconstitution_real_repository_genome_topology_amds'

def test_tld_source_ledger_covers_all_notebooks_when_materialized():
    path=OUT/'tld_1_44_requirement_ledger_v2.jsonl'
    if not path.exists(): return
    rows=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x]
    assert {x['notebook'] for x in rows if x['notebook'] is not None}==set(range(1,45))
    assert all(x['stable_content_identity'] and x['source_file'] for x in rows)
