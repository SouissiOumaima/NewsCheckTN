# Lot D - EXP-D-014 : Falcon-H1-3B en local (Ollama, GTX 1650 4 Go)
#
# PLAN FIXE AVANT LA MESURE (ce fichier est commite avant toute execution)
# Question : un LLM qui tourne entierement sur le PC de l'equipe (GPU 4 Go) donne-t-il des verdicts
# utilisables pour l'integration locale (Lot E), sans GPU distant ni API ?
# - Modele : Falcon-H1-3B-Instruct, GGUF Q4_K_M (hf.co/tiiuae/Falcon-H1-3B-Instruct-GGUF:Q4_K_M),
#   servi par Ollama (100 % GPU, 2,1 Go). C'est exactement la configuration de la demo locale.
# - Meme protocole qu'EXP-D-010 : rag_llm.silver_verdict --main-only, prompt v1, temperature 0.3,
#   top-p 0.9, graines 13 / 42 / 2026, recherche hybride top 5, NLI Bronze pour le gabarit de repli.
#   Differences inevitables : quantification GGUF (pas bitsandbytes) et max_tokens 1024 (API).
# - Dev d'abord (sorties valides), puis test gele UNE SEULE FOIS.
# - Regle de decision : Falcon-H1-3B est utilise pour la demo et l'integration locales si, sur le
#   test, (1) sorties valides >= 0,90 (graine 42), (2) exactitude moyenne (3 graines) >= majorite
#   (0,524) et (3) meilleur que le gabarit + NLI Bronze au bootstrap (p unilateral < 0,05).
#   Le resultat officiel du Silver reste Aya Expanse 8B (EXP-D-010, 0,730) ; tout ecart est rapporte.
#
# Usage (nouvelle fenetre PowerShell, Ollama lance) :
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_014_falcon3b_local.ps1 -Split dev
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_014_falcon3b_local.ps1 -Split test   # une seule fois
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
Remove-Item Env:LLM_REASONING_EFFORT -ErrorAction SilentlyContinue

$pyArgs = @("-X", "utf8", "-m", "rag_llm.silver_verdict", "--main-only", "--splits", $Split)
if ($Limit -gt 0) { $pyArgs += @("--limit", "$Limit") }
$t = Get-Date
python @pyArgs
if ($LASTEXITCODE -ne 0) { throw "silver_verdict a echoue (code $LASTEXITCODE)" }
"Temps : {0:N1} min" -f ((Get-Date) - $t).TotalMinutes
