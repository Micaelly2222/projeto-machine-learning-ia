from app.config import settings
from app.policies import POLICIES
from app.schemas import CaseFacts, Decision, PolicyCheck
from app.text import format_brl


def check_policies(facts: CaseFacts, min_amount: float | None = None) -> list[PolicyCheck]:
    min_amount = settings.min_award_amount if min_amount is None else min_amount
    amount_known = facts.award_amount is not None
    results = {
        "POL-1": facts.final_judgment,
        "POL-2": amount_known,
        "POL-3": (not amount_known) or facts.award_amount >= min_amount,
        "POL-4": not facts.is_labor_court,
        "POL-5": not facts.plaintiff_deceased,
        "POL-6": not facts.substitution_without_reservation,
        "POL-7": True,
        "POL-8": facts.has_merit_decision and facts.has_calculation,
    }
    return [
        PolicyCheck(
            policy=pid,
            title=POLICIES[pid].title,
            passed=passed,
            outcome_if_failed=POLICIES[pid].outcome_if_failed,
        )
        for pid, passed in results.items()
    ]


def missing_documents(facts: CaseFacts) -> list[str]:
    missing = []
    if not facts.has_merit_decision:
        missing.append("sentença ou acórdão")
    if not facts.has_calculation:
        missing.append("planilha de cálculos")
    return missing


def failure_reason(policy: str, facts: CaseFacts, min_amount: float) -> str:
    if policy == "POL-1":
        return "não há certidão ou registro de trânsito em julgado"
    if policy == "POL-2":
        return "o valor da condenação não foi informado nem encontrado nos cálculos"
    if policy == "POL-3":
        return f"o valor da condenação ({format_brl(facts.award_amount)}) é menor que o mínimo de {format_brl(min_amount)}"
    if policy == "POL-4":
        return "o processo é da Justiça do Trabalho"
    if policy == "POL-5":
        return "há registro de óbito da parte autora"
    if policy == "POL-6":
        return "há substabelecimento sem reserva de poderes"
    if policy == "POL-8":
        return "faltam documentos essenciais: " + ", ".join(missing_documents(facts))
    return POLICIES[policy].description


def decide(facts: CaseFacts, min_amount: float | None = None) -> tuple[Decision, str, list[str], list[PolicyCheck]]:
    min_amount = settings.min_award_amount if min_amount is None else min_amount
    checks = check_policies(facts, min_amount)
    failed = [c for c in checks if not c.passed]
    rejected = [c for c in failed if c.outcome_if_failed == Decision.REJECTED]
    incomplete = [c for c in failed if c.outcome_if_failed == Decision.INCOMPLETE]

    if rejected:
        decision, blocking = Decision.REJECTED, rejected
    elif incomplete:
        decision, blocking = Decision.INCOMPLETE, incomplete
    else:
        decision, blocking = Decision.APPROVED, []

    if blocking:
        reasons = [f"{c.policy}: {failure_reason(c.policy, facts, min_amount)}" for c in blocking]
        label = "Rejeitado" if decision == Decision.REJECTED else "Incompleto"
        rationale = f"{label}. " + "; ".join(reasons) + "."
        citations = [c.policy for c in blocking]
    else:
        rationale = (
            f"Aprovado. Trânsito em julgado comprovado, valor de {format_brl(facts.award_amount)}, "
            "documentos essenciais presentes e nenhuma restrição encontrada."
        )
        citations = [c.policy for c in checks if c.policy != "POL-7"]

    if facts.attorney_fees:
        rationale += " Honorários identificados (POL-7): " + "; ".join(facts.attorney_fees) + "."
        citations.append("POL-7")

    return decision, rationale, citations, checks
