param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$素材文件夹,
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$IndexerArguments
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) {
    Write-Error "本地运行环境不存在。请先运行：.\install.ps1"
    exit 1
}

$indexer = Join-Path $projectRoot "scripts\footage_indexer.py"
& $pythonPath $indexer $素材文件夹 @IndexerArguments
exit $LASTEXITCODE
