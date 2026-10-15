# macOS 安装（Apple Silicon 与 Intel）

macOS 版不内置二进制，也不使用 Git LFS 的 Windows 离线包：FFmpeg 来自 Homebrew，Python 依赖从 PyPI 安装（PyPI 提供 arm64 与 x86_64 轮子）。

## 前置条件

- macOS 12 或更高
- Homebrew
- Python 3.10+（推荐 3.12）与 FFmpeg（需包含 `ffprobe`）

```bash
brew install python@3.12 ffmpeg
```

## 安装

```bash
git clone <仓库 URL> cinematic-edit-workflow
cd cinematic-edit-workflow
./install.sh                 # 默认链接到 ~/.codex/skills
./install.sh --claude-skills # 同时链接到 ~/.claude/skills
```

`install.sh` 会创建 `.venv`、安装 `scripts/requirements-lock.txt`、用符号链接注册 Skill，并运行 `verify.sh`。已有同名普通目录会被改名备份，不会被删除。

如果克隆时 Git LFS 拉取了 Windows 的 `ffmpeg.exe` 与 wheels，macOS 会忽略它们；只想要 macOS 版可用 `GIT_LFS_SKIP_SMUDGE=1 git clone ...`。

## 使用

```bash
./run.sh /Volumes/SSD/footage --output-dir /Volumes/SSD/project/edit/footage_index
```

- 默认自动选择 `h264_videotoolbox` 生成浏览用镜头片段，速度明显快于 `libx264`；需要软编码时加 `--encoder libx264`。
- 胶片条中文标签使用系统 PingFang 字体，无需额外安装。
- 外接盘路径包含空格时请加引号。

## macOS 常见问题

- **“无法验证开发者”弹窗**：只会出现在手动下载的二进制上；Homebrew 的 FFmpeg 不受影响。
- **Codex 找不到 ffmpeg**：从 Dock/Finder 启动的应用不继承终端的 PATH。脚本已显式查找 `/opt/homebrew/bin` 与 `/usr/local/bin`；其他位置请用 `--ffmpeg` 指定。
- **完全磁盘访问权限**：素材在外接盘或“桌面/文档”时，需在系统设置 > 隐私与安全性中授予运行 Codex 的终端或应用访问权限，否则索引会报“Operation not permitted”。
- **剪映**：见 `references/jianying.md` 的“macOS”一节；macOS 上推荐使用达芬奇后端（`references/davinci.md`）。

## 跨系统迁移同一个项目

索引缓存以内容指纹（大小 + 头尾字节）而不是绝对路径识别素材，`SRC` 编号记录在 `source_registry.json` 中并只增不改。把素材与 `edit/` 一起拷到 Mac 后重新运行 `run.sh`，会命中缓存并只更新源路径；导出 EDL 时用 `--path-map` 重写盘符前缀即可。
