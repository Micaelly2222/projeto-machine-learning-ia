from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    id: str
    dataHoraJuntada: str | None = None
    nome: str = ""
    texto: str = ""


class Movement(BaseModel):
    model_config = ConfigDict(extra="allow")

    dataHora: str | None = None
    descricao: str = ""


class CaseInput(BaseModel):
    numeroProcesso: str
    classe: str | None = None
    orgaoJulgador: str | None = None
    ultimaDistribuicao: str | None = None
    assunto: str | None = None
    segredoJustica: bool = False
    justicaGratuita: bool = False
    siglaTribunal: str | None = None
    esfera: str | None = None
    valorCondenacao: float | None = Field(default=None, ge=0)
    documentos: list[Document] = Field(default_factory=list)
    movimentos: list[Movement] = Field(default_factory=list)


class Decision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    INCOMPLETE = "incomplete"


class Evidence(BaseModel):
    policy: str
    source: str
    excerpt: str


class DocumentPrediction(BaseModel):
    id: str
    name: str
    document_type: str
    type_source: Literal["name", "classifier", "unknown"]
    classifier_label: str | None = None
    classifier_confidence: float | None = None
    top_terms: list[str] = Field(default_factory=list)


class CaseFacts(BaseModel):
    final_judgment: bool = False
    award_amount: float | None = None
    is_labor_court: bool = False
    plaintiff_deceased: bool = False
    substitution_without_reservation: bool = False
    has_merit_decision: bool = False
    has_calculation: bool = False
    attorney_fees: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    source: Literal["rules", "llm", "llm+rules"] = "rules"


class PolicyCheck(BaseModel):
    policy: str
    title: str
    passed: bool
    outcome_if_failed: Decision | None


class AnalysisResult(BaseModel):
    numeroProcesso: str
    decision: Decision
    rationale: str
    citations: list[str]
    checks: list[PolicyCheck]
    evidence: list[Evidence]
    documents: list[DocumentPrediction]
    facts: CaseFacts
    extraction_source: str
    model_version: str


class BatchInput(BaseModel):
    processos: list[CaseInput] = Field(min_length=1, max_length=100)


class BatchResult(BaseModel):
    total: int
    summary: dict[str, int]
    results: list[AnalysisResult]
