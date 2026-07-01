from controllergate.core.curvature_selection import curvature_feature_vector, curvature_feature_vector_schema


def test_curvature_feature_vector_blocks_no_patchable_source():
    vector = curvature_feature_vector({"candidate_class": "native_candidate", "patchable_source_file_count": 0})

    assert "candidate_id" in curvature_feature_vector_schema()["required_fields"]
    assert vector["curvature_eligibility_status"] == "BLOCK"
    assert vector["blocker_if_ineligible"] == "curvature_no_patchable_basin"
