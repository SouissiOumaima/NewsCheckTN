# Lot D - EXP-D-015 : Falcon-H1-3B en local avec format JSON impose (Ollama, GTX 1650 4 Go)
#
# PLAN FIXE AVANT LA MESURE (ce fichier est commite avant toute execution)
# Constat d'EXP-D-014 : sur le test, 9 reponses sur 21 (graine 42) sans JSON (json_absent),
# sorties valides 0,571 < 0,90 : regle non remplie. Seul changement ici : le format JSON est impose
# par Ollama (response_format = json_object, LLM_RESPONSE_FORMAT=json). Tout le reste est identique
# a EXP-D-014 (modele, quantification, prompt v1, temperature 0.3, top-p 0.9, graines 13/42/2026,
# recherche hybride top 5, NLI Bronze pour le repli).
# - Dev d'abord : sorties valides et exactitude, comparees a EXP-D-014 (aucun autre reglage).
# - Puis test gele UNE SEULE FOIS. C'est un 2e passage d'un systeme Falcon-H1-3B sur le meme test :
#   il est rapporte comme tel, avec EXP-D-014.
# - Regle de decision (inchangee) : Falcon-H1-3B est utilise pour la demo et l'integration locales si,
#   sur le test, (1) sorties valides >= 0,90 (graine 42), (2) exactitude moyenne (3 graines) >= majorite
#   (0,524) et (3) meilleur que le gabarit + NLI Bronze au bootstrap (p unilateral < 0,05).
#   Le resultat officiel du Silver reste Aya Expanse 8B (EXP-D-010, 0,730).
#
# Usage (nouvelle fenetre PowerShell, Ollama lance) :
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_015_falcon3b_json.ps1 -Split dev
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_015_falcon3b_json.ps1 -Split test   # une seule fois
param([ValidateSet("dev", "test")][string]$Split = "dev", [int]$Limit = 0)
$ErrorActionPreference = "Stop"
$Model = "hf.co/tiiuae/Falcon-H1-3B-Instruct-GGUF:Q4_K_M"

try { $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 10 }
catch { throw "Ollama ne repond pas sur localhost:11434 : lancer l'application Ollama." }
if (-not ($tags.models.name -contains $Model)) { throw "Modele absent : ollama pull $Model" }

$env:LLM_PROVIDER = "ollama"
$env:LLM_BASE_URL = "http://localhost:11434/v1"
$env:LLM_API_KEY = "ollama"          # Ollama n'utilise pas de cle ; le code en attend une
$env:LLM_MODEL = $Model
$env:LLM_MIN_INTERVAL = "0"
$env:LLM_TIMEOUT = "600"
$env:RETRIEVAL_METHOD = "hybrid"
$env:NLI_BACKEND = "bronze"
$env:LLM_RESPONSE_FORMAT = "json"
$env:LLM_CACHE = "evaluation/results/lot-d_llm_cache_exp-d-015.jsonl"   # cache separe : la cle du cache ne contient pas le format   # seul changement par rapport a EXP-D-014
Remove-Item Env:LLM_REASONING_EFFORT -ErrorAction SilentlyContinue

$pyArgs = @("-X", "utf8", "-m", "rag_llm.silver_verdict", "--main-only", "--splits", $Split)
if ($Limit -gt 0) { $pyArgs += @("--limit", "$Limit") }
$t = Get-Date
python @pyArgs
if ($LASTEXITCODE -ne 0) { throw "silver_verdict a echoue (code $LASTEXITCODE)" }
"Temps : {0:N1} min" -f ((Get-Date) - $t).TotalMinutes
