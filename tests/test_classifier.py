from app.analyzer import classify_documents
from app.schemas import CaseInput
from tests.conftest import make_case


def test_classificador_reconhece_tipos(classifier):
    textos = {
        "certidao_transito_julgado": "Certifico que a decisão transitou em julgado em 14/02/2024, sem recurso.",
        "calculos": "Planilha de atualização. Principal corrigido, juros de mora. Total geral atualizado: R$ 31.250,00.",
        "certidao_obito": "Registro Civil. Consta o óbito de João Silva, falecido em 02/01/2024.",
        "procuracao": "Por este instrumento, nomeio e constituo meu procurador o advogado, com poderes ad judicia.",
    }
    predictions = classifier.predict(list(textos.values()))
    for expected, pred in zip(textos, predictions):
        assert pred.label == expected
        assert 0 < pred.confidence <= 1
        assert pred.top_terms


def test_nome_generico_usa_classificador(classifier):
    docs = [{"id": "DOC-1", "nome": "Documento 7",
             "texto": "CERTIFICO E DOU FÉ que a sentença transitou em julgado em 01/02/2024."}]
    result = classify_documents(CaseInput(**make_case(documentos=docs)), classifier)
    assert result[0].type_source == "classifier"
    assert result[0].document_type == "certidao_transito_julgado"


def test_nome_conhecido_tem_prioridade(classifier):
    result = classify_documents(CaseInput(**make_case()), classifier)
    assert [d.type_source for d in result] == ["name", "name", "name"]


def test_metricas_salvas_no_modelo(classifier):
    meta = classifier.metadata
    assert meta["cross_validation"]["accuracy_mean"] > 0.7
    assert set(meta["classes"]) >= {"sentenca", "calculos", "certidao_transito_julgado"}
