# DaVinci Resolve 后端（Windows / macOS）

当用户明确选择达芬奇（DaVinci Resolve）作为时间线与交付端时阅读本文。审片、选材、EDL 逻辑与其他后端完全一致；Resolve 负责时间线精修、调色、混音和最终导出。FFmpeg 仍只用于索引和独立 QC。

## 为什么用交换文件而不是内部接口

Resolve 的时间线导入（File > Import > Timeline）是公开、跨平台、版本稳定的路径，Free 与 Studio 都可用，Windows 与 macOS 行为一致。Python 脚本 API 仅限 Studio，并且据报道自 21.1 起 Free 版已移除脚本支持，因此本后端**默认不依赖脚本 API**，由 `scripts/edl_export.py` 生成交换文件，用户在 Resolve 中手动导入。这与剪映后端“不绕过宿主授权”的边界一致，也不依赖任何未公开接口。

## 流程

1. 照常完成索引、审片、策略确认，写出源时间码 EDL（v2，见 `schemas.md`）。EDL 的 `timeline.frame_rate`、`width`、`height` 必须与计划交付规格一致。
2. 导出：

   ```bash
   # macOS / Linux
   .venv/bin/python scripts/edl_export.py <project>/edit/edl.json \
     --out-dir <project>/edit/davinci \
     --manifest <project>/edit/footage_index/manifest.json \
     --path-map "E:/footage=/Volumes/SSD/footage"
   ```

   ```powershell
   # Windows
   .\.venv\Scripts\python.exe scripts\edl_export.py "<project>\edit\edl.json" `
     --out-dir "<project>\edit\davinci" --manifest "<project>\edit\footage_index\manifest.json"
   ```

   - `--path-map` 可重复，用于跨系统（Windows 盘符 ↔ macOS `/Volumes/...`）重写素材路径前缀；源路径必须是绝对路径。
   - 默认同时输出 `*.fcpxml`（FCPXML 1.9，多轨，首选）和 `*.edl`（CMX3600，仅 V1，兜底）。
3. 在 Resolve 新建项目，**先设置时间线帧率与分辨率**（项目设置里的帧率在建立第一条时间线后不可改），再 File > Import > Timeline > 选择 `.fcpxml`；导入对话框中取消勾选“自动设置项目设置”以免覆盖交付规格。
4. 导入后做 **导入核对**（必做，成功导入不等于正确）：
   - 片段数、轨道数、总时长与导出命令输出一致；
   - 抽查首、中、尾和每个 V2 以上片段的源入点/出点是否等于 EDL（点开片段看源时间码）；
   - 没有红色“媒体离线”片段；离线则说明路径映射有误，修正 `--path-map` 重新导出，不要逐个手动重链接；
   - 带 `transform` / `continuity_compromise` 的片段在 FCPXML 中带有标记（marker）。镜像、重构图等**只是意图标记，不会自动应用**，需在 Resolve 中手动实施并按 `performance-first-selection.md` 复查。
5. 在 Resolve 中按阶段保存时间线副本（`10_SELECTS`…`70_FINAL`，同 `jianying.md`），手动改动要回写到 EDL 或 `project.md`。
6. 导出成片后运行 `scripts/qc.py`（见 `production.md`），并做视觉审片。

## 已知边界

- FCPXML 假定素材起始时间码为 0（AI 生成素材通常如此）。带内嵌起始 TC 的相机素材需在 Resolve 中核对或改用 `--format cmx3600`。
- 变速、转场、调色、字幕不进入交换文件，全部在 Resolve 内完成。
- 本导出器的 FCPXML 结构经过单元测试和 XML 良构检查，但**尚未在真实 Resolve 安装上做过导入验证**；首次使用请先用 3–5 个片段的 EDL 在一次性项目里试导入，确认源入出点、帧率和链接后再用于正式项目。
- Studio 用户如需自动导入，可使用 Resolve 官方脚本 API 的 `MediaPool.ImportTimelineFromFile`；论坛反馈通过 API 导入偶有片段显示未链接，需自行验证，不属于本后端的受支持路径。
