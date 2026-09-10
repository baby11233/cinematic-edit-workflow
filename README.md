# Cinematic Edit Workflow 1.1.1

一套独立、可复制、本地运行的影视剪辑工作流，面向预筛选素材的混剪、作品集、宣传片和剧情片。

它不是 `video-use` 的补丁或派生运行层。素材索引、深度审片、剪辑决策、项目记忆、包装混音与交付检查均由本项目自己的 Skill、程序和规范定义。未来外部工作流的更新只在评估后手动吸收。

## 能做什么

- 批量扫描指定素材目录；
- PySceneDetect 自动给出候选分镜；
- FFmpeg 将候选分镜保存成独立预览镜头；
- 按0.3秒生成带源时间码的分页胶片条；
- 为快速动作和疑难区间提供0.2秒或更密集复查机制；
- 生成 HTML、JSON、CSV、Markdown 素材索引；
- 通过文件指纹复用缓存；
- 分别处理音乐混剪和剧情连续性剪辑；
- 保存审核、EDL、验证和项目决策，避免重复读取素材。

运行期间不上传视频、不调用云端识别服务。首次部署也可以使用随包保存的离线 Python wheels。

## 一次部署

在 PowerShell 中运行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
& ".\install.ps1"
```

安装程序会：

1. 检查 Windows x64、Python 3.12 和内置 FFmpeg；
2. 在本项目下创建 `.venv`；
3. 从 `vendor/wheels` 离线安装固定版本依赖；
4. 在当前 Codex Home 的 `skills` 目录建立指向本项目的目录联接；
5. 执行程序、依赖与 Skill 结构验证。

详细说明见 [docs/INSTALL.md](docs/INSTALL.md)。

## 生成素材索引

```powershell
& ".\run.ps1" "E:\项目\素材"
```

默认结果位于：

```text
E:\项目\素材\edit\footage_index\
```

Codex 读取顺序：

1. `CODEX_INDEX.md`
2. `manifest.json` 或 `shots.csv`
3. 当前待审核镜头的胶片条
4. 仅对存疑区间读取0.2秒或逐帧结果

## 调用 Skill

```text
使用 $cinematic-edit-workflow 剪辑这个项目，素材在……
```

## 项目结构

```text
cinematic-edit-workflow/
├── SKILL.md
├── VERSION
├── README.md
├── install.ps1
├── run.ps1
├── verify.ps1
├── agents/
├── docs/
├── references/
├── scripts/
│   ├── footage_indexer.py
│   └── bin/ffmpeg.exe
└── vendor/wheels/
```
