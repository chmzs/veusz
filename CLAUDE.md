# Veusz Project - Claude Code Instructions

## 🚨 硬约束（MUST / MUST NOT）

### 代码修改
- **修改设置项**：必须在 `veusz/setting/setting.py` 中同步更新 `__slots__`，否则序列化会静默失败。
- **添加新 C++ 扩展**：必须手动执行 `python setup.py build_ext --inplace` 并在本地验证，否则 PyInstaller 打包会因缺少 `.pyd` 而失败。
- **禁止裸 `except:`**：必须捕获具体异常类型（如 `ValueError`, `KeyError`）。仅顶层主循环允许 `except Exception` 并记录日志。
- **修改 `gradient.py` 时**：必须同时更新 `PRESETS` 字典和 `GradientConfig` 的 `__init__` 默认值，保持一致性。
- **禁止硬编码颜色值**：必须使用 `QColor` 或 `utils.misc.colorFromName`，支持用户主题切换。

### 提交前
- **必须运行**：`pixi run lint` 和 `pixi run format`（由 `ruff` 驱动）。
- **必须通过**：`pixi run test`（单元测试）。
- **推荐通过**：`VEUSZ_INPLACE_TEST=1 pixi run python tests/runselftest.py`（若因 Qt 剪贴板失败可忽略，不影响核心功能）。

### 测试豁免（已知可忽略错误）
- `test_gradient_fill.py` 在 `runselftest.py` 全量运行时可能因 `QGuiApplication` 剪贴板环境失败 → **不阻塞 PR**，单独用 `pytest` 运行即可。
- 任何依赖外部网络或 GUI 交互的测试，在 CI 中自动跳过（设置 `QT_QPA_PLATFORM=offscreen`）。

## 🏗️ 架构原则（新增代码必须遵守）

1. **梯度系统**（`utils/gradient.py`）
   - `GradientConfig` 为不可变数据类（使用 `dataclass(frozen=True)`）。
   - 新增预设色图时，同时支持 `matplotlib` 名称和 `ColorBrewer` 名称。
   - 透明度合成公式：`alpha_eff = (1 - brush_alpha) * (1 - gradient_alpha)`，在 `extbrushfilling.py` 中统一实现。

2. **轴统一颜色**（进行中，由独立 agent 实现）
   - 在 Axis 面板加 `color` 设置，默认 `auto`；指定颜色时统一覆盖轴线、刻度、刻度标签、轴标签。
   - 取代早期 `@axis:x:Line/color` 的 Color 轴引用机制（该机制已回滚，勿再引入）。

3. **新增绘图部件**
   - 必须继承 `widgets/widgetbase.py` 中的 `Widget` 或 `XYWidget`。
   - 必须在 `widgets/__init__.py` 中注册，否则无法在 UI 中显示。
   - 图例支持：必须实现 `getLegendSymbols()` 方法。

4. **持久化（Save/Load）**
   - 任何新增属性必须在 `setting/setting.py` 中定义 `Setting` 子类。
   - 确保旧版本文件加载时提供默认值（使用 `setting.setDefault`）。

## 📦 依赖与版本
- Python 3.13.12（由 `pixi.toml` 锁定，禁止手动升/降）
- Qt 6.10.2 / PyQt 6.11.0
- 新增依赖必须通过 `pixi add <package>` 添加，并提交 `pixi.lock`

## 🔧 常用命令（AI 可执行）
| 任务 | 命令 |
|------|------|
| 运行 Veusz | `pixi run veusz` |
| 运行单元测试 | `pixi run test` |
| 代码格式化 | `pixi run format`（`ruff format .`） |
| Lint 检查 | `pixi run lint`（`ruff check .`） |
| 类型检查 | `pixi run typecheck`（`mypy veusz/`） |
| 编译 C++ 扩展 | `python setup.py build_ext --inplace` |
| 构建 Windows 安装包 | `pixi run python -m PyInstaller support/veusz_windows_pyinst.spec --distpath support/dist --workpath support/build` |

## 🚫 禁止 AI 执行的操作
- **禁止**自动提交 `pixi.lock`（除非明确要求更新依赖）。
- **禁止**修改 `VERSION` 文件（由发布流程手动控制）。
- **禁止**在未询问用户的情况下删除或重命名公共 API 函数。
- **禁止**使用 `subprocess` 调用外部命令而不设置超时。

## 📝 提交信息规范
格式：`<type>(<scope>): <subject>`
- `type`：`feat` / `fix` / `docs` / `refactor` / `test` / `chore`
- `scope`：`gradient` / `widget` / `plugin` / `build` / `ci`
- 示例：`feat(gradient): add spectral preset with midpoint support`