# Lot D - EXP-D-020 (suite) : effet du re-ranker sur le verdict, dev seulement
#
# REGLE FIXEE AVANT : docs/lot-d_protocole_reranker_incertitude.md, section 3 :
# Falcon sur le dev (30 phrases, 3 graines) avec les passages du re-ranker ; au plus 1 bonne
# reponse perdue (graine 42) par rapport a EXP-D-018. Aucun verdict genere sur le test.
#
# Usage (Ollama lance, depuis Z:\NewsCheckTN) :
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_020_verdict_dev.ps1
$ErrorActionPreference = "Stop"
$Model = "hf.co/tiiuae/Falcon-H1-3B-Instruct-GGUF:Q4_K_M"
try { $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 10 }
catch { throw "Ollama ne repond pas sur localhost:11434 : lancer l'application Ollama." }
if (-not ($tags.models.name -contains $Model)) { throw "Modele absent : ollama pull $Model" }
$Python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$env:LLM_PROVIDER = "ollama"
$env:LLM_BASE_URL = "http://localhost:11434/v1"
$env:LLM_API_KEY = "ollama"
$env:LLM_MODEL = $Model
$env:LLM_MIN_INTERVAL = "0"
$env:LLM_TIMEOUT = "600"
$env:LLM_RESPONSE_FORMAT = "json"
$env:LLM_ALLOW_EXTERNAL = "0"
$env:RETRIEVAL_METHOD = "hybrid"
$env:NLI_BACKEND = "fine-tuned"
$env:CUDA_VISIBLE_DEVICES = ""       # NLI, e5 et re-ranker sur le CPU ; le GPU reste a Ollama
$env:LLM_CACHE = "evaluation/results/lot-d_llm_cache_exp-d-020.jsonl"
Remove-Item Env:LLM_REASONING_EFFORT -ErrorAction SilentlyContinue
Remove-Item Env:NLI_FINETUNED_MODEL -ErrorAction SilentlyContinue
$t = Get-Date
& $Python -X utf8 -m rag_llm.gold_reranker_verdict
if ($LASTEXITCODE -ne 0) { throw "gold_reranker_verdict a echoue (code $LASTEXITCODE)" }
"Temps : {0:N1} min" -f ((Get-Date) - $t).TotalMinutes
