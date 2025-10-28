"""
Definição dos modelos de dados (schemas) usando Pydantic.
Garante validação automática dos dados de entrada da API.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Documento(BaseModel):
    """Modelo para documentos do processo judicial"""
    id: str
    dataHoraJuntada: str
    nome: str
    texto: str

class ProcessoInput(BaseModel):
    """Modelo principal para recebimento de dados do processo"""
    numeroProcesso: str
    classe: str
    orgaoJulgador: str
    ultimaDistribuicao: str
    assunto: str
    segredoJustica: bool
    justicaGratuita: bool
    siglaTribunal: str
    esfera: str
    valorCondenacao: Optional[float] = None  # Opcional para casos incompletos
    documentos: List[Documento]
    movimentos: List[Dict[str, Any]]

class AnalysisResult(BaseModel):
    """Modelo para padronizar a resposta da análise"""
    decision: str  # "approved", "rejected", ou "incomplete"
    rationale: str  # Justificativa detalhada da decisão
    citations: List[str]  # Lista de políticas aplicadas (ex: ["POL-1", "POL-3"])