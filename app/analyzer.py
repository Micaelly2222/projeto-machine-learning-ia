import logging
from functools import lru_cache

from app import __version__
from app.classifier import DocumentClassifier
from app.config import settings
from app.engine import decide
from app.extraction import extract_facts, type_from_name
from app.llm import LLMUnavailable, extract_with_llm
from app.schemas import AnalysisResult, CaseFacts, CaseInput, DocumentPrediction

logger = logging.getLogger(__name__)

RISK_FACTS = ("plaintiff_deceased", "substitution_without_reservation")
SUPPORT_FACTS = ("final_judgment", "has_merit_decision", "has_calculation")


@lru_cache(maxsize=1)
def get_classifier() -> DocumentClassifier:
    if not settings.model_path.exists():
        from scripts.train import train_and_save

        logger.warning("Model not found at %s, training a new one", settings.model_path)
        train_and_save()
    return DocumentClassifier.load(settings.model_path)


def classify_documents(case: CaseInput, classifier: DocumentClassifier) -> list[DocumentPrediction]:
    if not case.documentos:
        return []
    texts = [f"{d.nome}. {d.texto}" for d in case.documentos]
    predictions = classifier.predict(texts)
    results = []
    for doc, pred in zip(case.documentos, predictions):
        # O nome do documento tem prioridade; o classificador cobre nomes genéricos como "Documento 1"
        by_name = type_from_name(doc.nome)
        if by_name:
            doc_type, source = by_name, "name"
        elif pred.confidence >= settings.classifier_min_confidence:
            doc_type, source = pred.label, "classifier"
        else:
            doc_type, source = "desconhecido", "unknown"
        results.append(
            DocumentPrediction(
                id=doc.id,
                name=doc.nome,
                document_type=doc_type,
                type_source=source,
                classifier_label=pred.label,
                classifier_confidence=round(pred.confidence, 4),
                top_terms=pred.top_terms,
            )
        )
    return results


# O LLM só complementa: todo fato vindo dele já passou pela checagem de citação.
def merge_facts(rules: CaseFacts, llm: CaseFacts) -> CaseFacts:
    merged = rules.model_copy(deep=True)
    merged.source = "llm+rules"
    for name in RISK_FACTS + SUPPORT_FACTS:
        setattr(merged, name, getattr(rules, name) or getattr(llm, name))
    if merged.award_amount is None:
        merged.award_amount = llm.award_amount
    merged.attorney_fees = rules.attorney_fees or llm.attorney_fees
    known = {(e.policy, e.source) for e in merged.evidence}
    merged.evidence += [e for e in llm.evidence if (e.policy, e.source) not in known]
    return merged


def analyze(case: CaseInput, classifier: DocumentClassifier | None = None, use_llm: bool | None = None) -> AnalysisResult:
    classifier = classifier or get_classifier()
    documents = classify_documents(case, classifier)
    facts = extract_facts(case, documents)

    use_llm = settings.llm_enabled if use_llm is None else use_llm
    if use_llm:
        try:
            facts = merge_facts(facts, extract_with_llm(case))
        except LLMUnavailable as exc:
            logger.warning("LLM extraction skipped for %s: %s", case.numeroProcesso, exc)

    decision, rationale, citations, checks = decide(facts)
    return AnalysisResult(
        numeroProcesso=case.numeroProcesso,
        decision=decision,
        rationale=rationale,
        citations=citations,
        checks=checks,
        evidence=facts.evidence,
        documents=documents,
        facts=facts,
        extraction_source=facts.source,
        model_version=f"app {__version__} / classifier {classifier.version}",
    )
