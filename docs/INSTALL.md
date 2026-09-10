# 安装与复刻

## 支持环境

- Windows 10/11 x64
- PowerShell 5.1 或更高
- Python 3.12 x64
- Codex Desktop 或能够读取个人 Skills 目录的 Codex 环境

项目内置 FFmpeg，因此不要求系统 PATH 中存在 FFmpeg。Python 包默认从 `vendor/wheels` 离线安装，不依赖安装时访问 GitHub或 PyPI。

## 在另一台电脑复刻

1. 将整个 `cinematic-edit-workflow` 文件夹复制到任意固定目录，推荐：

   ```text
   D:\AI\codex\cinematic-edit-workflow
   ```

2. 安装 Python 3.12 x64。如果机器安装了 Codex Desktop，安装程序也会尝试寻找 Codex 自带的 Python 3.12 运行时。
3. 在项目目录打开 PowerShell：

   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\install.ps1
   ```

4. 运行验证：

   ```powershell
   .\verify.ps1
   ```

5. 重启或新建 Codex 任务，使 Skill 列表重新加载。

## 指定 Python 或 Codex Home

```powershell
.\install.ps1 `
  -PythonPath "C:\Python312\python.exe" `
  -CodexHome "C:\Users\用户名\.codex"
```

## 安装模型

项目目录是唯一真实副本。安装程序在：

```text
<CodexHome>\skills\cinematic-edit-workflow
```

建立指向项目目录的 Windows 目录联接，不复制代码。更新项目文件后，Codex 读取的仍是同一份内容。

如果目标位置已有普通目录，安装程序不会删除它，而是重命名为带时间戳的备份目录。

## 运行

```powershell
.\run.ps1 "E:\素材目录"
```

附加参数会原样传给索引器，例如：

```powershell
.\run.ps1 "E:\素材目录" --interval 0.2 --min-scene-len 0.7 --workers 3
```

## 卸载

删除 Codex Skills 目录中的目录联接即可。不要删除项目目录，除非确定不再需要程序、文档、离线依赖和项目版本记录。

```powershell
Remove-Item -LiteralPath "$env:USERPROFILE\.codex\skills\cinematic-edit-workflow"
```

目录联接的删除不会删除其指向的项目内容。
