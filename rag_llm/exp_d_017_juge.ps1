# Lot D - EXP-D-017 (Gold) : LLM-juge local (Qwen2.5-3B) valide sur l'annotation humaine
#
# PLAN FIXE AVANT LA MESURE : docs/lot-d_protocole_gold.md (sections 4 et 6) et rag_llm/gold_judge.py.
# - Juge : qwen2.5:3b-instruct (Ollama, local), different de Falcon ; prompt rag_llm/prompts/juge_v1.txt ;
#   temperature 0, graine 42, JSON impose.
# - Unites : les 30 verdicts de Falcon (graine 42) d'EXP-D-018, partages en 2 moities (graine 42) :
#   "mise_au_point" (le prompt peut y etre ameliore : nouveau fichier juge_v2.txt, etc.)
#   puis "mesure" (UNE SEULE FOIS, prompt fige).
# - Validation : kappa de Cohen >= 0.60 avec l'annotation humaine, par etiquette, sur "mesure".
#
# Usage (Ollama lance, depuis Z:\NewsCheckTN) :
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_017_juge.ps1 -Part mise_au_point
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_017_juge.ps1 -Part mesure -Prompt juge_v1
param(
    [Parameter(Mandatory = $true)][ValidateSet("mise_au_point", "mesure")][string]$Part,
    [string]$Prompt = "juge_v1"
)
$ErrorActionPreference = "Stop"
$Model = "qwen2.5:3b-instruct"

try { $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 10 }
catch { throw "Ollama ne repond pas sur localhost:11434 : lancer l'application Ollama." }
if (-not ($tags.models.name -contains $Model)) { throw "Modele absent : ollama pull $Model" }
if (-not (Test-Path "evaluation\results\lot-d_annotation_hadil_dev_annote.csv")) {
    throw "Annotation absente : evaluation\results\lot-d_annotation_hadil_dev_annote.csv"
}

$Python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

$env:LLM_PROVIDER = "ollama"
$env:LLM_BASE_URL = "http://localhost:11434/v1"
$env:LLM_API_KEY = "ollama"
$env:LLM_MODEL = $Model
$env:LLM_MIN_INTERVAL = "0"
$env:LLM_TIMEOUT = "600"
$env:LLM_RESPONSE_FORMAT = "json"
$env:LLM_ALLOW_EXTERNAL = "0"
$env:LLM_CACHE = "evaluation/results/lot-d_llm_cache_exp-d-017.jsonl"
Remove-Item Env:LLM_REASONING_EFFORT -ErrorAction SilentlyContinue

$t = Get-Date
& $Python -X utf8 -m rag_llm.gold_judge --part $Part --prompt $Prompt
if ($LASTEXITCODE -ne 0) { throw "gold_judge a echoue (code $LASTEXITCODE)" }
"Temps : {0:N1} min" -f ((Get-Date) - $t).TotalMinutes
