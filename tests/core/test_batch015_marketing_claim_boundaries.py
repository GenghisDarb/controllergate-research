from pathlib import Path


FORBIDDEN_AFFIRMATIVE = [
    "claims hallucination elimination",
    "claims absolute uncrashability",
    "claims fully self-maintaining software",
    "is production-ready",
    "aerospace-ready",
    "cybersecurity-ready",
    "financial-systems-ready",
    "scientific-trust standard",
]


def test_docs_do_not_claim_forbidden_batch015_outcomes():
    paths = [Path("README.md"), Path("docs/controllergate_positioning.md"), Path("docs/use_case_positioning.md")]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths if path.exists())
    assert not [term for term in FORBIDDEN_AFFIRMATIVE if term in text]
