# 架构与数据流

```text
用户预筛选素材
    ↓
本地素材索引器
    ├─ PySceneDetect：候选镜头边界
    ├─ FFmpeg：镜头预览与定时抽帧
    └─ Pillow：带时间码分页胶片条
    ↓
CODEX_INDEX.md + manifest.json + shots.csv + HTML
    ↓
0.3秒完整审核 / 0.2秒重点复查 / 疑难区间逐帧
    ↓
material_review + usable_ranges + similarity_notes
    ↓
混剪模式：音乐图谱          剧情模式：剧本拆解、连续性图谱、选材矩阵
    ↓
剧情选材：表演/信息价值与瑕疵风险分离 → 覆盖与修复方案 → 项目专属策略确认
    ↓
源时间码 EDL
    ├─ 默认后端：预览 → 审片 → 精修 → 最终 QC
    ├─ 剪映后端：EDL v2 → 素材ID映射 → 分阶段补丁 → 剪映工程 → 剪映导出 → 独立 QC
    └─ 达芬奇后端：EDL v2 → edl_export.py → FCPXML/CMX3600 → 手动导入 Resolve → 导入核对 → 导出 → scripts/qc.py
```

## 边界

- 自动分镜只提供候选边界，不能取代视觉复核。
- 拆分镜头是浏览代理；最终 EDL回指原素材及源时间码。
- 素材未改变时复用缓存。
- 本项目不在运行时读取或调用 `video-use`。
- 外部工作流的改进必须走 `references/upstream-evaluation.md` 的评估流程。
- 剪映模式不直接写加密草稿；补丁必须匹配真实工程、素材ID和revision，并通过对应版本的Agent CLI验证。
- 剪映的宿主授权、运行令牌和PC确认属于不可绕过的应用边界。
- 达芬奇后端只使用公开的时间线交换格式，不调用 Resolve 脚本 API，因此 Free/Studio、Windows/macOS 行为一致。
- 素材身份由内容指纹和只增不改的 `source_registry.json` 决定，与路径、盘符和操作系统无关。
