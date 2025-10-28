"""
Módulo central de análise de processos judiciais.
Implementa a lógica de negócio baseada nas políticas da empresa.
"""
import json
import requests
from typing import Dict, Any

# Política empresarial para análise de processos
POLICY = """
POL-1: Apenas processos transitados em julgado e em fase de execução são elegíveis
POL-2: Valor de condenação deve estar claramente informado
POL-3: Processos com valor inferior a R$ 1.000,00 são rejeitados
POL-4: Processos na esfera trabalhista são automaticamente rejeitados
POL-5: Óbito do autor sem habilitação no inventário resulta em rejeição
POL-6: Substabelecimento sem reserva de poderes resulta em rejeição
POL-7: Honorários devem ser informados quando existirem
POL-8: Falta de documento essencial resulta em status 'incomplete'
"""

def analyze_process(process_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analisa um processo judicial com base nas políticas da empresa.
    
    Args:
        process_data: Dicionário com dados do processo judicial
        
    Returns:
        Dict com decisão, justificativa e citações das políticas aplicadas
    """
    # Tenta usar LLM para análise inteligente (se disponível)
    llm_result = _try_llm_analysis(process_data)
    if llm_result:
        return llm_result
    
    # Fallback: análise baseada em regras (garante funcionamento)
    return _rule_based_analysis(process_data)

def _try_llm_analysis(process_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tenta análise usando LLM local (Ollama + Mistral).
    Retorna None se não conseguir conectar.
    """
    prompt = f"""
    {POLICY}

    Analise o processo judicial abaixo e retorne APENAS um JSON com:
    - decision: "approved", "rejected" ou "incomplete"
    - rationale: justificativa detalhada em português
    - citations: lista de políticas aplicadas (ex: ["POL-1", "POL-3"])

    Dados do processo:
    {json.dumps(process_data, indent=2, ensure_ascii=False)}
    """
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral", "prompt": prompt, "format": "json", "stream": False},
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get("response", {})
    except Exception:
        pass
    
    return None

def _rule_based_analysis(process_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Análise baseada em regras fixas - funciona mesmo sem LLM.
    """
    documentos = process_data.get("documentos", [])
    
    # Verifica trânsito em julgado (POL-1, POL-8)
    tem_transito_julgado = any(
        doc["nome"].lower() in ["certidão de trânsito em julgado", "trânsito em julgado"] 
        for doc in documentos
    )
    
    if not tem_transito_julgado:
        return {
            "decision": "incomplete",
            "rationale": "Documentação incompleta: trânsito em julgado não comprovado.",
            "citations": ["POL-1", "POL-8"]
        }
    
    # Verifica valor da condenação (POL-2, POL-3)
    valor_condenacao = process_data.get("valorCondenacao", 0)
    if not valor_condenacao or valor_condenacao == 0:
        return {
            "decision": "incomplete", 
            "rationale": "Valor de condenação não informado ou zerado.",
            "citations": ["POL-2", "POL-8"]
        }
    
    if valor_condenacao < 1000:
        return {
            "decision": "rejected",
            "rationale": f"Valor de condenação (R$ {valor_condenacao:,.2f}) abaixo do mínimo permitido de R$ 1.000,00.",
            "citations": ["POL-3"]
        }
    
    # Verifica esfera trabalhista (POL-4)
    if process_data.get("esfera", "").lower() == "trabalhista":
        return {
            "decision": "rejected",
            "rationale": "Processos da esfera trabalhista não são elegíveis para aquisição.",
            "citations": ["POL-4"]
        }
    
    # Verifica óbito do autor (POL-5)
    tem_obito = any("óbito" in doc["nome"].lower() or "obito" in doc["nome"].lower() 
                   for doc in documentos)
    if tem_obito:
        return {
            "decision": "rejected",
            "rationale": "Óbito do autor detectado na documentação.",
            "citations": ["POL-5"]
        }
    
    # Verifica substabelecimento (POL-6)
    tem_substabelecimento = any("substabelecimento" in doc["nome"].lower() 
                               for doc in documentos)
    if tem_substabelecimento:
        return {
            "decision": "rejected", 
            "rationale": "Substabelecimento sem reserva de poderes detectado.",
            "citations": ["POL-6"]
        }
    
    # Se passou por todas as verificações
    return {
        "decision": "approved",
        "rationale": "Processo atende todos os critérios da política: trânsito em julgado comprovado, valor adequado, esfera elegível e documentação completa.",
        "citations": ["POL-1", "POL-2"]
    }