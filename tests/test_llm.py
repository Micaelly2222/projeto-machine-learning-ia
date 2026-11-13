from types import SimpleNamespace

import pytest

from app import llm
from app.analyzer import merge_facts
from app.extraction import extract_facts
from app.llm import LLMEvidence, LLMFacts, LLMUnavailable, extract_with_llm
from app.schemas import CaseInput
from app.text import mask_pii
from tests.conftest import make_case


class FakeMessages:
    def __init__(self, output, stop_reason="end_turn"):
        self.output = output
        self.stop_reason = stop_reason
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(parsed_output=self.output, stop_reason=self.stop_reason)


class FakeClient:
    def __init__(self, output, stop_reason="end_turn"):
        self.messages = FakeMessages(output, stop_reason)


@pytest.fixture(autouse=True)
def llm_ligado(monkeypatch):
    monkeypatch.setattr(llm, "settings", llm.settings.__class__(llm_enabled=True))


def facts(**overrides):
    base = dict(
        final_judgment=False, award_amount=None, plaintiff_deceased=False,
        substitution_without_reservation=False, has_merit_decision=False,
        has_calculation=False, attorney_fees=[], evidence=[],
    )
    base.update(overrides)
    return LLMFacts(**base)


def test_citacao_inexistente_e_descartada():
    case = CaseInput(**make_case())
    output = facts(
        final_judgment=True,
        plaintiff_deceased=True,
        evidence=[
            LLMEvidence(fact="final_judgment", document_id="DOC-2", quote="transitou em julgado em 10/03/2024"),
            LLMEvidence(fact="plaintiff_deceased", document_id="DOC-1", quote="o autor faleceu"),
        ],
    )
    result = extract_with_llm(case, client=FakeClient(output))
    assert result.final_judgment is True
    assert result.plaintiff_deceased is False
    assert [e.policy for e in result.evidence] == ["POL-1"]


def test_recusa_vira_fallback():
    case = CaseInput(**make_case())
    with pytest.raises(LLMUnavailable):
        extract_with_llm(case, client=FakeClient(None, stop_reason="refusal"))


def test_dados_pessoais_mascarados_no_prompt():
    docs = [{"id": "DOC-1", "nome": "Petição",
             "texto": "Autora CPF 123.456.789-00, e-mail maria@exemplo.com, telefone (65) 99999-1234."}]
    case = CaseInput(**make_case(documentos=docs))
    client = FakeClient(facts())
    extract_with_llm(case, client=client)
    prompt = client.messages.calls[0]["messages"][0]["content"]
    assert "123.456.789-00" not in prompt
    assert "maria@exemplo.com" not in prompt
    assert "99999-1234" not in prompt
    assert "[CPF]" in prompt and "[EMAIL]" in prompt and "[PHONE]" in prompt


def test_mask_pii():
    assert mask_pii("CNPJ 12.345.678/0001-90") == "CNPJ [CNPJ]"


def test_merge_soma_fatos_das_duas_fontes(classifier):
    case = CaseInput(**make_case(valorCondenacao=None))
    from app.analyzer import classify_documents

    rules = extract_facts(case, classify_documents(case, classifier))
    rules.final_judgment = False
    from_llm = rules.model_copy(update={"final_judgment": True, "source": "llm"})
    merged = merge_facts(rules, from_llm)
    assert merged.final_judgment is True
    assert merged.source == "llm+rules"
