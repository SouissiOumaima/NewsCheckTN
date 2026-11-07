
import json
from pathlib import Path

# Dossier principal du projet
ROOT = Path(__file__).resolve().parents[2]

# Fichier TArC original
INPUT_FILE = ROOT / "data" / "raw" / "tarc" / "forum.tab"

# Fichier de sortie
OUTPUT_FILE = ROOT / "data" / "annotations" / "tarc_candidates.jsonl"


def enregistrer_phrase(mots, dates, fichier, numero):
    """Reconstruit et enregistre une phrase en Arabizi."""

    if not mots:
        return False

    texte = " ".join(mots).strip()

    # Garder la date uniquement si elle est cohérente
    date = None
    if len(set(dates)) == 1 and len(dates[0]) == 8:
        valeur = dates[0]
        try:
            from datetime import datetime
            date = datetime.strptime(valeur, "%Y%m%d").date().isoformat()
        except ValueError:
            pass

    phrase = {
        "id": f"tarc-forum-{numero:04d}",
        "text": texte,
        "lang": "tn",
        "script": "latin",
        "source": "TArC - forum.tab",
        "url": "https://github.com/eligugliotta/tarc",
        "date": date,
        "decision": "A_REVOIR"
    }

    fichier.write(json.dumps(phrase, ensure_ascii=False) + "\n")
    return True



def main():
    if not INPUT_FILE.exists():
        print("ERREUR : fichier forum.tab introuvable.")
        print(INPUT_FILE)
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    nombre = 0
    mots = []
    dates = []

    with INPUT_FILE.open("r", encoding="utf-8-sig") as source:
        with OUTPUT_FILE.open("w", encoding="utf-8") as sortie:

            next(source)  # Ignorer l'en-tête

            for ligne in source:
                ligne = ligne.strip()

                # Une ligne vide sépare deux phrases
                if not ligne:
                    if mots:
                        nombre += 1
                        enregistrer_phrase(mots, dates, sortie, nombre)
                        mots = []
                        dates = []
                    continue

                colonnes = ligne.split("\t")

                if len(colonnes) < 2:
                    continue

                date = colonnes[0].strip()
                mot = colonnes[1].strip()

                if mot:
                    mots.append(mot)
                    dates.append(date)

            # Enregistrer la dernière phrase
            if mots:
                nombre += 1
                enregistrer_phrase(mots, dates, sortie, nombre)

    print(f"Extraction terminée : {nombre} phrases.")
    print(f"Fichier créé : {OUTPUT_FILE}")
    print("Attention : les phrases doivent être vérifiées manuellement.")


if __name__ == "__main__":
    main()
