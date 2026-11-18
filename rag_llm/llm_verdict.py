"""Lot D — Palier Silver : verdict par LLM contraint aux preuves (prompt contrôlé).

Le LLM reçoit l'affirmation et les k passages retrouvés, numérotés P1…Pk, et doit répondre par
un **objet JSON** et rien d'autre :

    {"label": "vrai | faux | trompeur | preuves_insuffisantes",
     "citations": ["P1", ...], "explication": "..."}

Contraintes vérifiées par le code (pas seulement demandées au modèle) :
- `label` appartient aux 4 labels du projet ;
- chaque citation désigne un passage **fourni** (P1…Pk) : une citation inventée est refusée ;
- vrai / faux / trompeur exigent au moins une citation ; `preuves_insuffisantes` n'en a pas.
Si la sortie viole une contrainte, elle est **rejetée** et remplacée par le verdict du gabarit
Bronze (`rag_llm.verdict`), ou par une abstention si aucune position NLI n'est disponible.
Le taux de sorties rejetées est mesuré (EXP-D-009).

Moteurs (`LLM_PROVIDER`, voir `.env.example`) :
- `hf` (défaut, alias `transformers`) : modèle ouvert local, `LLM_MODEL` (défaut
  `CohereLabs/aya-expanse-8b`, 8 milliards de paramètres, chargé en 4 bits sur GPU, ex. Colab T4 ;
  modèle à accès contrôlé : accepter la licence sur Hugging Face, jeton dans `HF_TOKEN`) ;
- `openai` : toute API compatible OpenAI, y compris Ollama en local (`LLM_BASE_URL`, `LLM_MODEL`,
  clé dans `LLM_API_KEY`).
Échantillonnage : température 0.3, top-p 0.9, une graine par exécution (3 graines au Silver).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from typing import Protocol

from common.schemas import Claim, Evidence, Label, Lang, StanceResult, Verdict
from rag_llm.verdict import generate_verdict_with_reason

PROMPT_VERSION = "v1"
LABELS = [label.value for label in Label]
NEI = Label.NOT_ENOUGH_INFO.value
DEFAULT_MODEL = "CohereLabs/aya-expanse-8b"  # ≤ 8 milliards de paramètres (cahier des charges)
TEMPERATURE = 0.3
TOP_P = 0.9
MAX_NEW_TOKENS = 300
PASSAGE_LEN = 700  # caractères gardés par passage dans le prompt
LLM_UNCERTAINTY = 0.4  # le LLM ne donne pas de probabilité calibrée : valeur fixe, documentée

SYSTEM_PROMPT = """Tu es un vérificateur de faits pour la Tunisie. On te donne une affirmation et \
des passages numérotés (P1, P2…) tirés d'articles de vérification. Tu dois juger l'affirmation \
EN T'APPUYANT UNIQUEMENT SUR CES PASSAGES, jamais sur tes connaissances.

Labels possibles :
- "vrai" : un passage confirme l'affirmation ;
- "faux" : un passage contredit ou dément l'affirmation ;
- "trompeur" : un passage montre que l'affirmation contient du vrai mais déforme les faits \
(chiffre exagéré, contexte retiré, ancienne information présentée comme nouvelle) ;
- "preuves_insuffisantes" : aucun passage ne parle directement du même fait (même événement, \
même chiffre, même date). Dans le doute, choisis "preuves_insuffisantes".

Règles :
1. Cite les passages qui justifient ton label, avec leur numéro exact ("P1", "P2"…). \
Pour "vrai", "faux" et "trompeur", au moins une citation. Pour "preuves_insuffisantes", aucune.
2. Ne cite jamais un passage qui n'est pas dans la liste.
3. "explication" : une ou deux phrases, dans la langue de l'affirmation (français, ou arabe \
pour une affirmation en arabe ou en tunisien).
4. Réponds uniquement par un objet JSON, sans texte autour :
{"label": "...", "citations": ["P1"], "explication": "..."}"""

_STANCE_FR = {"supports": "soutient", "refutes": "contredit", "neutral": "neutre"}


class Generator(Protocol):
    name: str

    def generate(self, messages: list[dict], seed: int) -> str: ...


class OutputError(ValueError):
    """Sortie du LLM qui viole le format ou une contrainte (code dans `reason`)."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------


def _short(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= PASSAGE_LEN else text[:PASSAGE_LEN].rsplit(" ", 1)[0] + "…"


def build_messages(
    claim: Claim, evidences: list[Evidence], stances: list[StanceResult] | None = None
) -> list[dict]:
    """Messages système + utilisateur. `stances` : indices NLI à afficher (ablation)."""
    hints = {s.evidence.doc_id: s for s in stances or []}
    lines = [f"Affirmation : {claim.text}", "", "Passages :"]
    if not evidences:
        lines.append("(aucun passage retrouvé)")
    for i, ev in enumerate(evidences, start=1):
        meta = ", ".join(x for x in (ev.source, ev.date) if x)
        hint = ""
        if ev.doc_id in hints:
            s = hints[ev.doc_id]
            hint = f" [indice NLI : {_STANCE_FR[s.stance.value]}, confiance {s.confidence:.2f}]"
        lines.append(f"[P{i}]{f' ({meta})' if meta else ''}{hint} {_short(ev.text)}")
    lines += ["", "Réponds uniquement par l'objet JSON."]
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(lines)},
    ]


def prompt_fingerprint() -> str:
    return hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Lecture et contrôle de la sortie
# ---------------------------------------------------------------------------


def parse_output(text: str, n_passages: int) -> dict:
    """Extrait le JSON et vérifie les contraintes. Lève `OutputError` sinon."""
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        raise OutputError("json_absent", text[:80])
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise OutputError("json_invalide", exc.msg) from None
    label = str(data.get("label", "")).strip().lower()
    if label not in LABELS:
        raise OutputError("label_inconnu", label)
    raw_cites = data.get("citations") or []
    if not isinstance(raw_cites, list):
        raise OutputError("citations_mal_formees", str(raw_cites)[:40])
    indices = []
    for cite in raw_cites:
        m = re.fullmatch(r"\s*\[?P?(\d+)\]?\s*", str(cite), flags=re.I)
        if not m or not 1 <= int(m.group(1)) <= n_passages:
            raise OutputError("citation_hors_liste", str(cite))
        if int(m.group(1)) not in indices:
            indices.append(int(m.group(1)))
    if label != NEI and not indices:
        raise OutputError("verdict_sans_citation", label)
    if label == NEI:
        indices = []
    explanation = str(data.get("explication") or data.get("explanation") or "").strip()
    return {"label": label, "indices": indices, "explanation": explanation}


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


@dataclass
class LLMResult:
    verdict: Verdict
    valid: bool
    error: str | None = None
    raw: str = ""
    fallback: str | None = None  # "gabarit" | "abstention" si la sortie a été rejetée
    info: dict = field(default_factory=dict)


def _abstention(claim: Claim) -> Verdict:
    text = (
        "الأدلة غير كافية للحكم."
        if claim.lang in (Lang.AR, Lang.TN)
        else ("Preuves insuffisantes pour statuer.")
    )
    return Verdict(claim=claim, label=Label.NOT_ENOUGH_INFO, explanation=text, abstained=True)


def llm_verdict(
    claim: Claim,
    evidences: list[Evidence],
    generator: Generator,
    seed: int = 42,
    stances: list[StanceResult] | None = None,
    show_nli: bool = False,
    min_score: float | None = None,
) -> LLMResult:
    """Verdict par LLM ; repli sur le gabarit (si `stances`) ou l'abstention si sortie rejetée."""
    messages = build_messages(claim, evidences, stances if show_nli else None)
    raw = generator.generate(messages, seed=seed)
    try:
        out = parse_output(raw, len(evidences))
    except OutputError as exc:
        if stances is not None:
            verdict = generate_verdict_with_reason(claim, stances, min_score=min_score)[0]
            return LLMResult(verdict, False, exc.reason, raw, "gabarit")
        return LLMResult(_abstention(claim), False, exc.reason, raw, "abstention")
    cited = [evidences[i - 1].doc_id for i in out["indices"]]
    label = Label(out["label"])
    abstained = label == Label.NOT_ENOUGH_INFO
    verdict = Verdict(
        claim=claim,
        label=label,
        explanation=out["explanation"] or (_abstention(claim).explanation if abstained else ""),
        citations=cited,
        uncertainty=1.0 if abstained else LLM_UNCERTAINTY,
        abstained=abstained,
    )
    return LLMResult(verdict, True, None, raw)


# ---------------------------------------------------------------------------
# Moteurs
# ---------------------------------------------------------------------------


COMPUTE_DTYPES = ("float16", "bfloat16", "float32")


def compute_dtype_name() -> str:
    """Type de calcul du LLM local en 4 bits : `LLM_COMPUTE_DTYPE`, float16 par défaut.

    float16 est le réglage d'EXP-D-010 (Aya). Falcon-H1 produit des `inf` / `nan` en float16 sur
    un GPU T4 (pas de bfloat16) : EXP-D-013 utilise float32, plus lent mais stable.
    """
    name = (os.getenv("LLM_COMPUTE_DTYPE") or "float16").strip().lower()
    if name not in COMPUTE_DTYPES:
        raise ValueError(f"LLM_COMPUTE_DTYPE={name!r} : choisir parmi {COMPUTE_DTYPES}")
    return name


class TransformersGenerator:
    """Modèle ouvert chargé avec transformers (4 bits sur GPU si bitsandbytes est installé)."""

    def __init__(self, model_name: str | None = None, load_in_4bit: bool = True) -> None:
        self.name = model_name or os.getenv("LLM_MODEL") or DEFAULT_MODEL
        self.load_in_4bit = load_in_4bit
        self._model = self._tok = None

    def _load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        kwargs: dict = {"device_map": "auto"}
        if self.load_in_4bit and torch.cuda.is_available():
            from transformers import BitsAndBytesConfig

            compute = getattr(torch, compute_dtype_name())
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_compute_dtype=compute
            )
            if compute is not torch.float16:  # parties non quantifiées dans le même type
                kwargs["dtype"] = compute
        self._tok = AutoTokenizer.from_pretrained(self.name)
        self._model = AutoModelForCausalLM.from_pretrained(self.name, **kwargs)

    def generate(self, messages: list[dict], seed: int) -> str:
        if self._model is None:
            self._load()
        from transformers import set_seed

        set_seed(seed)
        prompt = self._tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self._tok(prompt, return_tensors="pt").to(self._model.device)
        out = self._model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            pad_token_id=self._tok.eos_token_id,
        )
        return self._tok.decode(out[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)


class OpenAICompatibleGenerator:
    """API compatible OpenAI (/chat/completions) : OpenAI, Gemini, Mistral, Groq, Ollama…

    Clé lue dans `LLM_API_KEY` (jamais écrite dans un fichier). Les offres gratuites limitent le
    nombre de requêtes par minute : une pause minimale `LLM_MIN_INTERVAL` (secondes, défaut 4)
    sépare deux appels ; une erreur 429 / 5xx ou un délai dépassé (`LLM_TIMEOUT`, défaut 300 s)
    est réessayé jusqu'à 6 fois avec une attente croissante. `LLM_REASONING_EFFORT` (optionnel,
    ex. `low`) limite la « réflexion » des modèles qui raisonnent avant de répondre (Gemini) ;
    si l'API refuse ce champ ou `seed`, il est retiré.
    """

    MAX_TOKENS = 1024  # marge pour les modèles qui « réfléchissent » avant de répondre

    def __init__(self, model_name: str | None = None, base_url: str | None = None) -> None:
        self.name = model_name or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        self.base_url = base_url or os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1"
        self.base_url = self.base_url.rstrip("/")
        self.min_interval = float(os.getenv("LLM_MIN_INTERVAL", "4"))
        self.timeout = float(os.getenv("LLM_TIMEOUT", "300"))
        self.reasoning_effort = os.getenv("LLM_REASONING_EFFORT") or None
        self.dropped: list[str] = []  # champs refusés par l'API (à noter dans le rapport)
        self._last = 0.0

    def _post(self, body: bytes) -> dict:
        import urllib.request

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ['LLM_API_KEY']}",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read())

    def generate(self, messages: list[dict], seed: int) -> str:
        import time
        import urllib.error

        payload = {
            "model": self.name,
            "messages": messages,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "seed": seed,
            "max_tokens": self.MAX_TOKENS,
        }
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort
        for field_name in self.dropped:
            payload.pop(field_name, None)
        for attempt in range(7):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                data = self._post(json.dumps(payload).encode())
                return data["choices"][0]["message"].get("content") or ""
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:1500]
                if exc.code == 400:
                    refused = next(
                        (
                            f
                            for f in ("reasoning_effort", "seed")
                            if f in payload and f in detail.lower()
                        ),
                        None,
                    )
                    refused = refused or (
                        "seed" if "seed" in payload and "model" not in detail.lower() else None
                    )
                    if refused:
                        payload.pop(refused)
                        self.dropped.append(refused)
                        continue
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 6:
                    raise RuntimeError(f"API LLM : HTTP {exc.code} — {detail}") from None
            except (TimeoutError, urllib.error.URLError, ConnectionError) as exc:
                if attempt == 6:
                    raise RuntimeError(f"API LLM injoignable : {exc}") from None
            time.sleep(min(60, 5 * 2**attempt))
        raise RuntimeError("API LLM : trop d'échecs")


def get_generator() -> Generator:
    provider = (os.getenv("LLM_PROVIDER") or "hf").lower()
    if provider in ("hf", "transformers", "none"):
        return TransformersGenerator()
    if provider in ("openai", "ollama"):
        return OpenAICompatibleGenerator()
    raise ValueError(f"LLM_PROVIDER={provider!r} inconnu (attendu : hf | openai | ollama)")
