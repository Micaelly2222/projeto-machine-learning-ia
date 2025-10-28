from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .schemas import ProcessoInput, AnalysisResult
from .analyzer import AnalisadorProcessos

app = FastAPI(title="Sistema de Análise de Processos Judiciais")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instanciar o analisador
analisador = AnalisadorProcessos()

@app.get("/")
async def root():
    return {"message": "Sistema de Análise de Processos Judiciais"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "process-analyzer"}

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_process(processo: ProcessoInput):
    """Analisa um processo judicial e retorna a decisão"""
    resultado = analisador.analisar_processo(
        processo.texto_processo,
        processo.politicas
    )
    return resultado