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
for f in files:
    st.subheader(f.stem)
    st.json(json.loads(f.read_text(encoding="utf-8")))

# TODO(Lot E): graphiques par lot (F1 par langue, Recall@k, taux d'abstention, fidélité).
