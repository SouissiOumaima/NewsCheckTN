# Lot D - EXP-D-020 : re-ranker cross-encoder apres la recherche hybride
#
# PLAN FIXE AVANT LA MESURE : docs/lot-d_protocole_reranker_incertitude.md, section 3.
# - Modele : BAAI/bge-reranker-v2-m3 (CPU). Repli cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
#   seulement si plus de 15 s par affirmation sur le dev (critere de vitesse uniquement).
# - 20 candidats de la fusion RRF, top 5 apres re-ranking.
# - Dev d'abord (controle et vitesse), puis test Tunifact v1 UNE SEULE FOIS.
# - Adopte si le rappel@5 du test augmente (p unilateral < 0.05) et si celui du dev ne baisse pas.
# Pas besoin d'Ollama : seuls la recherche et le re-ranker tournent (CPU).
#
# Usage (depuis Z:\NewsCheckTN) :
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_020_reranker.ps1 -Split dev
#   powershell -ExecutionPolicy Bypass -File .\rag_llm\exp_d_020_reranker.ps1 -Split test
param(
    [Parameter(Mandatory = $true)][ValidateSet("dev", "test")][string]$Split,
    [ValidateSet("principal", "repli")][string]$Model = "principal"
)
$ErrorActionPreference = "Stop"
$Python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
if ($Split -eq "test" -and -not (Test-Path "data\interim\lot_d\evidence_tunifact_v1.jsonl")) {
    throw "Corpus du test absent : data\interim\lot_d\evidence_tunifact_v1.jsonl"
}
$env:RETRIEVAL_METHOD = "hybrid"
$env:CUDA_VISIBLE_DEVICES = ""       # e5 et le re-ranker sur le CPU
$pyArgs = @("-X", "utf8", "-m", "rag_llm.gold_reranker", "--split", $Split)
if ($Split -eq "dev") { $pyArgs += @("--model", $Model) }
$t = Get-Date
& $Python @pyArgs
if ($LASTEXITCODE -ne 0) { throw "gold_reranker a echoue (code $LASTEXITCODE)" }
"Temps : {0:N1} min" -f ((Get-Date) - $t).TotalMinutes
