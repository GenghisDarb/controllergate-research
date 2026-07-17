import pytest
from controllergate.metrology.tld_contract import ParentNullPair, ThreeProjectionResult
from controllergate.pathways.quality_control_v2 import IncidentClass, classify
from controllergate.topology.canonical_v2 import couple_graphs, LocalBrotGraphV2

def test_parent_null_isolation():
    pair=ParentNullPair('p','h',('n',),1,1); pair.validate()
def test_onset_and_persistence_not_conflated():
    with pytest.raises(ValueError): ThreeProjectionResult('c','a','b','c',True,1,'same','same','w','c').validate()
def test_false_orthology_is_not_terminal_transfer():
    a=LocalBrotGraphV2('a',(),(),(),(),()); b=LocalBrotGraphV2('b',(),(),(),(),())
    result=couple_graphs((a,b),{'a':{'abi':'cp311'},'b':{'abi':'cp313'}})
    assert result.edges[0]['transfer_allowed'] is False
def test_environment_incident_does_not_license_patch():
    assert classify(return_code=1,product_valid=None,transport_failed=True,import_failed=False,warning_only=False).patch_allowed is False
