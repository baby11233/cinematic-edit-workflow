# GitHub 发布与同步

本项目可存放在公开或私有 GitHub 仓库中。仓库可见性取决于协作需求；无论选择哪一种，都不要提交素材、成片、项目输出或凭据。

## 上传内容

- Skill 与完整工作流文档；
- 素材索引器源码；
- 安装、运行、验证脚本；
- 通过 Git LFS 保存的 FFmpeg 和离线 wheels。

## 明确排除

- `.venv` 本机虚拟环境；
- 素材、成片和任何项目 `edit` 输出；
- API Key、Token、`.env`；
- 临时日志、缓存和本地压缩包。

## 克隆

目标机器需要先安装 Git LFS：

```powershell
git lfs install
$RepositoryUrl = Read-Host "请输入仓库 URL"
$LocalDirectory = Read-Host "请输入本地安装目录"
git clone $RepositoryUrl $LocalDirectory
Set-Location $LocalDirectory
.\install.ps1
```

公开仓库允许任何人读取代码；私有仓库只允许仓库所有者、明确添加的协作者以及授权应用访问。两者都属于云端存储，不要把访问 Token 写入项目文件。
