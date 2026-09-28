# Cinematic Edit Workflow 1.3.0

一套面向 **AI 生成素材、多 take 素材和连续剧情素材** 的本地影视剪辑工作流。它把“先看懂素材，再做剪辑决定”固化为可复用的 Codex Skill：高密度审片、表演优先选材、源时间码 EDL、持续项目记忆、时间线执行与成片 QC 都有明确产物和质量门槛。

项目适用于剧情短片、预告片、宣传片、作品集和音乐混剪。所有素材分析均在本地完成，不上传视频，也不依赖云端识别服务。

> 本项目独立于 `video-use`，不是它的补丁或派生运行层。外部工作流的更新只在评估后手动吸收。

## 为什么需要这套工作流

常见的自动剪辑容易停留在“检测场景并拼接”的层面，却忽略真正决定成片质量的细节：同一句台词该选哪个 take、反应镜头是否比说话镜头更有力量、动作能否连续、穿帮是否进入注意中心、音乐转折是否与叙事转折一致。

本项目把这些判断拆成可检查的流程：

- **表演优先**：优先评价微表情、眼神、动作完成度、关系张力和台词落点，而不是只看画质或镜头长度；
- **保留源时间码**：每个入选区间都能回到原片复核，避免代理素材和切分素材造成时间漂移；
- **高密度视觉复查**：默认以 0.3 秒胶片条理解镜头，对快速动作和疑难区间提升到 0.2 秒或逐帧检查；
- **连续性与瑕疵分开评估**：不为规避轻微瑕疵牺牲更强表演，也不让明显穿帮因剧情正确而被忽略；
- **决策可追溯**：审核结论、选材理由、EDL、验证结果和项目记忆都保存为文件，后续迭代无需从头看素材；
- **预览后再锁片**：粗剪、结构复查、精修、混音和最终交付分别设有检查点。

## 工作流概览

```text
原始素材 + 剧本/音乐
        │
        ▼
素材扫描与场景检测 ──► 候选镜头 + 代理片段
        │
        ▼
0.3s 胶片条审片 ──► 疑难区间 0.2s / 逐帧复查
        │
        ▼
表演、连续性、瑕疵与修复成本联合评估
        │
        ▼
剪辑方案 + 源时间码 EDL + 项目记忆
        │
        ├──► 通用本地成片流程
        │
        └──► 剪映 11.5 可编辑工程流程
                    │
                    ▼
              预览、精修、导出与 QC
```

## 核心能力

- 批量扫描视频、音频与剧本文档，使用文件指纹复用缓存；
- 通过 PySceneDetect 生成候选分镜，并用 FFmpeg 保存独立预览镜头；
- 输出带源时间码的 HTML、JSON、CSV、Markdown 素材索引和分页胶片条；
- 针对音乐混剪与剧情连续性剪辑采用不同的审核、节奏和覆盖逻辑；
- 对重复生成、多 take 和 AI 抽卡素材执行表演优先的微区间选材；
- 使用说话者、倾听者、双人关系、信息插入和中性桥接构建覆盖剪辑；
- 对越轴、跳切和画面瑕疵优先采用有叙事依据的重构，并单独验证镜像、裁切等修复；
- 保存可复用的剪辑方案、EDL、QC 结果与项目决策；
- 在明确选择剪映专业版时，将 EDL 编译为经过验证的剪映 11.5 装配计划，并把可编辑工程归档纳入交付。

## 目录约定与可移植性

项目不绑定盘符、用户名或固定文件夹。说明中的路径均应理解为运行时参数，而不是必须照搬的目录结构：

- **仓库目录**：本项目代码所在位置，可以放在任意本地固定目录；
- **素材目录**：原始视频和音频所在位置，可以位于其他磁盘或外接存储；
- **项目目录**：保存审核、EDL、预览、QC 和编辑工程的工作区；
- **输出目录**：默认可放在素材目录下，也可以通过 `--output-dir` 指向项目目录中的任意位置。

仓库、素材和项目输出可以位于三个不同位置。脚本通过自身位置寻找内置程序，通过传入参数寻找素材和输出，不依赖当前机器上的示例盘符。

这里的可移植性指 Windows 电脑之间以及不同目录布局之间的迁移；当前安装脚本、内置二进制和剪映后端仍以 Windows x64 为运行边界。

## 快速开始

### 1. 安装

在 Windows PowerShell 中运行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
& ".\install.ps1"
```

安装程序会检查 Windows x64、Python 3.12 和内置 FFmpeg，在仓库下创建 `.venv`，从 `vendor/wheels` 离线安装固定版本依赖，并将本项目 Skill 链接到当前 Codex Home。仓库可位于任意固定目录，完整说明见 [安装文档](docs/INSTALL.md)。

### 2. 建立素材索引

```powershell
$FootagePath = Read-Host "请输入素材目录"
& ".\run.ps1" $FootagePath
```

默认输出到素材目录下的 `edit\footage_index`。如果希望素材与项目产物分开存放，可显式指定输出位置：

```powershell
$FootagePath = Read-Host "请输入素材目录"
$ProjectPath = Read-Host "请输入项目工作目录"
$IndexPath = Join-Path $ProjectPath "edit\footage_index"
& ".\run.ps1" $FootagePath --output-dir $IndexPath
```

建议按以下顺序读取索引：

1. `CODEX_INDEX.md`
2. `manifest.json` 或 `shots.csv`
3. 当前候选镜头的 0.3 秒胶片条
4. 仅对存疑区间读取 0.2 秒或逐帧结果

### 3. 在 Codex 中调用

```text
使用 $cinematic-edit-workflow 剪辑这个项目。素材目录是 <素材目录>，项目工作目录是 <项目目录>，参考剧本是 <剧本路径>。
```

Skill 会根据素材类型选择剧情或混剪路径，并把后续判断写回项目目录。详细执行规范位于 [SKILL.md](SKILL.md)。

## 两种时间线执行方式

### 通用本地流程

适合自动化装配、预览输出和独立质量检查。FFmpeg 负责素材索引、代理生成、技术检测及成片 QC；剪辑决定始终来自审核记录和源时间码 EDL，而不是场景检测结果本身。

### 剪映专业版 11.5 流程

当用户明确要求使用剪映时，前半段审片与选材逻辑保持不变，剪映成为唯一的时间线精修和最终导出端。当前验证环境：

```text
剪映专业版 11.5.0.14471
jianying-agent-cli 0.1.0
```

先在目标剪映工程中导入原始素材并取得真实的 project、draft、revision 与 material id，再生成装配计划：

```powershell
$ProjectPath = Read-Host "请输入项目工作目录"
$EditPath = Join-Path $ProjectPath "edit"
& ".\scripts\run_jianying_patch.ps1" `
  -Edl (Join-Path $EditPath "edl.json") `
  -MaterialMap (Join-Path $EditPath "jianying\material_map.json") `
  -Output (Join-Path $EditPath "jianying\patches\02_assembly.json") `
  -ProjectId "真实项目ID" `
  -DraftRef "真实草稿Ref" `
  -BaseRevision 0
```

这一后端采用保守边界：编译器只使用已验证的 `add_track` 与 `add_clip` 操作；包装脚本负责定位已安装的 Agent 并执行非写入式 `validate-patch`。它**不会**直接修改加密草稿、自动应用补丁、绕过宿主授权或替用户确认 PC 操作。版本不匹配时应停止并重新验证接口。

完整步骤、限制与故障处理见 [剪映工作流](references/jianying.md)。

## 主要产物

一次完整项目通常会留下：

- `footage_index/`：素材清单、镜头边界、代理片段和胶片条；
- 审核记录：可用区间、排除原因、表演与连续性判断；
- 剪辑方案：叙事目标、节奏曲线、音乐结构和覆盖策略；
- 源时间码 EDL：可复核、可重建的时间线决策；
- `jianying/`：素材映射、补丁计划、验证结果和草稿归档（剪映模式）；
- QC 报告：黑帧、静音、响度、画面边界、字幕和交付检查结果；
- 项目记忆：已经确认的偏好、问题和后续迭代依据。

## 文档导航

- [安装与离线部署](docs/INSTALL.md)
- [系统架构](docs/ARCHITECTURE.md)
- [审片与索引规范](references/review-and-index.md)
- [表演优先选材](references/performance-first-selection.md)
- [剧情连续性剪辑](references/narrative.md)
- [音乐混剪](references/montage.md)
- [制作、混音与交付](references/production.md)
- [数据结构与 EDL](references/schemas.md)
- [剪映专业版工作流](references/jianying.md)

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
│   ├── jianying_patch_compiler.py
│   ├── run_jianying_patch.ps1
│   └── bin/ffmpeg.exe
├── tests/
└── vendor/wheels/
```

## 当前状态

- 版本：`1.3.0`
- 平台：Windows x64
- 默认运行时：Python 3.12
- 剪映后端：针对 11.5.0.14471 验证，其他版本需重新做接口探测与安全验证
- 原始 1.2.0 版本已保存在 Git tag `backup-pre-jianying-20260928`

本项目仍处于快速迭代阶段。执行实际工程写入前，请保留源素材和编辑工程的独立备份，并以预览成片和 QC 结果作为最终验收依据。
