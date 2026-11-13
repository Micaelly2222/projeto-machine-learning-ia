import logging
from collections import Counter
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.analyzer import analyze, get_classifier
from app.config import settings
from app.policies import POLICIES
from app.schemas import AnalysisResult, BatchInput, BatchResult, CaseInput

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_classifier()
    yield


app = FastAPI(
    title="Análise de Processos Judiciais",
    description="Classifica documentos judiciais com Machine Learning, extrai fatos com regras ou LLM "
    "e decide cada processo com base em políticas explícitas.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])


@app.get("/")
def root() -> dict:
    return {"service": "legal-case-analyzer", "version": __version__, "docs": "/docs"}


@app.get("/health")
def health() -> dict:
    classifier = get_classifier()
    return {
        "status": "ok",
        "classifier_version": classifier.version,
        "llm_enabled": settings.llm_enabled,
    }


@app.get("/policies")
def policies() -> list[dict]:
    return [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "outcome_if_failed": p.outcome_if_failed.value if p.outcome_if_failed else None,
        }
        for p in POLICIES.values()
    ]


@app.get("/model")
def model_info() -> dict:
    return get_classifier().metadata


@app.post("/analyze", response_model=AnalysisResult)
def analyze_case(case: CaseInput) -> AnalysisResult:
    return analyze(case)


@app.post("/analyze/batch", response_model=BatchResult)
def analyze_batch(batch: BatchInput) -> BatchResult:
    results = [analyze(case) for case in batch.processos]
    summary = Counter(r.decision.value for r in results)
    return BatchResult(total=len(results), summary=dict(summary), results=results)
