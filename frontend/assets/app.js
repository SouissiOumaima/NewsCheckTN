/* NewsCheck TN — base commune de la plateforme (toutes les pages).
 *
 * Fournit l'objet global `NC` :
 *   NC.PAGES            liste des pages du menu (ajouter une page = une ligne ici)
 *   NC.init(pageId)     dessine l'en-tête commun et vérifie que l'API répond
 *   NC.tiles(el, id)    cartes de navigation vers les autres pages
 *   NC.api(path, body)  appelle l'API (GET si body absent, sinon POST JSON)
 *   NC.esc, NC.text, NC.fmt, NC.verdictChip, NC.verdictBox, NC.LABELS : aides d'affichage
 *
 * URL de l'API : même adresse que la page quand elle est servie par l'API
 * (http://localhost:8000/app/), sinon http://localhost:8000. Modifiable dans l'en-tête
 * (« changer ») ; le choix est gardé dans le navigateur.
 */
const NC = (() => {
  const PAGES = [
    { id: "accueil", href: "index.html", icon: "✦", label: "Vérifier un texte",
      desc: "Coller un texte et obtenir un verdict cité pour chaque affirmation." },
    { id: "a1", href: "lot-a1.html", icon: "🗂️", label: "A1 · Données",
      desc: "Le corpus de preuves utilisé par l'API : sources et passages." },
    { id: "a2", href: "lot-a2.html", icon: "🔤", label: "A2 · Normalisation",
      desc: "Nettoyage du texte, langue et écriture (arabe, latin, arabizi)." },
    { id: "b", href: "lot-b.html", icon: "🧩", label: "B · Affirmations",
      desc: "Extraction des affirmations vérifiables, sujet-prédicat-objet, modalité." },
    { id: "c", href: "lot-c.html", icon: "🧠", label: "C · Modèles et NLI",
      desc: "Position d'un passage face à une affirmation : soutient, contredit, neutre." },
    { id: "d", href: "lot-d.html", icon: "🔎", label: "D · Preuves et verdict",
      desc: "Recherche des passages, verdict cité ou abstention." },
    { id: "evaluation", href: "evaluation.html", icon: "📊", label: "Évaluation",
      desc: "Les résultats de tous les lots, par langue et par expérience." },
  ];
  const LABELS = {
    vrai: "Vrai", faux: "Faux", trompeur: "Trompeur", preuves_insuffisantes: "Preuves insuffisantes",
  };
  const STANCES = { supports: "soutient", refutes: "contredit", neutral: "neutre" };
  const AR = /[؀-ۿ]/;
  const STORE_KEY = "newscheck-api";

  const defaultApi = () =>
    location.protocol.startsWith("http") && location.pathname.startsWith("/app")
      ? location.origin
      : "http://localhost:8000";

  function apiBase() {
    try { return localStorage.getItem(STORE_KEY) || defaultApi(); } catch { return defaultApi(); }
  }

  async function api(path, body) {
    let res;
    try {
      res = await fetch(apiBase() + path, body === undefined ? {} : {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
    } catch {
      throw new Error(`L'API ne répond pas à ${apiBase()}. Lance-la depuis la racine du dépôt : uvicorn api.main:app --reload`);
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail || data);
      throw new Error(`Erreur ${res.status} sur ${path} : ${detail}`);
    }
    return data;
  }

  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const text = (s) => `<span dir="auto"${AR.test(String(s ?? "")) ? ' class="ar"' : ""}>${esc(s)}</span>`;
  const fmt = (v, d = 2) => (v === null || v === undefined || Number.isNaN(+v)) ? "—" : Number(v).toFixed(d).replace(".", ",");
  const verdictChip = (label) => `<span class="verdict-chip v-${esc(label)}">${esc(LABELS[label] || label)}</span>`;
  const stanceChip = (s, conf) => `<span class="st st-${esc(s)}">${esc(STANCES[s] || s)}${conf ? " · " + fmt(conf) : ""}</span>`;

  /** Encadré de verdict : label, explication, citations, incertitude. `v` = Verdict de l'API. */
  function verdictBox(v, engine = {}) {
    const unc = Math.max(0, Math.min(1, +v.uncertainty || 0));
    const uncertainty = engine.used === "llm"
      ? '<span class="tag">incertitude non calibrée</span>'
      : `<span class="meter">indice d'incertitude (non calibré) <span class="track"><span class="fill" style="width:${Math.round(unc * 100)}%"></span></span><span class="num">${fmt(unc)}</span></span>`;
    const cites = (v.citations || []).map((c) => `<span class="tag">${esc(c)}</span>`).join(" ");
    return `<div class="verdict vb-${esc(v.label)}">
      <div class="row" style="align-items:center">${verdictChip(v.label)}
        ${uncertainty}
        ${v.abstained ? '<span class="tag">abstention</span>' : ""}</div>
      <pre dir="auto"${AR.test(v.explanation || "") ? ' class="ar"' : ""}>${esc(v.explanation)}</pre>
      ${cites ? `<div class="examples">Sources citées : ${cites}</div>` : (v.abstained ? "" : '<div class="error">Verdict sans citation : non conforme.</div>')}
    </div>`;
  }

  function header(pageId) {
    const nav = PAGES.map((p) => `<a href="${p.href}"${p.id === pageId ? ' aria-current="page"' : ""}><span class="ic" aria-hidden="true">${p.icon}</span>${esc(p.label)}</a>`).join("");
    const el = document.createElement("header");
    el.className = "nc-header";
    el.innerHTML = `<div class="in">
        <a class="nc-brand" href="index.html"><span class="logo" aria-hidden="true">✓</span><span>NewsCheck <span class="tn">TN</span></span></a>
        <nav class="nc-nav" aria-label="Pages de la plateforme">${nav}</nav>
        <div class="nc-api" id="nc-api"><span class="dot"></span><span id="nc-api-txt">API…</span><button type="button" id="nc-api-edit">changer</button></div>
      </div>
      <form class="nc-settings" id="nc-settings" hidden>
        <label class="field" style="flex:1 1 260px">Adresse de l'API<input type="url" id="nc-api-url"></label>
        <button class="btn" type="submit">Enregistrer</button>
        <button class="btn ghost" type="button" id="nc-api-reset">Par défaut</button>
      </form>`;
    document.body.prepend(el);
    const form = el.querySelector("#nc-settings");
    el.querySelector("#nc-api-edit").addEventListener("click", () => {
      form.hidden = !form.hidden;
      el.querySelector("#nc-api-url").value = apiBase();
    });
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      try { localStorage.setItem(STORE_KEY, el.querySelector("#nc-api-url").value.replace(/\/$/, "")); } catch {}
      form.hidden = true; ping();
    });
    el.querySelector("#nc-api-reset").addEventListener("click", () => {
      try { localStorage.removeItem(STORE_KEY); } catch {}
      form.hidden = true; ping();
    });
  }

  async function ping() {
    const box = document.getElementById("nc-api"), label = document.getElementById("nc-api-txt");
    box.className = "nc-api";
    try {
      const h = await api("/health");
      box.classList.add("ok"); label.textContent = `API ${h.version || ""} connectée`;
    } catch {
      box.classList.add("ko"); label.textContent = "API non joignable";
    }
  }

  function footer() {
    const f = document.createElement("footer");
    f.className = "nc-footer";
    f.innerHTML = `NewsCheck TN · projet NLP ESPRIM · pages servies par l'API sur <code>/app/</code> ; chaque lot complète sa page (voir <code>frontend/README.md</code>).`;
    document.body.append(f);
  }

  /** Cartes de navigation vers les autres pages (utilisées sur l'accueil). */
  function tiles(el, exceptId) {
    el.innerHTML = PAGES.filter((p) => p.id !== exceptId).map((p) => `
      <a class="tile" href="${p.href}"><span class="ic" aria-hidden="true">${p.icon}</span>
        <span class="t">${esc(p.label)}</span><span class="d">${esc(p.desc)}</span></a>`).join("");
  }

  /** Le modèle tenté ne devient pas le moteur d'un verdict de repli. */
  function verdictModelText(engine = {}) {
    if (!engine.model) return "";
    return `${engine.used === "llm" ? "modèle" : "modèle tenté"} : ${engine.model}`;
  }

  function init(pageId) { header(pageId); footer(); ping(); }

  return { PAGES, LABELS, STANCES, init, tiles, api, apiBase, esc, text, fmt, verdictChip, stanceChip, verdictBox, verdictModelText };
})();
