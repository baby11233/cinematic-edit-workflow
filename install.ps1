param(
    [string]$PythonPath,
    [string]$CodexHome = (Join-Path $env:USERPROFILE ".codex"),
    [switch]$AllowOnline
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Resolve-Python {
    param([string]$Requested)
    if ($Requested) {
        if (-not (Test-Path -LiteralPath $Requested)) { throw "Python不存在：$Requested" }
        return (Resolve-Path -LiteralPath $Requested).Path
    }
    foreach ($name in @("python", "py")) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) { return $command.Source }
    }
    $runtimeRoot = Join-Path $env:USERPROFILE ".cache\codex-runtimes"
    if (Test-Path -LiteralPath $runtimeRoot) {
        $candidate = Get-ChildItem -LiteralPath $runtimeRoot -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match "dependencies\\python\\python.exe$" } |
            Select-Object -First 1
        if ($candidate) { return $candidate.FullName }
    }
    throw "未找到Python 3.12 x64。请安装后使用 -PythonPath 指定。"
}

$basePython = Resolve-Python $PythonPath
$version = & $basePython -c "import platform,sys; print(f'{sys.version_info.major}.{sys.version_info.minor}|{platform.machine()}')"
if ($LASTEXITCODE -ne 0 -or $version.Trim() -notmatch '^3\.12\|AMD64$') {
    throw "离线依赖包要求Python 3.12 x64，当前为：$version"
}

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    & $basePython -m venv (Join-Path $projectRoot ".venv")
    if ($LASTEXITCODE -ne 0) { throw "创建虚拟环境失败。" }
}

$lockFile = Join-Path $projectRoot "scripts\requirements-lock.txt"
$wheelDir = Join-Path $projectRoot "vendor\wheels"
if ((Test-Path -LiteralPath $wheelDir) -and (Get-ChildItem -LiteralPath $wheelDir -File -ErrorAction SilentlyContinue)) {
    & $venvPython -m pip install --no-index --find-links $wheelDir -r $lockFile
} elseif ($AllowOnline) {
    & $venvPython -m pip install -r $lockFile
} else {
    throw "离线依赖不存在：$wheelDir。重新取得完整项目包，或明确使用 -AllowOnline。"
}
if ($LASTEXITCODE -ne 0) { throw "安装Python依赖失败。" }

$skillsRoot = Join-Path $CodexHome "skills"
New-Item -ItemType Directory -Force $skillsRoot | Out-Null
$skillLink = Join-Path $skillsRoot "cinematic-edit-workflow"
if (Test-Path -LiteralPath $skillLink) {
    $item = Get-Item -LiteralPath $skillLink -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        $resolved = $item.Target
        if ($resolved -eq $projectRoot) {
            Write-Host "Skill目录联接已存在。"
        } else {
            throw "目标位置已有指向其他目录的联接：$skillLink -> $resolved"
        }
    } else {
        $backup = "$skillLink.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Move-Item -LiteralPath $skillLink -Destination $backup
        New-Item -ItemType Junction -Path $skillLink -Target $projectRoot | Out-Null
        Write-Host "旧Skill已备份：$backup"
    }
} else {
    New-Item -ItemType Junction -Path $skillLink -Target $projectRoot | Out-Null
}

& (Join-Path $projectRoot "verify.ps1") -CodexHome $CodexHome
if ($LASTEXITCODE -ne 0) { throw "安装后验证失败。" }
Write-Host "安装完成。请新建或重启Codex任务以重新加载Skill。"
