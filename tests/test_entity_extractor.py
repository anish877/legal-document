import sys
import types


stub = types.ModuleType("transformers")


class _Dummy:
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        return cls()


def _pipeline(*args, **kwargs):
    return None


stub.AutoModelForTokenClassification = _Dummy
stub.AutoTokenizer = _Dummy
stub.pipeline = _pipeline
sys.modules.setdefault("transformers", stub)

from ai.entity_extractor import LegalEntityExtractor


def test_agreement_party_regex_prefers_numbered_and_designated_entities():
    extractor = LegalEntityExtractor()
    text = """
    THIS AGREEMENT
    1. ABC Enterprises Pvt. Ltd.
    2. XYZ Solutions Ltd.

    ABC Enterprises Pvt. Ltd. (hereinafter referred to as the "First Party")
    XYZ Solutions Ltd. (hereinafter referred to as the "Second Party")
    Supersedes All Prior Discussions
    """

    parties = extractor.extract_entities(text)["parties"]

    assert parties == [
        {"name": "ABC Enterprises Pvt. Ltd.", "role": "First Party"},
        {"name": "XYZ Solutions Ltd.", "role": "Second Party"},
    ]


def test_agreement_party_filter_rejects_generic_phrases():
    extractor = LegalEntityExtractor()
    text = """
    First Party: Supersedes All Prior Discussions
    Second Party: Section Review Clause
    """

    assert extractor.extract_entities(text)["parties"] == []
