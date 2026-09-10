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
混剪模式：音乐图谱          剧情模式：剧本拆解与连续性图谱
    ↓
项目专属策略确认
    ↓
源时间码 EDL → 预览 → 审片 → 精修 → 最终 QC
```

## 边界

- 自动分镜只提供候选边界，不能取代视觉复核。
- 拆分镜头是浏览代理；最终 EDL回指原素材及源时间码。
- 素材未改变时复用缓存。
- 本项目不在运行时读取或调用 `video-use`。
- 外部工作流的改进必须走 `references/upstream-evaluation.md` 的评估流程。
