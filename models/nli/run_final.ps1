# Relance finale EXP-C-011 avec les poids (configurations choisies par la regle sur la val).
# Test jamais lu (train.py ne charge que train et val).
# Usage, depuis la racine du depot :
#   powershell -ExecutionPolicy Bypass -File models\nli\run_final.ps1 [-Py <python.exe>]
# Poids : models\checkpoints\nli_<modele>_v3_lr<lr>_e6_seed<graine>\  (non versionne)
# Journaux : models\checkpoints\grid_v3\final_*.log et status_final.txt
param([string]$Py = "python")
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path   # racine du depot (models\nli\..\..)
$Grid = Join-Path $Repo "models\checkpoints\grid_v3"
New-Item -ItemType Directory -Force $Grid | Out-Null
$Status = Join-Path $Grid "status_final.txt"
Set-Location $Repo
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"
function Say($msg) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $msg" | Out-File -Append -Encoding utf8 $Status }

# modele principal : lr 1e-5, epoque 1 ; ablation : lr 5e-5, epoque 5 (EXP-C-011, choix sur la val)
$runs = @()
foreach ($s in 42, 123, 2026) { $runs += ,@("main", "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7", "1e-5", 1, $s) }
foreach ($s in 42, 123, 2026) { $runs += ,@("ablation", "microsoft/mdeberta-v3-base", "5e-5", 5, $s) }

Say "RELANCE FINALE : $($runs.Count) executions, avec les poids"
$i = 0
foreach ($r in $runs) {
    $i++
    $which, $base, $lr, $k, $seed = $r
    $log = Join-Path $Grid ("final_{0}_lr{1}_k{2}_seed{3}.log" -f $which, $lr, $k, $seed)
    Say "START $i/$($runs.Count)  $which lr=$lr keep-epoch=$k seed=$seed"
    cmd /c "`"$Py`" -m models.nli.train --version v3 --seed $seed --lr $lr --epochs 6 --keep-epoch $k --base-model $base > `"$log`" 2>&1"
    if ($LASTEXITCODE -eq 0) { Say "END   $i/$($runs.Count)  $which seed=$seed  OK" } else { Say "END   $i/$($runs.Count)  $which seed=$seed  ECHEC (code $LASTEXITCODE)" }
}
Say "RELANCE FINALE TERMINEE"
