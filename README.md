<p align="center"><a href="#english">English</a> · <a href="#portugues">Português</a></p>

<a id="english"></a>

# English

## ⚖️ Legal Case Analysis System with Machine Learning

An intelligent system for the automatic analysis and classification of legal proceedings using Machine Learning and AI techniques.

### 🚀 Main Features

- **🤖 Automated ML Analysis**: Intelligent classification of cases  
- **📊 Complete Explainability**: Detailed justifications for each decision  
- **🌐 Multiple Interfaces**: REST API + visual interface  
- **🐳 Containerized Deployment**: Production-ready with Docker  

### 🛠️ Technologies

- **Python** – Programming language  
- **FastAPI** – Web API framework  
- **Streamlit** – Web interface framework  
- **Docker** – Containerization platform  

### 🏃‍♂️ How to Run

#### Option 1: Docker

```sh
docker build -t projeto-machine-learning-ia .

docker run -p 8000:8000 projeto-machine-learning-ia
```

#### Option 2: Local development

```sh
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000

streamlit run streamlit_app.py
```

### 🌐 Access

- **API:** http://localhost:8000  
- **API documentation:** http://localhost:8000/docs  
- **Web interface:** http://localhost:8501

---

<a id="portugues"></a>

# Português

## ⚖️ Sistema de Análise de Processos Judiciais com Machine Learning

Sistema inteligente para análise e classificação automática de processos judiciais utilizando técnicas de Machine Learning e IA.

### 🚀 Funcionalidades Principais

- **🤖 Análise Automatizada com ML**: Classificação inteligente de processos  
- **📊 Explicabilidade Completa**: Justificativas detalhadas das decisões  
- **🌐 Múltiplas Interfaces**: API REST + Interface visual  
- **🐳 Deploy Containerizado**: Pronto para produção com Docker  

### 🛠️ Tecnologias Utilizadas

- **Python** – Linguagem de programação  
- **FastAPI** – Framework para API web  
- **Streamlit** – Framework para interface web  
- **Docker** – Plataforma de containerização  

### 🏃‍♂️ Como Executar

#### Opção 1: Docker

```sh
docker build -t projeto-machine-learning-ia .

docker run -p 8000:8000 projeto-machine-learning-ia
```

#### Opção 2: Desenvolvimento Local

```sh
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000

streamlit run streamlit_app.py
```

### 🌐 Acesso

- **API:** http://localhost:8000  
- **Documentação da API:** http://localhost:8000/docs  
- **Interface Web:** http://localhost:8501
