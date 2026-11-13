import json
from pathlib import Path

import pytest

from app.analyzer import get_classifier

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def classifier():
    return get_classifier()


@pytest.fixture(scope="session")
def cases():
    return json.loads((ROOT / "data" / "cases.json").read_text(encoding="utf-8"))


def make_case(**overrides):
    base = {
        "numeroProcesso": "0001234-56.2023.4.05.8100",
        "classe": "Cumprimento de Sentença",
        "esfera": "Federal",
        "valorCondenacao": 15000.0,
        "documentos": [
            {"id": "DOC-1", "nome": "Sentença", "texto": "Julgo procedente o pedido."},
            {"id": "DOC-2", "nome": "Certidão de Trânsito em Julgado", "texto": "A sentença transitou em julgado em 10/03/2024."},
            {"id": "DOC-3", "nome": "Planilha de Cálculos", "texto": "Total geral: R$ 15.000,00."},
        ],
        "movimentos": [],
    }
    base.update(overrides)
    return base
