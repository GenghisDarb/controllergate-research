import inspect
from pathlib import Path

from controllergate.amds.topology_compiler import compile_topology_frame
from controllergate.state.provisional_store import ProvisionalEvidenceStore


def test_decisive_compiler_has_no_external_scientific_inputs():
    parameters=set(inspect.signature(compile_topology_frame).parameters)
    assert not parameters & {'hypotheses','constraints','probes'}


def test_provisional_store_requires_controller_audit(tmp_path: Path):
    store=ProvisionalEvidenceStore(tmp_path/'state.sqlite'); store.create_branch('root'); fact=store.add_fact('root',{'value':1},[])
    try:
        store.promote(fact,None)
    except ValueError as exc:
        assert 'ControllerAudit' in str(exc)
    else:
        raise AssertionError('promotion escaped ControllerAudit')
    store.close()
