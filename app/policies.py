from dataclasses import dataclass

from app.schemas import Decision


@dataclass(frozen=True)
class Policy:
    id: str
    title: str
    description: str
    outcome_if_failed: Decision | None  # None = política apenas informativa


POLICIES: dict[str, Policy] = {
    p.id: p
    for p in [
        Policy(
            "POL-1",
            "Trânsito em julgado",
            "O processo precisa ter trânsito em julgado certificado. Sem isso, fica incompleto.",
            Decision.INCOMPLETE,
        ),
        Policy(
            "POL-2",
            "Valor da condenação informado",
            "O valor da condenação deve estar nos dados do processo ou na planilha de cálculos.",
            Decision.INCOMPLETE,
        ),
        Policy(
            "POL-3",
            "Valor mínimo",
            "Condenações abaixo do valor mínimo (padrão R$ 1.000,00) são rejeitadas.",
            Decision.REJECTED,
        ),
        Policy(
            "POL-4",
            "Não trabalhista",
            "Processos da Justiça do Trabalho são rejeitados.",
            Decision.REJECTED,
        ),
        Policy(
            "POL-5",
            "Sem óbito da parte autora",
            "Processos com registro de óbito da parte autora são rejeitados.",
            Decision.REJECTED,
        ),
        Policy(
            "POL-6",
            "Sem substabelecimento sem reserva",
            "Substabelecimento sem reserva de poderes transfere o mandato e leva à rejeição.",
            Decision.REJECTED,
        ),
        Policy(
            "POL-7",
            "Honorários identificados",
            "Os honorários encontrados nos documentos são informados. Esta política não altera a decisão.",
            None,
        ),
        Policy(
            "POL-8",
            "Documentos essenciais",
            "O processo deve ter decisão de mérito (sentença ou acórdão) e planilha de cálculos.",
            Decision.INCOMPLETE,
        ),
    ]
}
