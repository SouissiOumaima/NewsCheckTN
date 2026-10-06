"""Lot A2 — Normalisation FR / AR / tunisien et identification de langue.

Ce module reçoit un texte brut et renvoie un `Document` (voir common/schemas.py) :
    raw_text : le texte d'origine, jamais modifié ;
    text     : le texte normalisé (moins de variantes d'écriture, même sens) ;
    lang     : fr | ar | tn | unk ;
    script   : arabic | latin | arabizi | mixed.

Règle d'or (projet de fact-checking) : la normalisation ne doit JAMAIS changer
un nombre, une date, un sigle ou un nom propre, car ce sont eux qui portent
l'affirmation à vérifier. Chaque règle ci-dessous a été choisie avec ce critère.

Ce que cette version ne fait pas encore (prévu dans le plan du lot) :
    - reconnaître le tunisien écrit en lettres arabes (il sort en `ar`) ;
    - reconnaître l'arabizi sans chiffres (il sort en `fr`) ;
    - convertir l'arabizi en lettres arabes (`arabizi_to_arabic` reste un stub).
"""

from __future__ import annotations

import math
import re
import unicodedata

from common.schemas import Document, Lang

# ---------------------------------------------------------------------------
# 1. Motifs et tables de remplacement
# ---------------------------------------------------------------------------

# Lettres de chaque alphabet. On liste des LETTRES uniquement : ni les chiffres
# ni la ponctuation arabes ne doivent compter comme "texte arabe".
_ARABIC_LETTER = re.compile(r"[\u0621-\u064A\u066E-\u06D3\u06D5]")
# Latin de base + lettres accentuées (é, ç, œ...), sans les signes × et ÷.
_LATIN_LETTER = re.compile(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u024F]")

# Diacritiques arabes (voyelles courtes, shadda, soukoun, alef suscrit) et
# tatweel (trait d'allongement décoratif). Presque personne ne les écrit :
# les retirer fait de "مَدْرَسَة" et "مدرسة" un seul et même mot.
_ARABIC_DIACRITICS = re.compile(r"[\u064B-\u0652\u0670\u0640]")

# Les quatre variantes de l'alef (hamza dessus, dessous, madda, wasla) sont
# écrites au hasard par les internautes : on les ramène à l'alef simple.
_ALEF_VARIANTS = re.compile(r"[\u0623\u0625\u0622\u0671]")

# Lettres arabes souvent confondues, ramenées à une seule forme.
_ARABIC_LETTER_MAP = str.maketrans(
    {
        "\u0649": "\u064A",  # alef maqsura -> ya (confondus en fin de mot)
        "\u0629": "\u0647",  # ta marbuta -> ha (choix du dépôt, testé)
        "\u06A9": "\u0643",  # kaf persan -> kaf arabe (question de clavier)
        "\u06CC": "\u064A",  # ya persan -> ya arabe (question de clavier)
    }
)

# "Formes de présentation" : anciens codes où une lettre arabe est stockée
# déjà dessinée (isolée, initiale, ligature lam-alef...). Certains PDF et
# vieux sites en produisent. On les reconvertit en lettres normales.
_ARABIC_PRESENTATION = re.compile(r"[\uFB50-\uFDFF\uFE70-\uFEFC]+")

# Chiffres arabes-indiens et persans -> chiffres 0-9, pour que "٢٠٢٣" dans une
# affirmation retrouve "2023" dans une preuve. La VALEUR ne change pas.
_DIGIT_MAP = str.maketrans(
    {
        # chr(0x0660 + i) est le i-ème chiffre arabe-indien (٠ à ٩)
        **{chr(0x0660 + i): str(i) for i in range(10)},
        # chr(0x06F0 + i) est le i-ème chiffre persan (۰ à ۹)
        **{chr(0x06F0 + i): str(i) for i in range(10)},
        "\u066B": ".",  # séparateur décimal arabe
        "\u066A": "%",  # signe pourcentage arabe
        "\u066C": ",",  # séparateur de milliers arabe
    }
)

# Apostrophes typographiques -> apostrophe simple, pour que les deux écritures
# de "l'inflation" soient identiques. On ne touche PAS aux guillemets : ils
# servent à repérer le discours rapporté (Lot B).
_APOSTROPHE_MAP = str.maketrans(
    {
        "\u2019": "'",  # apostrophe courbe droite
        "\u2018": "'",  # apostrophe courbe gauche
        "`": "'",  # accent grave isolé
        "\u00B4": "'",  # accent aigu isolé
    }
)

# Caractères invisibles (largeur nulle, marques de direction, césure cachée).
# On ne les voit pas, mais ils rendent deux mots identiques "différents".
_INVISIBLE = re.compile(r"[\u00AD\u200B-\u200F\u202A-\u202E\u2066-\u2069\uFEFF]")

# Zones à ne jamais modifier ni compter comme de la langue : liens, adresses
# e-mail, mentions. (?<![\w.]) = "le @ n'est pas collé à un mot", ce qui
# distingue la mention "@user" de l'adresse "ali@gmail.com".
_PROTECTED = re.compile(
    r"https?://\S+|www\.\S+|[\w.+-]+@[\w-]+\.[\w.-]+|(?<![\w.])@\w+"
)

# Un texte découpé en zones protégées (groupe "keep") et en mots faits de
# lettres seulement (groupe "word"). [^\W\d_] se lit "une lettre", quel que
# soit l'alphabet.
_KEEP_OR_WORD = re.compile(rf"(?P<keep>{_PROTECTED.pattern})|(?P<word>[^\W\d_]+)")

# La même lettre répétée 3 fois ou plus : "graaaave", "هههههه".
_ELONGATION = re.compile(r"(.)\1{2,}")

# Un "mot" au sens large : lettres et chiffres collés ("3lech", "A320").
_TOKEN = re.compile(r"[^\W_]+")

# Chiffres utilisés en arabizi à la place de lettres arabes
# (3 = ع, 7 = ح, 9 = ق, 5 = خ, 2 = ء, 6 = ط).
_ARABIZI_DIGITS = frozenset("235679")

# Mots internationaux qui ressemblent à de l'arabizi sans en être.
_NOT_ARABIZI = frozenset(
    {"mp3", "b2b", "b2c", "p2p", "co2", "h2o", "web3", "ps5", "ipv6",
     "km2", "cm2", "mm2", "km3", "cm3", "dm3"}
)

# Un chiffre suivi d'une unité ou d'un suffixe ordinal : "2eme", "5km", "3rd".
_UNIT_OR_ORDINAL = re.compile(r"\d(?:eme|\u00E8me|nd|rd|th|km|kg|cm|mm|ml|mn|min)")

# Part de lettres arabes à partir de laquelle le texte est dit "arabe" ;
# symétriquement, en dessous de 20 % il est dit "latin". Entre les deux : mixed.
_MAJORITY = 0.8

# Part minimale de mots en arabizi parmi les mots latins pour conclure
# "arabizi". Elle évite qu'UN mot ambigu dans un long article français fasse
# basculer tout le texte. Valeur de départ, à régler sur de vraies données.
_ARABIZI_MIN_RATIO = 0.05


# ---------------------------------------------------------------------------
# 2. Détection du script (alphabet) et de la langue
# ---------------------------------------------------------------------------

def _is_arabizi_token(token: str) -> bool:
    """Dit si UN mot ressemble à de l'arabizi ("3lech", "mta3", "Sa7a").

    L'ancien stub répondait oui dès qu'un chiffre touchait une lettre, donc
    aussi pour "G20", "A320", "5G" ou "km2". On exige maintenant un ensemble
    de conditions que ces faux amis ne remplissent pas.
    """
    digit_runs = re.findall(r"\d+", token)
    n_letters = sum(1 for char in token if char.isalpha())
    if not digit_runs or n_letters < 2:
        return False  # pas de chiffre, ou trop court ("2e", "9h", "5G", "m2")
    if _ARABIC_LETTER.search(token):
        return False  # l'arabizi s'écrit en lettres latines
    if any(run not in _ARABIZI_DIGITS for run in digit_runs):
        return False  # un nombre ("A320", "covid19") ou un chiffre hors liste
    if token.isupper():
        return False  # un sigle tout en majuscules ("COP2", "MP3")
    low = token.lower()
    # Dernier filtre : mot international, unité ou ordinal.
    return not (low in _NOT_ARABIZI or _UNIT_OR_ORDINAL.fullmatch(low))


def _count_letters(text: str) -> tuple[int, int]:
    """Renvoie (nombre de lettres arabes, nombre de lettres latines)."""
    return len(_ARABIC_LETTER.findall(text)), len(_LATIN_LETTER.findall(text))


def detect_script(text: str) -> str:
    """Retourne arabic | latin | arabizi | mixed.

    Script = alphabet, pas langue : "latin" peut être du français, de
    l'anglais ou du tunisien sans chiffres.
    """
    # Les liens et adresses ne sont pas de la langue : on les ignore ici.
    masked = _PROTECTED.sub(" ", text)
    n_ar, n_lat = _count_letters(masked)
    total = n_ar + n_lat

    # On décide à la majorité, pas au premier caractère rencontré : un sigle
    # latin dans une phrase arabe ne suffit pas à la rendre "mixed".
    if total and n_ar / total >= _MAJORITY:
        return "arabic"
    if total and n_ar / total > 1 - _MAJORITY:
        return "mixed"

    # Texte majoritairement latin (ou sans aucune lettre) : arabizi ou non ?
    tokens = _TOKEN.findall(masked)
    n_latin_words = sum(1 for token in tokens if _LATIN_LETTER.search(token))
    n_arabizi = sum(1 for token in tokens if _is_arabizi_token(token))
    needed = math.ceil(_ARABIZI_MIN_RATIO * n_latin_words)
    if n_arabizi and n_arabizi >= needed:
        return "arabizi"
    return "latin"


def detect_language(text: str) -> Lang:
    """Identifie la langue (heuristique provisoire fondée sur le script)."""
    # TODO(Lot A2): remplacer par un classifieur (n-grammes de caractères)
    # capable de séparer MSA / tunisien en lettres arabes, et français /
    # arabizi sans chiffres.
    if sum(_count_letters(_PROTECTED.sub(" ", text))) == 0:
        return Lang.UNKNOWN  # vide, ou seulement chiffres / emojis / liens
    script = detect_script(text)
    if script == "arabizi":
        return Lang.TN
    if script in ("arabic", "mixed"):
        return Lang.AR
    return Lang.FR


# ---------------------------------------------------------------------------
# 3. Normalisation
# ---------------------------------------------------------------------------

def normalize_arabic(text: str) -> str:
    """Supprime diacritiques/tatweel et unifie alef, ya, ta marbuta.

    Ces règles ne touchent que des caractères arabes : on peut donc les
    appliquer à n'importe quel texte, même mélangé avec du français.
    """
    text = _ARABIC_DIACRITICS.sub("", text)
    text = _ALEF_VARIANTS.sub("\u0627", text)
    return text.translate(_ARABIC_LETTER_MAP)


def arabizi_to_arabic(text: str) -> str:
    """Translittération arabizi -> lettres arabes."""
    # TODO(Lot A2): implémenter (table de correspondance + désambiguïsation).
    return text


def _reduce_elongation(text: str) -> str:
    """Raccourcit les lettres étirées : "graaaave" -> "graave".

    Trois protections, toutes dictées par la règle d'or :
      - les liens et adresses ne sont pas touchés ("www" reste "www") ;
      - les mots tout en majuscules non plus ("AAA" est une note financière,
        "XIII" un chiffre romain) ;
      - les nombres ne sont jamais concernés : on ne traite que des lettres.
    """

    def fix(match: re.Match[str]) -> str:
        if match.group("keep"):
            return match.group("keep")  # zone protégée : on la rend intacte
        word = match.group("word")
        if word.isupper():
            return word  # sigle ou chiffre romain
        # En français, aucun mot n'a 3 lettres identiques de suite : on garde
        # 2 lettres ("aller" reste intact). En arabe, quelques vrais mots en
        # ont 3 (ex. "تتتبع") : on garde donc 3 lettres pour ne pas les abîmer.
        keep = 3 if _ARABIC_LETTER.match(word) else 2
        return _ELONGATION.sub(lambda run: run.group(1) * keep, word)

    return _KEEP_OR_WORD.sub(fix, text)


def normalize(text: str) -> Document:
    """Point d'entrée du Lot A2 utilisé par le pipeline."""
    raw = text  # conservé tel quel pour l'affichage et les citations

    # 1. Unicode : une seule façon de coder chaque caractère ("é" en un seul
    #    code). On reste en NFC : la forme NFKC, plus agressive, transformerait
    #    "10²" en "102", ce qui change un nombre.
    text = unicodedata.normalize("NFC", text)
    #    Exception ciblée : les formes de présentation arabes, sans risque.
    text = _ARABIC_PRESENTATION.sub(
        lambda run: unicodedata.normalize("NFKC", run.group()), text
    )

    # 2. Caractères invisibles.
    text = _INVISIBLE.sub("", text)

    # 3. Lettres arabes, puis chiffres et signes arabes.
    text = normalize_arabic(text)
    text = text.translate(_DIGIT_MAP)

    # 4. Apostrophes.
    text = text.translate(_APOSTROPHE_MAP)

    # 5. Lettres étirées (après l'étape 3 : retirer les diacritiques peut
    #    rapprocher des lettres identiques).
    text = _reduce_elongation(text)

    # 6. Espaces multiples, tabulations, retours à la ligne, espaces insécables.
    text = re.sub(r"\s+", " ", text).strip()

    # Script et langue sont calculés sur le texte PROPRE.
    return Document(
        raw_text=raw,
        text=text,
        lang=detect_language(text),
        script=detect_script(text),
    )
