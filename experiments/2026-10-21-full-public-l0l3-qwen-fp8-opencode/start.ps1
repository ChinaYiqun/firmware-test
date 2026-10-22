param(
    [switch]$ResumeLatest,
    [string]$RunPath,
    [int]$Count = 0,
    [switch]$DryRun,
    [switch]$NoGui
)

$ErrorActionPreference = 'Stop'
$experimentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $experimentDir '..\..')).Path
$python = Join-Path $repoRoot 'experiments\2026-10-20-opus5-harness-comparison\.venv\Scripts\python.exe'
$manifest = Get-Content -LiteralPath (Join-Path $experimentDir 'subsets\public-l0-l3.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$maximum = @($manifest.cases).Count
if (-not (Test-Path -LiteralPath $python)) { throw "Missing Python environment: $python" }

$run = $null
$approvedInForm = $false
if ($RunPath) {
    $run = (Resolve-Path -LiteralPath $RunPath).Path
} elseif ($ResumeLatest) {
    $runs = @(Get-ChildItem -LiteralPath (Join-Path $experimentDir 'runs') -Directory -Filter 'run-*' -ErrorAction SilentlyContinue |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'config.json') } |
        Sort-Object LastWriteTime -Descending)
    if ($runs.Count -eq 0) { throw 'No formal run is available to resume.' }
    $run = $runs[0].FullName
}

if ($run) {
    $config = Get-Content -LiteralPath (Join-Path $run 'config.json') -Encoding UTF8 -Raw | ConvertFrom-Json
    $DryRun = [bool]$config.dry_run
    $selected = [int]$config.selected_count
    $runner = Join-Path $run 'frozen-runner.py'
    if (-not (Test-Path -LiteralPath $runner)) { throw "Missing frozen runner: $runner" }
    $pending = [int](& $python (Join-Path $experimentDir 'pending.py') $run)
    if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the run database.' }
    if ($pending -le 0) {
        Write-Host "This run already has all $selected terminal results: $run"
        exit 0
    }
    $question = "Continue run? $pending of $selected cases remain.`n$run"
} else {
    if ($Count -eq 0 -and -not $NoGui) {
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $form = New-Object System.Windows.Forms.Form
        $form.Text = 'EmbedEval L0/L3 - OpenCode FP8'
        $form.Width = 440
        $form.Height = 190
        $form.StartPosition = 'CenterScreen'
        $form.TopMost = $true
        $label = New-Object System.Windows.Forms.Label
        $label.Text = "可运行 $maximum 道公开题。请选择本次题数："
        $label.Left = 20; $label.Top = 20; $label.Width = 380
        $input = New-Object System.Windows.Forms.NumericUpDown
        $input.Minimum = 1; $input.Maximum = $maximum; $input.Value = $maximum
        $input.Left = 20; $input.Top = 52; $input.Width = 160
        $start = New-Object System.Windows.Forms.Button
        $start.Text = '确认并开始'; $start.Left = 210; $start.Top = 95; $start.Width = 100
        $start.DialogResult = [System.Windows.Forms.DialogResult]::OK
        $cancel = New-Object System.Windows.Forms.Button
        $cancel.Text = '取消'; $cancel.Left = 320; $cancel.Top = 95; $cancel.Width = 80
        $cancel.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
        $form.Controls.AddRange(@($label, $input, $start, $cancel))
        $form.AcceptButton = $start; $form.CancelButton = $cancel
        if ($form.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { exit 0 }
        $Count = [int]$input.Value
        $approvedInForm = $true
        $form.Dispose()
    } elseif ($Count -eq 0) {
        $answer = Read-Host "How many of the $maximum public cases should run? [$maximum]"
        $Count = if ([string]::IsNullOrWhiteSpace($answer)) { $maximum } else { [int]$answer }
    }
    if ($Count -lt 1 -or $Count -gt $maximum) { throw "Count must be 1..$maximum" }
    $selected = $Count
    $runner = Join-Path $experimentDir 'run_benchmark.py'
    $question = "Start $selected of $maximum public cases with OpenCode / qwen3.8-27b-coder390-fp8?"
}

if ($NoGui) {
    $answer = Read-Host "$question Type YES to continue"
    if ($answer -cne 'YES') { Write-Host 'Cancelled.'; exit 0 }
} elseif (-not $approvedInForm) {
    Add-Type -AssemblyName System.Windows.Forms
    $choice = [System.Windows.Forms.MessageBox]::Show($question, 'Confirm benchmark run',
        [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)
    if ($choice -ne [System.Windows.Forms.DialogResult]::Yes) { Write-Host 'Cancelled.'; exit 0 }
}

$concurrency = if ($run) { [int]$config.concurrency } else { 2 }
$timeout = if ($run) { [int]$config.timeout_seconds } else { 600 }
$repetitions = if ($run) { [int]$config.repetitions } else { 1 }
$arguments = @($runner, '--experiment-dir', $experimentDir, '--limit', "$selected",
               '--concurrency', "$concurrency", '--timeout', "$timeout", '--repetitions', "$repetitions")
if ($DryRun) { $arguments += '--dry-run' } else { $arguments += '--yes' }
if ($run) { $arguments += @('--resume', $run) }
Write-Host "Run: $selected/$maximum cases; L0+L3 only; concurrency $concurrency; resume=$([bool]$run)"
Push-Location $repoRoot
try {
    & $python @arguments
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
