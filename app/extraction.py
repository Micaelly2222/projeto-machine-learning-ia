import re

from app.schemas import CaseFacts, CaseInput, DocumentPrediction, Evidence
from app.text import MONEY, excerpt, find_affirmed, format_brl, normalize, normalize_aligned, parse_brl

# Numeração única do CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO, em que J=5 é a Justiça do Trabalho
CNJ_NUMBER = re.compile(r"^\d{7}-\d{2}\.\d{4}\.(\d)\.\d{2}\.\d{4}$")
LABOR_JUSTICE_SEGMENT = "5"

NAME_RULES = [
    ("certidao_transito_julgado", re.compile(r"transito em julgado")),
    ("certidao_obito", re.compile(r"certidao de obito|obito")),
    ("substabelecimento", re.compile(r"substabelecimento")),
    ("calculos", re.compile(r"calculo|planilha|demonstrativo de debito|memoria de calculo")),
    ("acordao", re.compile(r"acordao")),
    ("sentenca", re.compile(r"sentenca")),
    ("procuracao", re.compile(r"procuracao")),
    ("despacho", re.compile(r"despacho|decisao interlocutoria")),
    ("peticao", re.compile(r"peticao")),
]

# "transitou em julgado" afirma um fato; "trânsito em julgado" sozinho aparece também em frases
# futuras ("após o trânsito em julgado, arquive-se") e só vale em certidão ou movimento.
FINAL_JUDGMENT_CERTIFIED = re.compile(r"transitou em julgado|transitado em julgado")
FINAL_JUDGMENT_MENTION = re.compile(r"transito em julgado")
DEATH = re.compile(r"\b(obito|falecimento|faleceu|falecido|falecida)\b")
SUBSTITUTION_WITHOUT_RESERVATION = re.compile(r"sem (a )?reservas? de (iguais )?poderes")
AMOUNT_LABEL = re.compile(
    r"(total (geral|devido|da execucao|atualizado)?|valor (total|da condenacao|devido|atualizado))"
    r".{0,40}?r\$\s*([\d.]+,\d{2})"
)
ATTORNEY_FEES = re.compile(
    r"honorarios (advocaticios |contratuais |sucumbenciais |periciais )?[^.;]{0,60}?r\$\s*([\d.]+,\d{2})"
)


def type_from_name(name: str) -> str | None:
    normalized = normalize(name)
    for label, pattern in NAME_RULES:
        if pattern.search(normalized):
            return label
    return None


def is_labor_case(case: CaseInput) -> tuple[bool, str | None]:
    if case.esfera and "trabalh" in normalize(case.esfera):
        return True, f"esfera: {case.esfera}"
    match = CNJ_NUMBER.match(case.numeroProcesso.strip())
    if match and match.group(1) == LABOR_JUSTICE_SEGMENT:
        return True, f"numeroProcesso {case.numeroProcesso} (segmento J=5, Justiça do Trabalho)"
    return False, None


def extract_facts(case: CaseInput, documents: list[DocumentPrediction]) -> CaseFacts:
    facts = CaseFacts(source="rules")
    types = {d.id: d.document_type for d in documents}

    labor, labor_source = is_labor_case(case)
    if labor:
        facts.is_labor_court = True
        facts.evidence.append(Evidence(policy="POL-4", source="dados do processo", excerpt=labor_source))

    if case.valorCondenacao is not None:
        facts.award_amount = case.valorCondenacao
        facts.evidence.append(
            Evidence(policy="POL-2", source="valorCondenacao", excerpt=format_brl(case.valorCondenacao))
        )

    for movement in case.movimentos:
        text = normalize(movement.descricao)
        match = find_affirmed(FINAL_JUDGMENT_MENTION, text) or find_affirmed(FINAL_JUDGMENT_CERTIFIED, text)
        if match and not facts.final_judgment:
            facts.final_judgment = True
            facts.evidence.append(Evidence(policy="POL-1", source="movimento", excerpt=movement.descricao))

    for doc in case.documentos:
        doc_type = types.get(doc.id, "unknown")
        text = normalize_aligned(doc.texto)

        if doc_type in ("sentenca", "acordao"):
            facts.has_merit_decision = True
        if doc_type == "calculos":
            facts.has_calculation = True

        if not facts.final_judgment:
            match = find_affirmed(FINAL_JUDGMENT_CERTIFIED, text)
            if not match and doc_type == "certidao_transito_julgado":
                match = find_affirmed(FINAL_JUDGMENT_MENTION, text)
            if match:
                facts.final_judgment = True
                facts.evidence.append(
                    Evidence(policy="POL-1", source=doc.id, excerpt=excerpt(doc.texto, match.start(), match.end()))
                )

        if facts.award_amount is None and doc_type == "calculos":
            amount = AMOUNT_LABEL.search(text) or MONEY.search(text)
            if amount:
                value = amount.group(amount.lastindex)
                facts.award_amount = parse_brl(value)
                facts.evidence.append(
                    Evidence(policy="POL-2", source=doc.id, excerpt=excerpt(doc.texto, amount.start(), amount.end()))
                )

        death = find_affirmed(DEATH, text)
        if death and (doc_type == "certidao_obito" or re.search(r"\b(autor|autora|exequente|requerente)\b", text)):
            facts.plaintiff_deceased = True
            facts.evidence.append(
                Evidence(policy="POL-5", source=doc.id, excerpt=excerpt(doc.texto, death.start(), death.end()))
            )

        if doc_type == "substabelecimento" or "substabelec" in text:
            match = SUBSTITUTION_WITHOUT_RESERVATION.search(text)
            if match:
                facts.substitution_without_reservation = True
                facts.evidence.append(
                    Evidence(policy="POL-6", source=doc.id, excerpt=excerpt(doc.texto, match.start(), match.end()))
                )

        for fee in ATTORNEY_FEES.finditer(text):
            kind = (fee.group(1) or "").strip() or "advocaticios"
            facts.attorney_fees.append(f"{kind}: R$ {fee.group(2)} ({doc.id})")

    if facts.attorney_fees:
        facts.evidence.append(
            Evidence(policy="POL-7", source="documentos", excerpt="; ".join(facts.attorney_fees))
        )
    return facts
