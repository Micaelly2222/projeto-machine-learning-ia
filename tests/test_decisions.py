import pytest

from app.analyzer import analyze
from app.schemas import CaseInput, Decision
from tests.conftest import make_case


def run(classifier, **overrides):
    return analyze(CaseInput(**make_case(**overrides)), classifier=classifier, use_llm=False)


def test_casos_de_exemplo(classifier, cases):
    for item in cases:
        result = analyze(CaseInput(**item["case"]), classifier=classifier, use_llm=False)
        assert result.decision.value == item["expected"], item["name"]


def test_aprovado_cita_politicas_verificadas(classifier):
    result = run(classifier)
    assert result.decision == Decision.APPROVED
    assert "POL-1" in result.citations
    assert all(check.passed for check in result.checks)


def test_trabalhista_pelo_numero_cnj(classifier):
    result = run(classifier, numeroProcesso="0100001-11.2023.5.02.0001", esfera="Estadual")
    assert result.decision == Decision.REJECTED
    assert result.citations == ["POL-4"]


def test_valor_abaixo_do_minimo(classifier):
    result = run(classifier, valorCondenacao=999.99)
    assert result.decision == Decision.REJECTED
    assert "POL-3" in result.citations


def test_valor_no_limite_e_aceito(classifier):
    result = run(classifier, valorCondenacao=1000.0)
    assert result.decision == Decision.APPROVED


def test_valor_extraido_da_planilha(classifier):
    result = run(classifier, valorCondenacao=None)
    assert result.decision == Decision.APPROVED
    assert result.facts.award_amount == 15000.0


def test_rejeicao_tem_prioridade_sobre_incompleto(classifier):
    docs = [{"id": "DOC-1", "nome": "Sentença", "texto": "Julgo procedente."}]
    result = run(classifier, esfera="Trabalhista", documentos=docs)
    assert result.decision == Decision.REJECTED
    assert result.citations == ["POL-4"]


def test_improcedente_nao_vira_aprovacao(classifier):
    docs = [{"id": "DOC-1", "nome": "Sentença", "texto": "JULGO IMPROCEDENTE o pedido."}]
    result = run(classifier, documentos=docs)
    assert result.decision == Decision.INCOMPLETE


@pytest.mark.parametrize(
    "texto",
    [
        "Certifico que a sentença ainda não transitou em julgado.",
        "Não houve trânsito em julgado até a presente data.",
        "Após o trânsito em julgado, arquivem-se os autos.",
    ],
)
def test_negacao_e_mencao_futura_nao_contam(classifier, texto):
    docs = [
        {"id": "DOC-1", "nome": "Sentença", "texto": texto},
        {"id": "DOC-2", "nome": "Planilha de Cálculos", "texto": "Total geral: R$ 15.000,00."},
    ]
    result = run(classifier, documentos=docs)
    assert result.decision == Decision.INCOMPLETE
    assert "POL-1" in result.citations


def test_transito_pelo_movimento(classifier):
    docs = [
        {"id": "DOC-1", "nome": "Sentença", "texto": "Julgo procedente."},
        {"id": "DOC-2", "nome": "Planilha de Cálculos", "texto": "Total geral: R$ 15.000,00."},
    ]
    result = run(classifier, documentos=docs, movimentos=[{"descricao": "Trânsito em Julgado"}])
    assert result.decision == Decision.APPROVED


def test_obito_negado_nao_rejeita(classifier):
    extra = {"id": "DOC-4", "nome": "Petição", "texto": "A autora informa que não há notícia de óbito."}
    result = run(classifier, documentos=make_case()["documentos"] + [extra])
    assert result.decision == Decision.APPROVED


def test_substabelecimento_com_reserva_nao_rejeita(classifier):
    extra = {"id": "DOC-4", "nome": "Substabelecimento", "texto": "Substabeleço com reserva de iguais poderes."}
    result = run(classifier, documentos=make_case()["documentos"] + [extra])
    assert result.decision == Decision.APPROVED


def test_honorarios_sao_informados_sem_mudar_decisao(classifier):
    docs = make_case()["documentos"]
    docs[2] = {"id": "DOC-3", "nome": "Planilha de Cálculos",
               "texto": "Total geral: R$ 15.000,00. Honorários contratuais de 30%: R$ 4.500,00."}
    result = run(classifier, documentos=docs)
    assert result.decision == Decision.APPROVED
    assert "POL-7" in result.citations
    assert any("4.500,00" in fee for fee in result.facts.attorney_fees)


def test_justificativa_cita_evidencia(classifier):
    result = run(classifier, valorCondenacao=500.0)
    assert "R$ 500,00" in result.rationale and "R$ 1.000,00" in result.rationale
    assert any(e.policy == "POL-1" and e.source == "DOC-2" for e in result.evidence)
