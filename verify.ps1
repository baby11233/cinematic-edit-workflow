param(
    [string]$CodexHome = (Join-Path $env:USERPROFILE ".codex")
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$ffmpegPath = Join-Path $projectRoot "scripts\bin\ffmpeg.exe"
$skillLink = Join-Path $CodexHome "skills\cinematic-edit-workflow"

$required = @(
    (Join-Path $projectRoot "SKILL.md"),
    (Join-Path $projectRoot "VERSION"),
    (Join-Path $projectRoot "scripts\footage_indexer.py"),
    (Join-Path $projectRoot "scripts\jianying_patch_compiler.py"),
    (Join-Path $projectRoot "references\jianying.md"),
    $ffmpegPath,
    $pythonPath
)
foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) { throw "缺少必要文件：$path" }
}

& $pythonPath -c "import cv2, PIL, scenedetect; print('Python dependencies: OK')"
if ($LASTEXITCODE -ne 0) { throw "Python依赖验证失败。" }
& $ffmpegPath -hide_banner -version | Select-Object -First 1
if ($LASTEXITCODE -ne 0) { throw "FFmpeg验证失败。" }
& $pythonPath (Join-Path $projectRoot "scripts\footage_indexer.py") --help | Out-Null
if ($LASTEXITCODE -ne 0) { throw "索引器启动验证失败。" }
& $pythonPath (Join-Path $projectRoot "scripts\jianying_patch_compiler.py") --help | Out-Null
if ($LASTEXITCODE -ne 0) { throw "剪映补丁编译器启动验证失败。" }
& $pythonPath -m unittest discover -s (Join-Path $projectRoot "tests") -p "test_*.py"
if ($LASTEXITCODE -ne 0) { throw "测试失败。" }
if (-not (Test-Path -LiteralPath $skillLink)) { throw "Codex Skill未注册：$skillLink" }

Write-Host "Cinematic Edit Workflow $(Get-Content -Raw (Join-Path $projectRoot 'VERSION')) 验证通过。"
