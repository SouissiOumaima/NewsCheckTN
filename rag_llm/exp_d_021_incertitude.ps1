# Lot D - EXP-D-021 : incertitude du verdict calculee a partir du NLI
#
# PLAN FIXE AVANT LA MESURE : docs/lot-d_protocole_reranker_incertitude.md, section 4.
# - u = 1 - soutien des passages au verdict (confiances du NLI affine, aucun parametre regle).
# - Aucune nouvelle generation de Falcon : verdicts relus (dev : EXP-D-018 ; test : EXP-D-015).
# - Decision sur le dev : adoptee si la borne basse de l'IC 95 % de l'AUROC (verdict faux) > 0.5.
# - Test : descriptif seulement.
# Pas besoin d'Ollama.
#
# Usage (depuis Z:\NewsCheckTN) :
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_021_incertitude.ps1 -Split dev
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_021_incertitude.ps1 -Split test
param([Parameter(Mandatory = $true)][ValidateSet("dev", "test")][string]$Split)
$ErrorActionPreference = "Stop"
$Python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$Checkpoint = "models\checkpoints\nli_mdeberta-ft_v3_lr1e-05_e6_seed42"
if (-not (Test-Path $Checkpoint)) { throw "Checkpoint NLI absent : $Checkpoint" }
$env:RETRIEVAL_METHOD = "hybrid"
$env:NLI_BACKEND = "fine-tuned"
$env:CUDA_VISIBLE_DEVICES = ""
Remove-Item Env:NLI_FINETUNED_MODEL -ErrorAction SilentlyContinue
$t = Get-Date
& $Python -X utf8 -m rag_llm.gold_uncertainty --split $Split
if ($LASTEXITCODE -ne 0) { throw "gold_uncertainty a echoue (code $LASTEXITCODE)" }
"Temps : {0:N1} min" -f ((Get-Date) - $t).TotalMinutes
