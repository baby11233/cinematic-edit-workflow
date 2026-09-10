param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$素材文件夹,
    [double]$抽帧间隔 = 0.3,
    [int]$并行数 = 2
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = $null
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) {
    $pythonPath = $pythonCommand.Source
}
if (-not $pythonPath) {
    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) { $pythonPath = $pyCommand.Source }
}
if (-not $pythonPath) {
    $runtimeRoot = Join-Path $env:USERPROFILE ".cache\codex-runtimes"
    if (Test-Path -LiteralPath $runtimeRoot) {
        $bundled = Get-ChildItem -LiteralPath $runtimeRoot -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($bundled) { $pythonPath = $bundled.FullName }
    }
}
if (-not $pythonPath) {
    Write-Error "未找到 Python。请安装 Python 3.10+，或在终端中直接用 Python 绝对路径运行 footage_indexer.py。"
    exit 1
}

& $pythonPath "$scriptDir\footage_indexer.py" $素材文件夹 --interval $抽帧间隔 --workers $并行数
exit $LASTEXITCODE
