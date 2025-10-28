"""
API principal do Verificador de Processos Judiciais.
Expõe endpoints REST para análise automatizada de processos.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Importa modelos e lógica de análise
from schemas import ProcessoInput, AnalysisResult
from analyzer import analyze_process

# Inicializa aplicação FastAPI com metadados
app = FastAPI(
    title="Verificador de Processos Judiciais",
    description="API para análise automatizada de processos baseada em políticas empresariais usando IA",
    version="1.0.0"
)

# Configura CORS para permitir requisições da interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check() -> dict:
    """
    Endpoint de health check para monitoramento da API.
    Retorna status do serviço e versão.
    """
    return {
        "status": "healthy", 
        "service": "Process Verifier API",
        "version": "1.0.0"
    }

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_process_endpoint(processo: ProcessoInput) -> AnalysisResult:
    """
    Endpoint principal para análise de processos judiciais.
    
    Recebe dados do processo, aplica políticas empresariais e retorna
    decisão automatizada com justificativa detalhada.
    
    Args:
        processo: Dados completos do processo judicial
        
    Returns:
        AnalysisResult: Decisão, justificativa e políticas aplicadas
    """
    try:
        # Converte para dict e chama o analisador
        process_dict = processo.dict()
        result = analyze_process(process_dict)
        
        # Valida se o resultado tem estrutura correta
        if not all(key in result for key in ["decision", "rationale", "citations"]):
            raise ValueError("Resposta do analisador em formato inválido")
            
        return AnalysisResult(**result)
        
    except Exception as e:
        # Log do erro e retorno de resposta adequada
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno na análise do processo: {str(e)}"
        )

# Ponto de entrada para execução local
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)