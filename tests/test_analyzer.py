"""
Testes automatizados para o sistema de análise de processos judiciais
Garante que a lógica de Machine Learning e IA funciona corretamente
"""
import pytest
from app.analyzer import analyze_process

def test_processo_aprovado():
    """Testa um processo que deve ser APROVADO"""
    processo = {
        "numeroProcesso": "0001234-56.2023.4.05.8100",
        "classe": "Cumprimento de Sentença",
        "orgaoJulgador": "19a VARA FEDERAL - SOBRAL/CE",
        "esfera": "Federal",
        "valorCondenacao": 15000.00,
        "documentos": [
            {
                "id": "DOC-1",
                "nome": "Certidão de Trânsito em Julgado",
                "texto": "Certifico que o processo transitou em julgado..."
            }
        ],
        "movimentos": []
    }
    
    resultado = analyze_process(processo)
    assert resultado["decision"] == "approved"
    assert "POL-1" in resultado["citations"]

def test_processo_trabalhista_rejeitado():
    """Testa que processos TRABALHISTAS são rejeitados"""
    processo = {
        "numeroProcesso": "0100001-11.2023.5.02.0001",
        "classe": "Cumprimento de Sentença",
        "esfera": "Trabalhista",
        "valorCondenacao": 5000.00,
        "documentos": [
            {
                "id": "DOC-1",
                "nome": "Certidão de Trânsito em Julgado", 
                "texto": "Certifico o trânsito em julgado..."
            }
        ],
        "movimentos": []
    }
    
    resultado = analyze_process(processo)
    assert resultado["decision"] == "rejected"
    assert "POL-4" in resultado["citations"]

def test_processo_valor_baixo_rejeitado():
    """Testa que processos com valor < R$ 1000 são rejeitados"""
    processo = {
        "numeroProcesso": "0023456-78.2022.4.05.0000",
        "classe": "Cumprimento de Sentença",
        "esfera": "Federal", 
        "valorCondenacao": 500.00,
        "documentos": [
            {
                "id": "DOC-1",
                "nome": "Certidão de Trânsito em Julgado",
                "texto": "Trânsito em julgado confirmado..."
            }
        ],
        "movimentos": []
    }
    
    resultado = analyze_process(processo)
    assert resultado["decision"] == "rejected"
    assert "POL-3" in resultado["citations"]

def test_processo_incompleto_sem_transito():
    """Testa processo INCOMPLETO sem trânsito em julgado"""
    processo = {
        "numeroProcesso": "0704321-00.2021.8.26.0100", 
        "classe": "Cumprimento de Sentença",
        "esfera": "Federal",
        "valorCondenacao": 2000.00,
        "documentos": [
            {
                "id": "DOC-1",
                "nome": "Sentença de Mérito",
                "texto": "Julgou procedente o pedido..."
            }
            # Faltando certidão de trânsito em julgado
        ],
        "movimentos": []
    }
    
    resultado = analyze_process(processo)
    assert resultado["decision"] == "incomplete"
    assert "POL-8" in resultado["citations"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])