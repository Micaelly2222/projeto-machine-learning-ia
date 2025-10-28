"""
Interface visual para teste manual do verificador de processos.
Permite inserir dados via JSON e visualizar resultados de forma intuitiva.
"""
import streamlit as st
import requests
import json

# Configuração da página
st.set_page_config(
    page_title="Verificador de Processos",
    page_icon="⚖️",
    layout="wide"
)

# Título e descrição
st.title("⚖️ Verificador de Processos Judiciais")
st.markdown("""
**Analise automaticamente processos judiciais usando IA**  
Insira os dados do processo em JSON e receba uma decisão baseada nas políticas da empresa.
""")

# Sidebar com informações
with st.sidebar:
    st.header("ℹ️ Como usar")
    st.markdown("""
    1. Cole os dados do processo em JSON no campo abaixo
    2. Clique em **Analisar Processo** 
    3. Veja a decisão automatizada com justificativa
    """)
    
    st.header("📋 Políticas Aplicadas")
    st.markdown("""
    - POL-1: Trânsito em julgado obrigatório
    - POL-2: Valor de condenação informado
    - POL-3: Valor ≥ R$ 1.000,00
    - POL-4: Não trabalhista
    - POL-5: Sem óbito do autor
    - POL-6: Sem substabelecimento
    - POL-8: Documentação completa
    """)

# Área principal da aplicação
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📥 Dados do Processo")
    
    # Campo para entrada de dados
    processo_json = st.text_area(
        "Cole o JSON do processo aqui:",
        height=400,
        placeholder='{"numeroProcesso": "0001234-56.2023.4.05.8100", "classe": "...", ...}'
    )

with col2:
    st.subheader("🎯 Resultado")
    
    # Botão de análise
    if st.button("🔍 Analisar Processo", type="primary", use_container_width=True):
        if processo_json:
            try:
                # Valida e parseia JSON
                dados_processo = json.loads(processo_json)
                
                # Mostra spinner durante a análise
                with st.spinner("Analisando processo com IA..."):
                    response = requests.post(
                        "http://localhost:8000/analyze", 
                        json=dados_processo,
                        timeout=30
                    )
                
                if response.status_code == 200:
                    resultado = response.json()
                    
                    # Exibe resultado com formatação visual
                    st.success("✅ Análise concluída!")
                    
                    # Card de decisão colorido
                    decision_color = {
                        "approved": "🟢 APROVADO",
                        "rejected": "🔴 REJEITADO", 
                        "incomplete": "🟡 INCOMPLETO"
                    }
                    
                    st.markdown(f"### {decision_color.get(resultado['decision'], '⚪')}")
                    st.markdown(f"**Justificativa:** {resultado['rationale']}")
                    
                    # Políticas citadas
                    st.markdown("**Políticas aplicadas:**")
                    for citation in resultado.get('citations', []):
                        st.code(citation)
                        
                    # JSON completo (expansível)
                    with st.expander("Ver resposta completa em JSON"):
                        st.json(resultado)
                        
                else:
                    st.error(f"❌ Erro na API: {response.status_code} - {response.text}")
                    
            except json.JSONDecodeError:
                st.error("❌ JSON inválido. Verifique a formatação.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Não foi possível conectar à API. Verifique se o servidor está rodando.")
            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")
        else:
            st.warning("⚠️ Por favor, insira os dados do processo em JSON.")

# Seção de exemplo
with st.expander("📋 Exemplo de JSON válido"):
    st.code("""
{
    "numeroProcesso": "0001234-56.2023.4.05.8100",
    "classe": "Cumprimento de Sentença",
    "orgaoJulgador": "19a VARA FEDERAL - SOBRAL/CE", 
    "esfera": "Federal",
    "valorCondenacao": 15000.00,
    "documentos": [
        {
            "id": "DOC-1",
            "nome": "Certidão de Trânsito em Julgado",
            "texto": "..."
        }
    ],
    "movimentos": []
}
""")

# Rodapé
st.markdown("---")
st.markdown("*Desenvolvido para análise automatizada de processos judiciais*")