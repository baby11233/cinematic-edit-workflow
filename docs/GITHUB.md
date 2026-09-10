# 私有 GitHub 仓库

本项目建议只存放在 GitHub Private 仓库中。

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
git clone <private-repository-url>
cd cinematic-edit-workflow
.\install.ps1
```

私有仓库仍属于云端存储。只有仓库所有者、明确添加的协作者以及授权应用可以访问；不要把访问Token写入项目文件。
