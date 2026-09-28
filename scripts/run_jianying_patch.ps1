param(
    [Parameter(Mandatory=$true)][string]$Edl,
    [Parameter(Mandatory=$true)][string]$MaterialMap,
    [Parameter(Mandatory=$true)][string]$Output,
    [Parameter(Mandatory=$true)][string]$ProjectId,
    [Parameter(Mandatory=$true)][string]$DraftRef,
    [int]$BaseRevision = 0,
    [string]$RunId = "cinematic-edit-workflow",
    [switch]$SkipValidation
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$compiler = Join-Path $projectRoot "scripts\jianying_patch_compiler.py"

if (-not (Test-Path -LiteralPath $pythonPath)) { throw "缺少项目Python环境：$pythonPath" }
if (-not (Test-Path -LiteralPath $compiler)) { throw "缺少剪映补丁编译器：$compiler" }

$arguments = @(
    $compiler,
    $Edl,
    $MaterialMap,
    $Output,
    "--project-id", $ProjectId,
    "--draft-ref", $DraftRef,
    "--base-revision", $BaseRevision,
    "--run-id", $RunId
)

if (-not $SkipValidation) {
    $appsRoot = Join-Path $env:LOCALAPPDATA "JianyingPro\Apps"
    $agentCli = Get-ChildItem -LiteralPath $appsRoot -Filter "jianying-agent-cli.exe" -Recurse -File -ErrorAction SilentlyContinue |
        Sort-Object { try { [version]$_.Directory.Name } catch { [version]"0.0" } } -Descending |
        Select-Object -First 1
    if (-not $agentCli) { throw "找不到剪映Agent CLI。可使用-SkipValidation只生成计划，但不得据此宣称可应用。" }
    $arguments += @("--validate-cli", $agentCli.FullName)
}

& $pythonPath @arguments
exit $LASTEXITCODE
