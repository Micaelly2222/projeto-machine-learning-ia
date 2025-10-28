# ⚖️ Verificador de Processos Judiciais

Sistema automatizado para análise de processos judiciais usando IA, baseado em políticas empresariais.

## 🚀 Funcionalidades

- **Análise Automatizada**: Decide entre `approved`, `rejected` ou `incomplete`
- **Explicabilidade**: Justificativa detalhada com citações das políticas
- **Interface Dupla**: API REST + Interface visual (Streamlit)
- **Deploy Containerizado**: Pronto para produção com Docker

## 🛠️ Tecnologias

- **FastAPI**: API moderna com documentação automática
- **LLM Integration**: Análise inteligente com Mistral (Ollama)
- **Streamlit**: Interface visual intuitiva  
- **Docker**: Containerização e deploy
- **Pydantic**: Validação de dados robusta

## 📦 Estrutura do Projeto

ml-process-verifier/
├── app/
│ ├── main.py # API FastAPI principal
│ ├── analyzer.py # Lógica de análise (LLM + regras)
│ └── schemas.py # Modelos de dados
├── streamlit_app.py # Interface visual
├── requirements.txt # Dependências
├── Dockerfile # Configuração do container
└── README.md # Esta documentação


## 🏃‍♂️ Execução Local

### Opção 1: Docker (Recomendado)

```bash
# Build da imagem
docker build -t process-verifier .

# Executar container
docker run -p 8000:8000 process-verifier


### Opção 2: Python Nativo

# Instalar dependências
pip install -r requirements.txt

# Executar API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Em outro terminal, executar interface
streamlit run streamlit_app.py
