<p align="center"><a href="#english">English</a> · <a href="#portugues">Português</a></p>

<a id="english"></a>

# English

## Legal Case Analyzer

**Decide whether a Brazilian court case meets a credit-purchase policy, with the reason and the exact document passage behind each decision.**

The system reads the case data and its documents (sentences, appeals rulings, final judgment certificates, calculation spreadsheets, death certificates, powers of attorney) and returns **approved**, **rejected** or **incomplete**, the policies that decided it, and the evidence found in each document.

It works in three steps:

1. **Machine Learning document classifier.** TF-IDF (words and character n-grams) + Logistic Regression in scikit-learn identifies 9 document types, even when the file name is generic, such as "Documento 1". Each prediction comes with a confidence score and the terms that weighed most.
2. **Fact extraction.** Rules with negation handling find the facts each policy needs: final judgment, award amount, labor court, plaintiff's death, substitution of powers without reservation and attorney fees. An optional **LLM step (Claude API, structured output)** adds facts that the rules miss. Every LLM fact must come with a quote that exists in the document, or it is discarded. Personal data (CPF, CNPJ, e-mail, phone) is masked before any text is sent to the model.
3. **Policy engine.** Deterministic rules turn the facts into a decision. The LLM never decides; it only extracts facts.

### Results

| Check | Result |
|---|---|
| Document classifier, 5-fold cross-validation grouped by template | **0.87 accuracy** (± 0.06), 0.85 macro F1 |
| Document classifier, templates never seen in training | 1.00 accuracy (225 documents) |
| End-to-end decisions on the 12 reference cases | **12/12 correct** |
| Automated tests (pytest) | **31 passed** |

Grouped cross-validation is the honest number: the model is tested on writing patterns it did not see during training. Full report in [reports/classifier_report.md](reports/classifier_report.md).

**About the data:** the 1,350 training documents are synthetic. They were generated from templates based on real court documents, with random names, courts, amounts and OCR-like noise ([scripts/generate_dataset.py](scripts/generate_dataset.py)). No real case data is used.

### Run it

Requires **Python 3.11+**. Open a terminal in the project folder:

```sh
pip install -r requirements-dev.txt
python -m scripts.train
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000` and the interactive docs (Swagger) at `http://localhost:8000/docs`.

Visual interface, in a second terminal:

```sh
streamlit run streamlit_app.py
```

Tests and the decision evaluation:

```sh
python -m pytest -v
python -m scripts.evaluate
```

Expected result: **31 tests passed** and **12/12 correct**.

With Docker, API and interface together:

```sh
docker compose up --build
```

API on port 8000, interface on port 8501. The image trains the classifier during the build.

### Turn on the LLM step (optional)

Copy `.env.example` to `.env`, set `LLM_ENABLED=true` and `ANTHROPIC_API_KEY`. Without a key, the system runs on rules and Machine Learning only. If the API fails, refuses or times out, the analysis continues without the LLM.

```sh
python -m scripts.evaluate --llm
```

### Endpoints

| Method | Route | What it does |
|---|---|---|
| POST | `/analyze` | Analyzes one case |
| POST | `/analyze/batch` | Analyzes up to 100 cases and returns a summary |
| GET | `/policies` | Lists the policies |
| GET | `/model` | Classifier version and metrics |
| GET | `/health` | Service status |

### Policies

| Policy | Rule | If it fails |
|---|---|---|
| POL-1 | Final judgment (trânsito em julgado) certified | incomplete |
| POL-2 | Award amount informed | incomplete |
| POL-3 | Award of at least R$ 1,000.00 | rejected |
| POL-4 | Not a labor court case | rejected |
| POL-5 | No record of the plaintiff's death | rejected |
| POL-6 | No substitution of powers without reservation | rejected |
| POL-7 | Attorney fees identified | informative only |
| POL-8 | Merit decision and calculation spreadsheet present | incomplete |

A rejection takes priority over an incomplete case.

### How decisions work

A sentence that says *"after the final judgment, archive the case"* does not prove a final judgment. Only *"transitou em julgado"* in a document, or a certificate or a case movement, counts, and negated sentences such as *"ainda não transitou em julgado"* are ignored.

For example, the case `0100001-11.2023.5.02.0001` is **rejected under POL-4** even with `esfera: "Estadual"`, because digit 5 in the CNJ number identifies the Labor Court. A case with a *substabelecimento com reserva de poderes* passes; *sem reserva* is rejected under POL-6.

Response example:

```json
{
  "decision": "rejected",
  "rationale": "Rejeitado. POL-3: o valor da condenação (R$ 500,00) é menor que o mínimo de R$ 1.000,00.",
  "citations": ["POL-3"],
  "evidence": [{"policy": "POL-1", "source": "DOC-2", "excerpt": "Trânsito em julgado certificado: a decisão transitou em julgado em 05/05/2023."}],
  "documents": [{"id": "DOC-2", "document_type": "certidao_transito_julgado", "type_source": "name", "classifier_confidence": 0.9941}]
}
```

### Project structure

```
app/
  main.py          FastAPI routes
  analyzer.py      Pipeline: classifier, extraction, LLM, decision
  classifier.py    TF-IDF + Logistic Regression and term explanations
  extraction.py    Rule-based fact extraction with negation handling
  llm.py           Claude API extraction, quote grounding and PII masking
  engine.py        Policy engine and rationale
  policies.py      POL-1 to POL-8
scripts/
  generate_dataset.py   Synthetic labeled dataset
  train.py              Training, grouped cross-validation and reports
  evaluate.py           End-to-end evaluation on reference cases
data/              Training dataset and 12 reference cases
reports/           Classifier metrics and confusion matrix
tests/             31 pytest tests (decisions, classifier, LLM with a fake client, API)
```

### Technologies

Python, scikit-learn, TF-IDF, Logistic Regression, NLP, text classification, Pandas, FastAPI, Pydantic, Claude API (Anthropic), LLM structured outputs, Streamlit, Docker, Docker Compose, pytest, GitHub Actions (CI).

---

<a id="portugues"></a>

# Português

## Análise de Processos Judiciais

**Decida se um processo judicial atende a uma política de compra de crédito, com o motivo e o trecho exato do documento que sustenta cada decisão.**

O sistema lê os dados do processo e seus documentos (sentenças, acórdãos, certidões de trânsito em julgado, planilhas de cálculos, certidões de óbito, procurações) e devolve **aprovado**, **rejeitado** ou **incompleto**, as políticas que decidiram e as evidências encontradas em cada documento.

Funciona em três etapas:

1. **Classificador de documentos com Machine Learning.** TF-IDF (palavras e n-gramas de caracteres) + Regressão Logística no scikit-learn identifica 9 tipos de documento, mesmo quando o nome do arquivo é genérico, como "Documento 1". Cada previsão vem com a confiança e os termos que mais pesaram.
2. **Extração de fatos.** Regras com tratamento de negação encontram os fatos de cada política: trânsito em julgado, valor da condenação, Justiça do Trabalho, óbito da parte autora, substabelecimento sem reserva e honorários. Uma **etapa opcional com LLM (API do Claude, saída estruturada)** complementa o que as regras não acham. Todo fato vindo do LLM precisa trazer uma citação que exista no documento; caso contrário, é descartado. Dados pessoais (CPF, CNPJ, e-mail, telefone) são mascarados antes de qualquer texto ir ao modelo.
3. **Motor de políticas.** Regras determinísticas transformam os fatos em decisão. O LLM nunca decide; ele só extrai fatos.

### Resultados

| Verificação | Resultado |
|---|---|
| Classificador, validação cruzada de 5 folds agrupada por template | **0,87 de acurácia** (± 0,06), 0,85 de F1 macro |
| Classificador, templates nunca vistos no treino | 1,00 de acurácia (225 documentos) |
| Decisões de ponta a ponta nos 12 casos de referência | **12/12 corretas** |
| Testes automatizados (pytest) | **31 aprovados** |

A validação cruzada agrupada é o número mais honesto: o modelo é testado em padrões de escrita que não viu no treino. Relatório completo em [reports/classifier_report.md](reports/classifier_report.md).

**Sobre os dados:** os 1.350 documentos de treino são sintéticos. Foram gerados a partir de modelos de documentos judiciais reais, com nomes, varas, valores e ruído de OCR aleatórios ([scripts/generate_dataset.py](scripts/generate_dataset.py)). Nenhum dado real de processo é usado.

### Executar

Requer **Python 3.11+**. Abra um terminal na pasta do projeto:

```sh
pip install -r requirements-dev.txt
python -m scripts.train
uvicorn app.main:app --reload
```

A API roda em `http://localhost:8000` e a documentação interativa (Swagger) em `http://localhost:8000/docs`.

Interface visual, em um segundo terminal:

```sh
streamlit run streamlit_app.py
```

Testes e avaliação das decisões:

```sh
python -m pytest -v
python -m scripts.evaluate
```

Resultado esperado: **31 testes aprovados** e **12/12 corretas**.

Com Docker, API e interface juntas:

```sh
docker compose up --build
```

API na porta 8000, interface na porta 8501. A imagem treina o classificador durante o build.

### Ativar a etapa com LLM (opcional)

Copie `.env.example` para `.env`, defina `LLM_ENABLED=true` e `ANTHROPIC_API_KEY`. Sem chave, o sistema funciona só com regras e Machine Learning. Se a API falhar, recusar ou passar do tempo, a análise continua sem o LLM.

```sh
python -m scripts.evaluate --llm
```

### Endpoints

| Método | Rota | O que faz |
|---|---|---|
| POST | `/analyze` | Analisa um processo |
| POST | `/analyze/batch` | Analisa até 100 processos e devolve um resumo |
| GET | `/policies` | Lista as políticas |
| GET | `/model` | Versão e métricas do classificador |
| GET | `/health` | Status do serviço |

### Políticas

| Política | Regra | Se falhar |
|---|---|---|
| POL-1 | Trânsito em julgado certificado | incompleto |
| POL-2 | Valor da condenação informado | incompleto |
| POL-3 | Condenação de pelo menos R$ 1.000,00 | rejeitado |
| POL-4 | Não ser da Justiça do Trabalho | rejeitado |
| POL-5 | Sem registro de óbito da parte autora | rejeitado |
| POL-6 | Sem substabelecimento sem reserva de poderes | rejeitado |
| POL-7 | Honorários identificados | apenas informativa |
| POL-8 | Decisão de mérito e planilha de cálculos presentes | incompleto |

A rejeição tem prioridade sobre o incompleto.

### Como as decisões funcionam

Uma sentença que diz *"após o trânsito em julgado, arquivem-se"* não prova o trânsito. Só conta *"transitou em julgado"* em um documento, ou uma certidão ou um movimento do processo, e frases negadas como *"ainda não transitou em julgado"* são ignoradas.

Por exemplo, o processo `0100001-11.2023.5.02.0001` é **rejeitado pela POL-4** mesmo com `esfera: "Estadual"`, porque o dígito 5 na numeração do CNJ identifica a Justiça do Trabalho. Um processo com *substabelecimento com reserva de poderes* passa; *sem reserva* é rejeitado pela POL-6.

Veja [app/](app/) para o código e [tests/](tests/) para os testes. A estrutura do projeto e o exemplo de resposta estão na versão em inglês acima.

### Tecnologias

Python, scikit-learn, TF-IDF, Regressão Logística, NLP, classificação de texto, Pandas, FastAPI, Pydantic, API do Claude (Anthropic), saídas estruturadas de LLM, Streamlit, Docker, Docker Compose, pytest, GitHub Actions (CI).
