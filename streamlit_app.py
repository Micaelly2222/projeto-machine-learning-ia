import json
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from app.analyzer import analyze, get_classifier
from app.config import settings
from app.policies import POLICIES
from app.schemas import CaseInput

ROOT = Path(__file__).parent
EXAMPLES = json.loads((ROOT / "data" / "cases.json").read_text(encoding="utf-8"))
LABELS = {"approved": "Aprovado", "rejected": "Rejeitado", "incomplete": "Incompleto"}
COLORS = {"approved": "green", "rejected": "red", "incomplete": "orange"}
# Por padrão a interface roda o pipeline no próprio processo (é assim no Streamlit Cloud).
# Com USE_API=true ela chama a API FastAPI, como no docker compose.
USE_API = os.getenv("USE_API", "false").lower() == "true"

st.set_page_config(page_title="Análise de Processos Judiciais", layout="wide")


@st.cache_resource(show_spinner="Carregando o classificador...")
def classifier():
    return get_classifier()


def run_case(payload: dict) -> dict:
    if USE_API:
        response = requests.post(f"{settings.api_url}/analyze", json=payload, timeout=90)
        response.raise_for_status()
        return response.json()
    return analyze(CaseInput(**payload), classifier=classifier()).model_dump(mode="json")


st.title("Análise de Processos Judiciais")
st.caption(
    "Classificador de documentos com Machine Learning, extração de fatos com regras (e LLM opcional) "
    "e decisão por políticas explícitas. "
    "[Código no GitHub](https://github.com/Micaelly2222/projeto-machine-learning-ia)"
)

with st.sidebar:
    st.header("Políticas")
    for p in POLICIES.values():
        outcome = LABELS.get(p.outcome_if_failed.value, "") if p.outcome_if_failed else "informativa"
        st.markdown(f"**{p.id}** {p.title}  \n<small>se falhar: {outcome}</small>", unsafe_allow_html=True)
    st.divider()
    mode = "API FastAPI" if USE_API else "pipeline local"
    llm = "ligado" if settings.llm_enabled else "desligado (regras + ML)"
    st.caption(f"Modo: {mode} · LLM: {llm}")

tab_case, tab_eval, tab_model = st.tabs(["Analisar processo", "Avaliação nos 12 casos", "Modelo de ML"])

with tab_case:
    left, right = st.columns([3, 2])
    with left:
        names = [e["name"] for e in EXAMPLES]
        example = st.selectbox("Escolha um exemplo ou cole o seu JSON", names, index=0)
        chosen = next(e for e in EXAMPLES if e["name"] == example)
        payload_text = st.text_area(
            "JSON do processo", value=json.dumps(chosen["case"], indent=2, ensure_ascii=False), height=460
        )
        submit = st.button("Analisar", type="primary", width="stretch")

    with right:
        if submit:
            try:
                result = run_case(json.loads(payload_text))
            except json.JSONDecodeError:
                st.error("JSON inválido.")
                st.stop()
            except Exception as exc:
                st.error(f"Não foi possível analisar: {exc}")
                st.stop()

            decision = result["decision"]
            st.markdown(f"### :{COLORS[decision]}[{LABELS[decision]}]")
            st.write(result["rationale"])
            st.markdown("**Políticas citadas:** " + ", ".join(result["citations"]))

            st.subheader("Verificações")
            st.dataframe(
                pd.DataFrame(
                    [{"Política": c["policy"], "Regra": c["title"], "Passou": "sim" if c["passed"] else "não"}
                     for c in result["checks"]]
                ),
                hide_index=True, width="stretch",
            )

            st.subheader("Documentos classificados")
            st.dataframe(
                pd.DataFrame(
                    [{"ID": d["id"], "Nome": d["name"], "Tipo": d["document_type"], "Origem": d["type_source"],
                      "Confiança": d["classifier_confidence"], "Termos que mais pesaram": ", ".join(d["top_terms"])}
                     for d in result["documents"]]
                ),
                hide_index=True, width="stretch",
            )

            st.subheader("Evidências")
            for e in result["evidence"]:
                st.markdown(f"- **{e['policy']}** ({e['source']}): {e['excerpt']}")

            with st.expander("Resposta completa (JSON)"):
                st.json(result)
        else:
            st.info("Escolha um exemplo e clique em **Analisar**. O resultado mostra a decisão, as políticas e o trecho do documento usado como evidência.")

with tab_eval:
    st.write("Roda os 12 casos de referência e compara a decisão do sistema com a decisão esperada.")
    if st.button("Rodar avaliação"):
        rows = []
        for item in EXAMPLES:
            result = run_case(item["case"])
            rows.append({
                "Caso": item["name"],
                "Esperado": LABELS[item["expected"]],
                "Sistema": LABELS[result["decision"]],
                "Políticas": ", ".join(result["citations"]),
                "Acertou": "sim" if result["decision"] == item["expected"] else "não",
            })
        df = pd.DataFrame(rows)
        hits = (df["Acertou"] == "sim").sum()
        st.metric("Acertos", f"{hits}/{len(df)}", f"{hits / len(df):.0%}")
        st.dataframe(df, hide_index=True, width="stretch")

with tab_model:
    meta = classifier().metadata
    c1, c2, c3 = st.columns(3)
    c1.metric("Validação cruzada (acurácia)", f"{meta['cross_validation']['accuracy_mean']:.2f}",
              f"± {meta['cross_validation']['accuracy_std']:.2f}", delta_color="off")
    c2.metric("F1 macro", f"{meta['cross_validation']['macro_f1_mean']:.2f}")
    c3.metric("Documentos de treino", meta["n_documents"])
    st.caption(
        "TF-IDF de palavras e de n-gramas de caracteres + Regressão Logística. A validação cruzada é agrupada "
        "por template: o modelo é testado em padrões de escrita que não viu no treino. Os documentos de treino "
        "são sintéticos, gerados a partir de modelos de documentos judiciais reais."
    )
    per_class = meta["holdout"]["per_class"]
    st.dataframe(
        pd.DataFrame(
            [{"Classe": k, "Precisão": round(v["precision"], 2), "Recall": round(v["recall"], 2),
              "F1": round(v["f1-score"], 2)} for k, v in per_class.items() if k in meta["classes"]]
        ),
        hide_index=True, width="stretch",
    )
