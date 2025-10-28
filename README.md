# ⚖️ Sistema de Análise de Processos Judiciais com Machine Learning

Sistema inteligente para análise e classificação automática de processos judiciais utilizando técnicas de Machine Learning e IA.

## 🚀 Funcionalidades Principais

- **🤖 Análise Automatizada com ML**: Classificação inteligente de processos  
- **📊 Explicabilidade Completa**: Justificativas detalhadas das decisões  
- **🌐 Múltiplas Interfaces**: API REST + Interface visual  
- **🐳 Deploy Containerizado**: Pronto para produção com Docker  

## 🛠️ Tecnologias Utilizadas

- **Python** – Linguagem de programação  
- **FastAPI** – Framework para API web  
- **Streamlit** – Framework para interface web  
- **Docker** – Plataforma de containerização  

## 🏃‍♂️ Como Executar

### Opção 1: Docker
docker build -t projeto-machine-learning-ia .

docker run -p 8000:8000 projeto-machine-learning-ia

### Opção 2: Desenvolvimento Local
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000

streamlit run streamlit_app.py

## 🌐 Acesso

- **API:** http://localhost:8000  
- **Documentação da API:** http://localhost:8000/docs  
- **Interface Web:** http://localhost:8501
