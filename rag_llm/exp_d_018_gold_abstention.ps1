# Lot D - EXP-D-018 (Gold) : regle d'abstention R-abst sur le dev, Falcon-H1-3B local + NLI affine
#
# PLAN FIXE AVANT LA MESURE : docs/lot-d_protocole_gold.md (commits fe97fdc et da06966), section 5.
# - Jeu : dev du Lot D (20 affirmations fictives) + 10 phrases hors sujet
#   (data/interim/lot_d/claims_dev_hors_sujet.jsonl, SHA-256 verifie par le script). JAMAIS le test.
# - Systeme : comme EXP-D-015 (Falcon-H1-3B Q4_K_M, prompt v1, JSON impose, temperature 0.3,
#   graines 13/42/2026, recherche hybride top 5). Seul changement : NLI affine du Lot C
#   (NLI_BACKEND=fine-tuned, EXP-C-011) au lieu de Bronze. Le LLM ne voit pas le NLI : il ne sert
#   qu'au repli et a R-abst.
# - R-abst : tous les passages cites neutres -> preuves insuffisantes (aucun seuil).
# - Decision (graine 42) : adoptee si l'abstention justifiee augmente ET si l'on perd au plus
#   1 bonne reponse sur les affirmations qui ont une preuve.
# - NLI et e5 sur le CPU (CUDA_VISIBLE_DEVICES vide) : le GPU de 4 Go reste a Falcon (Ollama).
#
# Usage (Ollama lance, depuis Z:\NewsCheckTN) :
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_018_gold_abstention.ps1 -Limit 3   # essai
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_018_gold_abstention.ps1            # mesure
param([int]$Limit = 0)
$ErrorActionPreference = "Stop"
$Model = "hf.co/tiiuae/Falcon-H1-3B-Instruct-GGUF:Q4_K_M"
$Checkpoint = "models\checkpoints\nli_mdeberta-ft_v3_lr1e-05_e6_seed42"

try { $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 10 }
catch { throw "Ollama ne repond pas sur localhost:11434 : lancer l'application Ollama." }
if (-not ($tags.models.name -contains $Model)) { throw "Modele absent : ollama pull $Model" }
if (-not (Test-Path $Checkpoint)) { throw "Checkpoint NLI absent : $Checkpoint (kit d'Achref)" }
if (-not (Test-Path "data\interim\lot_d\claims_dev_hors_sujet.jsonl")) {
    throw "Phrases hors sujet absentes : data\interim\lot_d\claims_dev_hors_sujet.jsonl"
}

$Python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

$env:LLM_PROVIDER = "ollama"
$env:LLM_BASE_URL = "http://localhost:11434/v1"
$env:LLM_API_KEY = "ollama"          # Ollama n'utilise pas de cle ; le code en attend une
$env:LLM_MODEL = $Model
$env:LLM_MIN_INTERVAL = "0"
$env:LLM_TIMEOUT = "600"
$env:LLM_RESPONSE_FORMAT = "json"
$env:LLM_ALLOW_EXTERNAL = "0"
$env:RETRIEVAL_METHOD = "hybrid"
$env:NLI_BACKEND = "fine-tuned"      # seul changement par rapport a EXP-D-015
$env:CUDA_VISIBLE_DEVICES = ""       # NLI et e5 sur le CPU
$env:LLM_CACHE = "evaluation/results/lot-d_llm_cache_exp-d-018.jsonl"
Remove-Item Env:LLM_REASONING_EFFORT -ErrorAction SilentlyContinue
Remove-Item Env:NLI_FINETUNED_MODEL -ErrorAction SilentlyContinue

$pyArgs = @("-X", "utf8", "-m", "rag_llm.gold_abstention")
if ($Limit -gt 0) { $pyArgs += @("--limit", "$Limit") }
$t = Get-Date
& $Python @pyArgs
if ($LASTEXITCODE -ne 0) { throw "gold_abstention a echoue (code $LASTEXITCODE)" }
"Temps : {0:N1} min" -f ((Get-Date) - $t).TotalMinutes
