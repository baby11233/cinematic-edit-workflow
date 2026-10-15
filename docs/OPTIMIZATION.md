# 1.4.0 优化记录

## 已实现

| 项 | 问题 | 处理 |
|---|---|---|
| 源编号不稳定 | `SRC0001…` 按文件排序号分配；新增素材会让后面所有编号后移，而缓存又按路径命中、读取 `SRC{序号}/shots.json`，会把**另一个文件的镜头数据**当作缓存读出，且已有 EDL 会静默指向错误素材 | 新增 `source_registry.json`（指纹 → SRC 号，只增不改）；缓存键改为 SRC 号 |
| 指纹绑定路径与 mtime | 换盘符、拷到 Mac、拷贝后 mtime 变化都会使缓存失效 | 指纹 = 大小 + 头尾各 1 MB，与路径无关；命中缓存时仅刷新源路径 |
| 输出内含绝对路径 | 移动项目目录后 HTML/CSV 里的预览路径全部失效 | `shots.json` 里的片段/胶片条路径改为相对索引目录 |
| 仅限 Windows | 字体、`.exe` 查找、PowerShell 脚本 | 增加 macOS/Linux 字体回退、Homebrew 路径查找、`install.sh/run.sh/verify.sh` |
| 浏览片段编码慢 | 每个镜头都 `libx264 -crf 18` 重编码 | `--encoder auto` 优先 VideoToolbox（macOS）/NVENC/QSV（Windows），回退 libx264 |
| 缺 ffprobe | 仓库只带 `ffmpeg.exe`，QC 与探测都需要回退 | 索引器和 QC 在无 ffprobe 时解析 `ffmpeg -i` |
| QC 只有文字清单 | `production.md` 列了检查项但没有可执行工具 | 新增 `scripts/qc.py`：解码错误、黑场、冻结、静音、响度/真峰值、尺寸/帧率断言，输出 `*.qc.json` |
| 只有剪映一个后端 | 剪映后端依赖未公开的 Agent CLI，仅 Windows 且版本锁定 | 新增达芬奇后端：`edl_export.py` → FCPXML 1.9 / CMX3600，跨平台、无私有接口 |
| 补丁编译器的记录位置 | 未写 `record_in` 时用**全局**游标，一个 V2 叠加片段会把后续 V1 片段整体后推 | 改为每条轨道独立游标（编译器与导出器一致） |

## 建议但未实现（需要你决定）

1. **自适应审片密度**：现行规则“每张胶片条都按 ≤0.3 秒逐段读完”对长素材的 token 成本很高（10 分钟素材约 2000 帧 ≈ 100 页）。可选方案：先对相邻帧做感知哈希差分，静态段合并为 0.6–1 秒一格，运动/表情段保持 0.2–0.3 秒。这改变了现有硬性门槛，所以只作建议。
2. **本地转写**：`production.md` 要求用“已验证的词边界”剪对白，但仓库没有任何转写工具。建议加入可选的本地 ASR（macOS 用 whisper.cpp + Metal，Windows 用 faster-whisper），输出词级时间戳到 `edit/transcripts/`。
3. **EDL v3**：以帧为单位（整数帧 + 有理数帧率）取代浮点秒，避免 23.976/29.97 下的取整漂移；`edl_export.py` 已按时间线帧网格取整，v3 可让这一步变成显式记录。
4. **Resolve Studio 自动导入**：可在 `davinci.md` 流程之上增加脚本，但 Free 版已无脚本 API，且 API 导入有链接问题的反馈，需要真机验证后再加。
5. **仓库瘦身**：145 MB 的 LFS 二进制（ffmpeg.exe + Windows wheels）可改为“下载脚本 + 校验和”，或移到 GitHub Release。
