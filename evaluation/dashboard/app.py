"""Lot E — Tableau de bord d'évaluation (Streamlit).

Lancer : streamlit run evaluation/dashboard/app.py
Lit les fichiers JSON produits dans evaluation/results/.
"""

import json
from pathlib import Path

import streamlit as st

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

st.title("NewsCheck TN — Tableau de bord d'évaluation")

files = sorted(RESULTS_DIR.glob("*.json"))
if not files:
    st.info("Aucun résultat dans evaluation/results/ pour l'instant.")
rows = []
for f in files:
    try:
        payload = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        st.warning(f"JSON illisible : {f.name}")
        continue
    metrics = payload.get("metrics", payload)
    rows.append({
        "fichier": f.name,
        "lot": payload.get("lot", "?"),
        "expérience": payload.get("exp_id", "-"),
        "tâche": payload.get("task", f.stem),
        "modèle": payload.get("model", ""),
        "jeu": payload.get("split", ""),
        **{key: value for key, value in metrics.items() if isinstance(value, (int, float))},
    })

if rows:
    st.dataframe(rows, use_container_width=True, hide_index=True)
    numeric = sorted({key for row in rows for key, value in row.items() if isinstance(value, (int, float))})
    metric = st.selectbox("Mesure à comparer", numeric)
    chart_rows = [row for row in rows if isinstance(row.get(metric), (int, float))]
    if chart_rows:
        st.bar_chart({f"{row['lot']} · {row['expérience']}": row[metric] for row in chart_rows})

    with st.expander("Détails bruts et résultats par groupe"):
        for f in files:
            st.markdown(f"#### {f.stem}")
            st.json(json.loads(f.read_text(encoding="utf-8")))
