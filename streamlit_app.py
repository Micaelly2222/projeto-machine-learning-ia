import json
from pathlib import Path

import requests
import streamlit as st

from app.config import settings

EXAMPLES = json.loads((Path(__file__).parent / "data" / "cases.json").read_text(encoding="utf-8"))
LABELS = {"approved": "Aprovado", "rejected": "Rejeitado", "incomplete": "Incompleto"}
COLORS = {"approved": "green", "rejected": "red", "incomplete": "orange"}

st.set_page_config(page_title="Análise de Processos Judiciais", layout="wide")
st.title("Análise de Processos Judiciais")
st.caption("Classificação de documentos com Machine Learning, extração de fatos e decisão por políticas.")

with st.sidebar:
    st.header("Políticas")
    try:
        for policy in requests.get(f"{settings.api_url}/policies", timeout=5).json():
            st.markdown(f"**{policy['id']}** {policy['title']}")
    except requests.RequestException:
        st.warning("API indisponível. Rode `uvicorn app.main:app` antes.")

left, right = st.columns([3, 2])

with left:
    example = st.selectbox("Carregar exemplo", ["(nenhum)"] + [e["name"] for e in EXAMPLES])
    default = ""
    if example != "(nenhum)":
        chosen = next(e for e in EXAMPLES if e["name"] == example)
        default = json.dumps(chosen["case"], indent=2, ensure_ascii=False)
    payload = st.text_area("JSON do processo", value=default, height=480)
    submit = st.button("Analisar", type="primary", use_container_width=True)

with right:
    if submit:
        try:
            response = requests.post(f"{settings.api_url}/analyze", json=json.loads(payload), timeout=90)
        except json.JSONDecodeError:
            st.error("JSON inválido.")
            st.stop()
        except requests.RequestException as exc:
            st.error(f"Não foi possível chamar a API: {exc}")
            st.stop()

        if response.status_code != 200:
            st.error(f"Erro {response.status_code}")
            st.json(response.json())
            st.stop()

        result = response.json()
        decision = result["decision"]
        st.markdown(f"### :{COLORS[decision]}[{LABELS[decision]}]")
        st.write(result["rationale"])
        st.markdown("**Políticas citadas:** " + ", ".join(result["citations"]))

        st.subheader("Verificações")
        st.dataframe(
            [{"Política": c["policy"], "Regra": c["title"], "Passou": "sim" if c["passed"] else "não"}
             for c in result["checks"]],
            hide_index=True, use_container_width=True,
        )

        st.subheader("Documentos")
        st.dataframe(
            [{"ID": d["id"], "Nome": d["name"], "Tipo": d["document_type"], "Origem": d["type_source"],
              "Confiança": d["classifier_confidence"], "Termos": ", ".join(d["top_terms"])}
             for d in result["documents"]],
            hide_index=True, use_container_width=True,
        )

        st.subheader("Evidências")
        for e in result["evidence"]:
            st.markdown(f"- **{e['policy']}** ({e['source']}): {e['excerpt']}")

        with st.expander("Resposta completa"):
            st.json(result)
