from data.prepare_claim_detection_dataset import metadata_from_source


def test_metadata_from_source_uses_only_explicit_source_information():
    assert metadata_from_source("original (tn-arabizi)") == ("tn", "arabizi")
    assert metadata_from_source("original") == ("unk", "unknown")
