Windows 桌面番茄钟 — 技术架构设计

一、技术选型与总体架构
- 技术栈：Python 3.11 + PySide6（Qt 6）用于桌面 GUI；内建 QPainter/QPixmap 渲染；QFontDatabase 加载 TTF 字体。
- 架构模式：模块化设计（计时服务、渲染器、皮肤加载、配置服务、主窗口）。UI 与业务逻辑分离，便于测试与扩展。
- 窗口属性：置顶 `Qt.WindowStaysOnTopHint`；无边框 `Qt.FramelessWindowHint`；固定大小 256×256；启用透明背景 `Qt.WA_TranslucentBackground`；鼠标穿透可选（后续版本）。

二、目录结构（建议）
- `src/`
  - `app.py`: 程序入口，初始化配置、服务与主窗口
  - `services/timer_service.py`: 番茄计时状态机与倒计时逻辑
  - `services/config_service.py`: 读取/写入 `config.json`
  - `services/audio_service.py`: 阶段结束提示音播放
  - `skin/loader.py`: 皮肤目录解析与帧加载（`QPixmap` 列表）
  - `render/renderer.py`: 文本与帧合成到画布（`QPixmap`）
  - `ui/main_window.py`: 置顶窗口，展示合成结果，处理交互
- `assets/fonts/Minecraftia-Regular.ttf`: 指定字体
- `skins/<skin_id>/skin.png` 或 `skin_000.png`…：皮肤素材
- `config.json`: 配置文件
- `docs/`: 项目文档（PRD、技术设计）

三、核心模块设计
- TimerService（计时服务）
  - 状态：`WORK`、`SHORT_BREAK`、`LONG_BREAK`、`PAUSED`
  - 接口：`start()`、`pause()`、`reset()`、`skip()`、`tick()`（每秒触发）
  - 事件：`on_tick(mm, ss)`、`on_phase_changed(phase)`、`on_completed()`
  - 逻辑：默认 25/5/15；每 4 次工作进入长休；可配置。
- ConfigService（配置服务）
  - 读取/写入 `config.json`；提供默认值与校验（范围、类型）。
  - 关键键：`workMinutes`、`shortBreakMinutes`、`longBreakMinutes`、`sessionsBeforeLongBreak`、`skinId`、`frameRate`、`alwaysOnTop`、`soundEnabled`（结束提醒开关）、`language`。
  - 校验规则：`workMinutes` 与 `shortBreakMinutes` 统一强制转换为整数，范围限制 0–99，非法值回退并持久化。
- SkinLoader（皮肤加载器）
  - 识别序列：按文件名排序读取 `skin_###.png`；否则读取单帧 `skin.png`。
- 校验尺寸：所有帧必须为 256×256；否则抛出受控异常并降级。
  - 输出：`List[QPixmap]` 与 `is_animated` 标记。
- Renderer（渲染器）
  - 目标：合成皮肤帧与文本；保证像素风清晰与坐标精确。
  - 字体：使用 `QFontDatabase.addApplicationFont()` 加载 `Minecraftia-Regular.ttf`；字号固定 24；等宽设置。
  - 文本绘制：以中心点 `(63, 88)` 居中绘制（字号 16）；使用 `QFontMetrics` 计算文本宽高并构造矩形，使中心点对齐；无固定高度限制。
  - 清晰度：关闭 `TextAntialiasing`；启用整像素对齐；禁用子像素渲染。
  - 帧率：动画播放默认 8 FPS；以系统计时驱动渲染。
- MainWindow（主窗口）
  - 置顶与无边框与透明背景；固定大小；通过 `QLabel`/`QWidget` 绘制当前帧。
  - 订阅 `TimerService` 事件；更新显示文本与阶段切换反馈。
  - 提供基础交互（开始/暂停/重置/跳过）与皮肤切换入口。
- AudioService（音频服务）
  - 播放 WAV/MP3 提示音；音量与开关由配置控制。

四、渲染与坐标细节
- 画布：`QPixmap(256, 256)`；背景为皮肤帧。
- 文本：格式为两位数 `xx:xx`（前导零），例如 `05:00`。
 - 坐标：计时文本左上角 `(53, 140)`；字号 36；对齐模式 `AlignLeft|AlignTop`；确保不同数字宽度一致（使用等宽像素字体）。
- 颜色：默认纯白；根据皮肤可支持阴影或描边（后续版本）。
 - 结束闪烁：在“开启结束提醒”开启时，计时完成后文本停在 `00:00` 并进行红/白交替闪烁 3 次（约 6 次切换，150ms 周期）。
 
五、叠加按钮与交互命中区域
- 图标资源：`assets/icons/start.png`、`assets/icons/pause.png`、`assets/icons/setting.png`、`assets/icons/reset.png`（均为 24×24）。
- 坐标与尺寸：
  - 开始/暂停按钮命中区域：左上角 `(132, 210)`，宽高 `24×24`。
  - 设置按钮命中区域：左上角 `(164, 210)`，宽高 `24×24`。
  - 重新开始按钮命中区域：左上角 `(196, 210)`，宽高 `24×24`。
- 绘制：在合成画布上叠加相应 PNG 图层；透明背景。
- 事件处理：
  - 在 `MainWindow` 的鼠标点击事件中进行命中测试（基于窗口坐标与固定大小）。
  - 点击开始：切换计时状态为运行，图标从 `start.png` 变为 `pause.png`。
  - 点击暂停：切换计时状态为暂停，图标从 `pause.png` 变为 `start.png`。
  - 点击设置：打开设置对话框（见下文）；打开设置时主窗口计时暂停，并弹出新窗口用于调整设置。
  - 点击重新开始：无论当前处于 `WORK`/`SHORT_BREAK`/`LONG_BREAK`，均停止计时并切换到 `WORK` 阶段，重置到初始值（显示如 `25:00`），不自动开始。
  - 无边框移动：非按钮区域按下左键记录拖拽偏移（`globalPosition - topLeft`）；在移动事件中调用 `move(newPos - offset)`；鼠标释放时结束拖拽。
  - 无边框移动：非按钮区域按下左键记录拖拽偏移（`globalPosition - topLeft`）；在移动事件中调用 `move(newPos - offset)`；鼠标释放时结束拖拽。

六、系统托盘集成
- 使用 `QSystemTrayIcon` 加载托盘图标 `assets/tray/tray.ico`；提供右键菜单。
- 菜单项：
  - 设置：打开设置对话框，修改专注时间（`workMinutes`）、休息时间（`shortBreakMinutes`）与结束提醒开关（`soundEnabled`）。
  - 开始/暂停、重置、退出。
  - 调整缩放倍率：通过 `QInputDialog.getDouble` 输入数值（范围 0.5–3.0，小数支持），更新 `uiScale` 并即时重设窗口尺寸与命中区域（所有命中区域按物理尺寸 `逻辑×uiScale` 计算）。
- 同步策略：托盘菜单与主界面按钮操作保持一致的状态与反馈。
 - 行为一致性：从托盘打开设置时同样暂停主窗口计时并弹出设置窗口。

七、时间与状态机
- 每秒触发 `tick`：`ss = (ss - 1)`；借位到分钟；到达 0:00 触发阶段完成。
- 阶段流转：工作→短休（循环）；每满 `sessionsBeforeLongBreak` 次工作进入长休。
- 交互：`pause` 冻结倒计时；`reset` 返回当前阶段初始值；`skip` 直接进入下阶段。
 - 手动进行休息：当配置 `manualBreak` 开启且处于 `WORK` 阶段结束时，不自动切换到休息；停留在 `00:00` 并暂停计时，记录下一阶段为 `SHORT_BREAK` 或 `LONG_BREAK`（按规则计算），用户再次点击开始后再进入休息阶段。

八、设置对话框
- 结构：三个字段——专注时间（分钟，映射 `workMinutes`）、休息时间（分钟，映射 `shortBreakMinutes`）、结束提醒（布尔，映射 `soundEnabled`）。
- 校验：取值范围（1–180）；实时预览；保存后写入配置并应用到 `TimerService`。

九、配置格式示例（`config.json`）
```json
{
  "workMinutes": 25,
  "shortBreakMinutes": 5,
  "longBreakMinutes": 15,
  "sessionsBeforeLongBreak": 4,
  "skinId": "default",
  "frameRate": 8,
  "alwaysOnTop": true,
  "soundEnabled": true,
  "language": "zh-CN"
}
```

十、错误处理与降级
- 缺失字体：提示并降级到系统等宽字体；建议用户补齐 `Minecraftia-Regular.ttf`。
- 皮肤尺寸非法：拒绝加载并提示；回退到内置默认皮肤。
- 序列缺帧：按可读帧播放；告警记录日志。

十一、日志与可观测性
- 级别：INFO/ERROR；记录阶段切换、资源加载失败、配置变更。
- 位置：`logs/app.log`（最多 1MB 轮转）。

十二、测试计划
- 单元测试：时间格式化（前导零）、状态机流转、配置读写与校验、皮肤尺寸校验。
- 集成测试：窗口置顶、序列播放帧率、文本坐标与清晰度检查；按钮命中区域正确、图标切换与状态同步；托盘菜单项生效。
- 验收清单：见 PRD 验收标准。

十三、打包与发布
- 打包：使用 PyInstaller 生成单文件或单目录 `.exe`，包含字体与默认皮肤。
- 运行环境：无外部依赖；首次启动创建默认 `config.json` 与 `logs/`。
- 版本化：语义化版本号；变更日志记录新增/修复项。

十四、风险与对策
- 字体许可：Minecraftia 为免费字体，需遵循许可说明；发布时附带许可文件。
- DPI 与缩放：初版不考虑缩放；如用户缩放≠100%，可能出现视觉偏差，可在后续版本引入缩放感知与坐标换算。
- 资源体积：序列帧过多导致启动慢与内存占用升高；建议限制帧数与按需加载。
