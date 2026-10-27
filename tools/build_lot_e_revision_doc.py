from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Lot_E_Fiche_Revision_Soutenance_Bronze.docx"

NAVY = "17365D"
BLUE = "EAF2F8"
LIGHT = "F6F8FA"
GRID = "D9E2F3"


def set_cell_shading(cell, color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def set_cell_border(cell, color: str = GRID) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def set_cell_margins(cell, top=110, start=120, bottom=110, end=120) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn("w:" + m))
        if node is None:
            node = OxmlElement("w:" + m)
            tc_mar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def keep_with_next(paragraph) -> None:
    paragraph.paragraph_format.keep_with_next = True


def set_font(run, size=10.5, bold=False, color="000000", italic=False) -> None:
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def add_paragraph(doc, text="", style=None, bold_prefix=None):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.12
    if bold_prefix and text.startswith(bold_prefix):
        set_font(p.add_run(bold_prefix), bold=True)
        set_font(p.add_run(text[len(bold_prefix):]))
    else:
        set_font(p.add_run(text))
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.05
    set_font(p.add_run(text))
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    p.paragraph_format.space_after = Pt(5)
    keep_with_next(p)
    run = p.add_run(text)
    set_font(run, size=15 if level == 1 else 12, bold=True, color="000000")
    return p


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    for idx, label in enumerate(headers):
        cell = table.rows[0].cells[idx]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run(label), size=9, bold=True, color="FFFFFF")
        set_cell_shading(cell, NAVY)
        set_cell_border(cell)
        set_cell_margins(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if widths:
            cell.width = Cm(widths[idx])
    for ridx, row in enumerate(rows):
        cells = table.add_row().cells
        for idx, value in enumerate(row):
            cell = cells[idx]
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            set_font(p.add_run(str(value)), size=8.7)
            if ridx % 2 == 1:
                set_cell_shading(cell, LIGHT)
            set_cell_border(cell)
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if widths:
                cell.width = Cm(widths[idx])
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def page_break(doc):
    doc.add_page_break()


def build():
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.6)
    section.left_margin = Cm(1.8)
    section.right_margin = Cm(1.8)

    styles = doc.styles
    styles["Normal"].font.name = "Aptos"
    styles["Normal"]._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    styles["Normal"]._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    styles["Normal"].font.size = Pt(10.5)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_font(header.add_run("NewsCheck TN  |  Fiche de revision Lot E"), size=8.5, color="666666")
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(footer.add_run("Soutenance Bronze  -  mercredi"), size=8.5, color="666666")

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.paragraph_format.space_after = Pt(5)
    set_font(title.add_run("Lot E Integration Evaluation et Demonstration Bronze"), size=23, bold=True)
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(15)
    set_font(subtitle.add_run("Document de revision pour la soutenance du mercredi"), size=12, color="555555")

    add_paragraph(doc, "Ce document explique ce que le Lot E apporte au projet NewsCheck TN, comment les lots A a D sont integres, comment tester le produit et quoi dire pendant la soutenance. L idee essentielle est simple : le Lot E ne remplace pas les composants NLP. Il les relie, expose une API, rend leurs sorties visibles, controle les erreurs d integration et fournit les preuves de fonctionnement bout en bout.")
    add_heading(doc, "A retenir en une minute", 1)
    add_bullet(doc, "Le Lot E est responsable de l integration : pipeline, API FastAPI, frontend commun, dashboard et tests E2E.")
    add_bullet(doc, "La demonstration Bronze utilise seulement des composants classiques : regles, BM25, NLI lexical et gabarit de verdict. Aucun LLM et aucun encodeur dense ne sont requis.")
    add_bullet(doc, "La route principale de demonstration est POST /bronze/check. Elle donne le texte normalise, les affirmations, les preuves, les positions, le verdict, les citations et les temps d execution.")
    add_bullet(doc, "L audit EXP-E-002 teste quatre situations : vrai, faux numerique, absence de preuve et opinion filtree.")
    add_bullet(doc, "La reponse sure quand le systeme ne peut pas trancher est preuves insuffisantes, jamais une invention.")

    add_heading(doc, "1 Role exact du Lot E", 1)
    add_paragraph(doc, "Le Lot E est la couche qui transforme des modules separes en une application utilisable. Les autres lots produisent les donnees ou les algorithmes. Le Lot E garantit que leurs entrees et sorties sont compatibles, qu un utilisateur peut les lancer depuis une interface et que le fonctionnement global peut etre mesure.")
    add_table(doc,
        ["Responsabilite", "Ce qui est livre", "Pourquoi c est important"],
        [
            ["Orchestration", "pipeline.py et contrats communs", "Enchaine les etapes sans modifier le travail interne des autres lots."],
            ["API", "api/main.py avec routes par etape et routes integrees", "Permet au frontend et au jury de tester le systeme reel."],
            ["Frontend", "pages A1, A2, B, C, D, Bronze et evaluation", "Rend chaque sortie visible et comprehensible."],
            ["Evaluation", "metriques communes, resultats JSON, dashboard", "Centralise les preuves de performance et les experiences."],
            ["Qualite", "tests API et audit E2E", "Detecte une regression quand un lot change son composant."],
        ], [3.0, 6.0, 8.0])

    add_heading(doc, "2 Architecture a expliquer au jury", 1)
    add_paragraph(doc, "Le flux normal est le suivant. Il faut le raconter dans cet ordre pendant la demonstration :")
    add_table(doc,
        ["Etape", "Lot", "Entree", "Sortie visible"],
        [
            ["1 Normalisation", "A2", "texte brut", "texte nettoye, langue, ecriture"],
            ["2 Extraction", "B", "Document", "affirmation, sujet, predicat, objet, modalite"],
            ["3 Filtre Model 1", "C", "claims", "claims verifiables pour le pipeline general"],
            ["4 Recherche", "D", "claim plus corpus", "top k passages BM25 avec score et source"],
            ["5 Position NLI", "C", "claim plus passage", "supports, refutes ou neutral et confiance"],
            ["6 Verdict", "D", "positions", "vrai, faux ou preuves insuffisantes avec citations"],
            ["7 Integration", "E", "toutes les sorties", "API, interface, latence, tests et resultats"],
        ], [3.2, 1.4, 4.8, 7.6])
    add_paragraph(doc, "Nuance a dire clairement : dans la demo Bronze, le filtre Model 1 appris est volontairement retire. On garde une extraction par regles afin de respecter le palier Bronze. Le pipeline general POST /check peut utiliser Model 1, alors que POST /bronze/check montre exclusivement le chemin classique.")

    page_break(doc)
    add_heading(doc, "3 Ce que contient la demonstration Bronze", 1)
    add_paragraph(doc, "Page a ouvrir : http://127.0.0.1:8000/app/bronze.html. L interface appelle une seule route integree, puis affiche toutes les etapes. Cette conception evite que cinq appels independants cachent une erreur d integration ou donnent des latences difficiles a expliquer.")
    add_table(doc,
        ["Element affiche", "Origine", "Ce que tu dis"],
        [
            ["Langue et ecriture", "A2 normalisation", "Le systeme normalise avant les regles et garde la trace de la langue."],
            ["Segments et SPO", "B extraction", "Seules les affirmations assertives poursuivent le parcours."],
            ["Preuves BM25", "D retrieval", "BM25 classe les passages du corpus selon les mots importants de l affirmation."],
            ["Position par passage", "C NLI lexical", "Chaque preuve soutient, contredit ou ne permet pas de conclure."],
            ["Verdict et citations", "D gabarit", "Le verdict cite uniquement les identifiants des preuves retrouvees."],
            ["Latence", "E instrumentation", "Le temps total et le detail par etape sont mesures en direct."],
        ], [4.0, 4.0, 9.0])
    add_heading(doc, "Role de Preuves BM25", 2)
    add_paragraph(doc, "Preuves BM25 signifie les passages candidats retrouves dans le corpus. BM25 est une methode classique de recherche par mots. Elle ne decide pas encore si la phrase est vraie : elle propose les textes qui semblent les plus pertinents. Ensuite le NLI compare la phrase et chaque preuve, puis le gabarit produit le verdict. Donc BM25 repond a la question ou chercher, le NLI repond a la question est ce que ce passage soutient ou contredit, et le verdict repond a la question que dire a l utilisateur.")

    add_heading(doc, "4 Routes API a connaitre", 1)
    add_table(doc,
        ["Route", "But", "Quand la montrer"],
        [
            ["GET /health", "Verifier que l API est active", "Avant la demo ou en cas de probleme."],
            ["POST /normalize", "Voir la sortie A2", "Pour expliquer langue et ecriture."],
            ["POST /extract", "Extraction plus Model 1", "Pour la page Lot B ou C hors Bronze."],
            ["POST /extract/bronze", "Extraction a regles seulement", "Pour prouver la contrainte Bronze."],
            ["POST /retrieve", "Recuperer les passages BM25", "Pour expliquer le role des preuves."],
            ["POST /nli", "Comparer une claim et une preuve", "Pour illustrer supports/refutes/neutral."],
            ["POST /verdict", "Produire un verdict cite", "Pour la page Lot D."],
            ["POST /bronze/check", "Tracer le parcours Bronze complet", "Route principale de la soutenance."],
            ["POST /check", "Pipeline general de l application", "Pour la verification utilisateur habituelle."],
            ["GET /results", "Alimenter le dashboard", "Pour montrer les resultats de tous les lots."],
        ], [4.2, 6.3, 6.5])

    page_break(doc)
    add_heading(doc, "5 Scenarios de test a refaire", 1)
    add_paragraph(doc, "Avant la soutenance, lance l API puis teste ces scenarios dans la page Bronze. Les phrases sont volontairement simples afin que tu puisses expliquer le resultat sans hesiter.")
    add_table(doc,
        ["Scenario", "Texte a coller", "Resultat attendu", "Point a expliquer"],
        [
            ["Preuve disponible", "Tunis est la capitale de la Tunisie.", "Vrai, citation sample-002", "La preuve BM25 est retrouvee puis elle soutient exactement la claim."],
            ["Contradiction numerique", "Le taux de chomage en Tunisie etait de 25 % au deuxieme trimestre 2023.", "Faux, citation sample-001", "La preuve indique 16,4 %, donc le NLI lexical detecte la contradiction sur la valeur."],
            ["Sans preuve", "Un nouvel aeroport a ete inaugure a Kairouan en 2026.", "Preuves insuffisantes et abstention", "Le systeme ne doit pas inventer une source ou un verdict."],
            ["Opinion filtree", "Je pense que Tunis est magnifique.", "Filtre, aucune claim aval", "Une opinion n est pas une affirmation factuelle a verifier dans Bronze."],
            ["Question", "Quel est le taux de chomage en Tunisie ?", "Filtre", "Une question demande une information mais ne fait pas une assertion."],
            ["Texte libre du jury", "Phrase fournie par l enseignant", "Trace complete ou filtre", "Montrer que la demo accepte une entree non preparee."],
        ], [2.8, 5.6, 4.1, 4.5])
    add_heading(doc, "Commandes de test", 2)
    add_paragraph(doc, "Depuis la racine du projet :", bold_prefix="")
    for command in [
        "uvicorn api.main:app --reload",
        "python -m pytest -q",
        "python -m evaluation.integration_audit",
        "python -m linguistic_analysis.evaluate --rules --out-dir evaluation/results --errors",
        "python -m rag_llm.evaluate_retrieval --method bm25 --exp-id EXP-D-001 --split dev-fictif-v2",
        "python -m rag_llm.evaluate_verdict --stance rules --method bm25 --exp-id EXP-D-002 --split dev-fictif-v2",
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.5)
        p.paragraph_format.space_after = Pt(3)
        set_font(p.add_run(command), size=9.5, color="17365D")

    add_heading(doc, "6 Audit d integration EXP E 002", 1)
    add_paragraph(doc, "L audit est un controle de regression, pas une evaluation scientifique generale. Il execute les quatre cas versionnes dans data/annotations/bronze_fr_integration_eval.jsonl et produit evaluation/results/lot-e_integration_bronze_20261027.json.")
    add_table(doc,
        ["Mesure", "Valeur obtenue", "Interpretation correcte"],
        [
            ["Nombre de cas", "4", "Vrai, faux numerique, abstention, opinion."],
            ["Succes bout en bout", "1,000", "Les 4 sorties attendues sont obtenues."],
            ["Macro F1", "1,000", "Sur seulement 3 cas avec verdict : ne pas presenter ce score comme general."],
            ["Recall at 5", "1,000", "Les preuves attendues sont retrouvees dans ces cas de controle."],
            ["Taux d abstention", "0,333", "Une des trois assertions avec verdict est abstention, ce qui est attendu."],
            ["Citations invalides", "0", "Chaque citation emise appartient aux preuves recuperees."],
            ["Latence moyenne", "5,82 ms", "Mesure locale, depend de la machine et du corpus charge."],
        ], [4.4, 3.4, 9.2])

    page_break(doc)
    add_heading(doc, "7 Resultats disponibles sur le dashboard", 1)
    add_paragraph(doc, "La page /app/evaluation.html lit GET /results et affiche les fichiers JSON des evaluations. Chaque resultat pointe vers un identifiant EXP dans experiments.md. Cela permet de montrer les resultats sans recopier les chiffres a la main.")
    add_table(doc,
        ["Lot", "Resultat affiche", "Chiffres a retenir", "Lecture honnete"],
        [
            ["B", "Extraction a regles", "claim 1,00 ; modalite 1,00 ; SPO exact 0,91 sur eval_30", "Jeu de 34 phrases, certains sous groupes tres petits."],
            ["C", "TF IDF caracteres plus regression logistique", "macro F1 0,6435 sur test gele de 120", "Baseline classique du Model 1, distincte de la demo Bronze."],
            ["D Retrieval", "BM25", "Hit at 1 0,889 ; Recall at 5 0,667 ; MRR 0,907", "Le retrieval trouve des passages, mais ne garantit pas le bon verdict."],
            ["D Verdict", "BM25 plus NLI regles plus gabarit", "accuracy 0,700 ; macro F1 0,524 ; couverture 0,650", "Les faiblesses TN et les abstentions sont visibles et doivent etre assumees."],
            ["E", "Audit integration Bronze", "4 sur 4, citations invalides 0", "Controle de regression, pas performance generale."],
        ], [2.0, 4.7, 4.9, 5.4])
    add_heading(doc, "Pourquoi les resultats Lot D ne sont pas parfaits", 2)
    add_paragraph(doc, "Le verdict par regles obtient une macro F1 de 0,524 sur son jeu de 20 claims. Il s abstient souvent quand la preuve est peu decisive ou quand la phrase est en tunisien. Ce n est pas un probleme a cacher : cela montre que la politique d abstention est activee au lieu de produire une affirmation non justifiee. Le jury attend une analyse des echecs, pas seulement des cas reussis.")

    add_heading(doc, "8 Questions probables et reponses courtes", 1)
    qa = [
        ("Pourquoi Lot E est necessaire si chaque lot marche seul ?", "Parce qu un module isole ne prouve pas que les formats, les langues, les erreurs et les citations restent coherents quand on les enchaine. Lot E teste la chaine complete."),
        ("Quelle est la difference entre BM25 et NLI ?", "BM25 retrouve les passages potentiellement utiles. Le NLI compare semantiquement et lexicalement une claim avec un passage pour dire soutient, contredit ou neutre."),
        ("Que se passe t il sans preuve ?", "Le verdict est preuves insuffisantes avec abstention. Il n y a pas de source inventee."),
        ("Pourquoi l audit E donne 1,00 ?", "Il contient quatre cas de regression controles, donc il valide l integration. Les performances generales sont celles des evaluations B, C et D avec leurs jeux dedies."),
        ("Comment savez vous que les citations sont fiables ?", "L audit compte les citations invalides. Une citation doit appartenir a la liste des preuves recuperees. Le resultat actuel est 0 citation invalide."),
        ("Pourquoi garder la latence ?", "Le guide demande une demonstration reelle. Afficher les millisecondes prouve que le pipeline s execute maintenant et pas sur une capture ecran."),
        ("Est ce que la demo utilise un LLM ?", "Non. La route Bronze est explicitement regles, BM25, NLI lexical et gabarit. Aucun LLM ni encodeur dense ne sont utilises."),
        ("Quels sont les limites du Lot E ?", "Lot E integre et teste, mais il depend de la qualite des corpus et des composants. La data card complete, le kappa et certaines analyses de 30 erreurs demandent encore une validation humaine."),
    ]
    add_table(doc, ["Question", "Reponse a memoriser"], qa, [6.0, 11.0])

    page_break(doc)
    add_heading(doc, "9 Probleme et solutions pendant la demo", 1)
    add_table(doc,
        ["Symptome", "Verification rapide", "Solution"],
        [
            ["La page affiche API non joignable", "Ouvrir http://127.0.0.1:8000/health", "Lancer uvicorn api.main:app --reload depuis la racine."],
            ["La page semble ancienne", "Verifier que la nouvelle carte Latence totale est visible", "Faire Ctrl plus F5 ou ajouter ?v=3 a l URL."],
            ["Une opinion ne donne aucun verdict", "Regarder la carte Etat", "C est le comportement attendu : expliquer le filtrage."],
            ["Un texte sans preuve donne abstention", "Lire les preuves BM25 et l explication", "C est une securite, pas un echec de l interface."],
            ["Le jury donne une phrase arabe ou TN", "Tester dans la page generale ou Lot D", "Preciser que la revue Bronze officielle est limitee au chemin classique FR ; les autres langues sont visibles dans les lots avances."],
            ["Un score change de quelques ms", "Relancer la meme phrase", "La latence depend de la machine ; l important est que chaque etape et le total soient affiches."],
        ], [4.2, 5.2, 7.6])

    add_heading(doc, "10 Etat final du Lot E", 1)
    add_paragraph(doc, "Pour la partie technique du Lot E, le travail est termine : API, integration Bronze, frontend, dashboard, metriques, resultats JSON, audit E2E, latence et tests sont en place. Le commit livre est fed0b78 sur la branche ot-c-model1-avancement.")
    add_paragraph(doc, "Les points restants ne sont pas des bugs de Lot E : il faut encore une validation humaine de certaines donnees de projet, notamment le kappa de double annotation, les 30 erreurs reellement annotees par composant lorsque requis, les slides PDF, la video de secours, le tag Git bronze, la declaration d usage IA et le journal de projet.")

    add_heading(doc, "Mini script oral de conclusion", 2)
    add_paragraph(doc, "Notre Lot E a transforme les contributions des autres lots en un produit verifiable. Nous pouvons lancer le pipeline complet en direct, voir chaque etape, mesurer la latence, afficher les preuves BM25 et garantir que les verdicts cites ne referencent que des passages retrouves. Lorsque la preuve est insuffisante, le systeme s abstient. Les resultats de chaque lot restent visibles dans le dashboard et reproductibles par commande.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
