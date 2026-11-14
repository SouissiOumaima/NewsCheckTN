# Grille Silver NLI (EXP-C-011), en serie. Test jamais lu (train.py ne charge que train et val).
# Usage, depuis la racine du depot :
#   powershell -ExecutionPolicy Bypass -File models\nli\run_grid.ps1 -Which main|ablation [-Lrs 2e-5,5e-5] [-Py <python.exe>]
# Journaux (non versionnes) : models\checkpoints\grid_v3\  (status_<Which>.txt, <Which>_lr<lr>_seed<graine>.log/.json)
# Puis : python models\nli\analyse_grid.py main|ablation
param(
    [ValidateSet("main", "ablation")][string]$Which = "main",
    [string[]]$Lrs = @(),
    [string]$Py = "python"
)
$ErrorActionPreference = "Continue"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path   # racine du depot (models\nli\..\..)
$Grid = Join-Path $Repo "models\checkpoints\grid_v3"
New-Item -ItemType Directory -Force $Grid | Out-Null
$Status = Join-Path $Grid "status_$Which.txt"
Set-Location $Repo
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"

if ($Which -eq "main") {
    $Base = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"; $Tag = "mdeberta-ft"
    if (-not $Lrs) { $Lrs = @("1e-5", "2e-5", "3e-5") }
} else {
    $Base = "microsoft/mdeberta-v3-base"; $Tag = "mdeberta-v3-base-ft"
    if (-not $Lrs) { $Lrs = @("2e-5", "3e-5", "5e-5") }
}
$Seeds = @(42, 123, 2026)

function Say($msg) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $msg" | Out-File -Append -Encoding utf8 $Status }

Say "GRILLE $Which : lr=$($Lrs -join ',') graines=$($Seeds -join ',') base=$Base"
$i = 0; $n = $Lrs.Count * $Seeds.Count
foreach ($lr in $Lrs) {
    foreach ($seed in $Seeds) {
        $i++
        # même nom que run_name() en Python (f"{lr:g}" : 1e-05)
        $lrName = ([double]::Parse($lr, [Globalization.CultureInfo]::InvariantCulture)).ToString("g", [Globalization.CultureInfo]::InvariantCulture).ToLower()
        $runDir = Join-Path $Repo ("models\checkpoints\nli_{0}_v3_lr{1}_e6_seed{2}" -f $Tag, $lrName, $seed)
        $log = Join-Path $Grid ("{0}_lr{1}_seed{2}.log" -f $Which, $lr, $seed)
        Say "START $i/$n  lr=$lr seed=$seed  -> $log"
        $cmd = "`"$Py`" -m models.nli.train --version v3 --seed $seed --lr $lr --epochs 6 --no-save --base-model $Base > `"$log`" 2>&1"
        cmd /c $cmd
        $code = $LASTEXITCODE
        # copie du journal : la relance finale (même nom de dossier) l'écraserait
        $runLog = Join-Path $runDir "train_log.json"
        if ($code -eq 0 -and (Test-Path $runLog)) {
            Copy-Item $runLog (Join-Path $Grid ("{0}_lr{1}_seed{2}.json" -f $Which, $lr, $seed)) -Force
            Say "END   $i/$n  lr=$lr seed=$seed  OK"
        } else {
            Say "END   $i/$n  lr=$lr seed=$seed  ECHEC (code $code) : voir $log"
        }
    }
}
Say "GRILLE $Which TERMINEE"
