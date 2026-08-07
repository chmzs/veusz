# Contributing to Veusz (Fork)

感谢你参与本分支的开发！请遵循以下流程，确保代码质量和协作效率。

## 1. 环境准备

```bash
# 克隆仓库
git clone <your-fork-url>
cd veusz

# 安装 Pixi（如未安装）
curl -fsSL https://pixi.sh/install.sh | bash

# 安装依赖
pixi install
```

## 2. 开发工作流

### 2.1 分支策略
- **`dev`**：主开发分支，所有 PR 目标分支。
- **`master`**：稳定版本，仅由维护者从 `dev` 合并。
- 功能开发：从 `dev` 切出 `feature/<name>` 分支。

### 2.2 提交前检查
```bash
pixi run format      # 自动格式化（ruff format）
pixi run lint        # 静态检查（ruff check）
pixi run typecheck   # 类型检查（mypy）
pixi run test        # 单元测试（pytest）
```

> 若 `mypy` 报错复杂，可在 PR 中说明，但至少确保新增代码有类型注解。

### 2.3 PR 要求
- **标题**：符合提交信息规范（见下文）。
- **描述**：说明改动目的、影响范围、测试情况。
- **截图**：涉及 UI 变更时，必须附带 Before / After 截图。
- **关联 Issue**：使用 `Closes #<issue-number>` 自动关联。

### 2.4 提交信息规范
格式：`<type>(<scope>): <subject>`

| type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 错误修复 |
| `docs` | 文档更新 |
| `refactor` | 代码重构（不改变功能） |
| `test` | 测试相关 |
| `chore` | 构建/工具链变更 |

示例：
- `feat(gradient): add gradientCenterValue support for diverging colormaps`
- `fix(widget): prevent donut line from origin in XYPie`

## 3. 代码风格

- **格式化工具**：`ruff format`（与 Black 兼容）
- **Lint 工具**：`ruff check`，规则集见 `pyproject.toml`
- **类型注解**：新代码必须包含完整类型注解（`mypy` 严格模式）
- **命名约定**：
  - 类名：`PascalCase`
  - 函数/变量：`snake_case`
  - 常量：`UPPER_SNAKE_CASE`
  - Qt 信号/槽：`camelCase`（与 Qt 保持一致）

## 4. 测试规范

- **单元测试**：放在 `tests/selftests/`，文件名以 `test_` 开头。
- **自测试**：`tests/runselftest.py` 用于回归测试（比对 SVG 输出），需在本地 GUI 环境运行。
- **新增功能**：必须附带至少一个单元测试。
- **修复 Bug**：优先添加回归测试，防止再次出现。

## 5. 构建与发布（详见 RELEASE.md）

- **本地调试构建**：不签名，直接 `python -m PyInstaller ...`。
- **CI 发布构建**：自动签名（如已配置 Secrets），否则跳过签名但不报错。

## 6. 行为准则

- 尊重他人劳动，友好讨论。
- 重大改动（如重构核心数据结构）请在 `dev-docs/plans/` 中先提交设计文档。
- 未讨论过的破坏性变更（Breaking Changes）不予合并。


# Release Guide

本文档说明如何从源码构建可分发的 Veusz 安装包，并（可选）进行数字签名。

## 1. 版本号管理

- 版本号存储在仓库根目录的 `VERSION` 文件中。
- 发布前由维护者手动更新，格式：`<major>.<minor>.<patch>-fork`。
- 更新后需提交并打 tag：`git tag -a v<version> -m "Release v<version>"`

## 2. 构建类型

| 类型 | 用途 | 签名 | CI 触发 |
|------|------|------|---------|
| Debug | 本地开发测试 | 否 | 手动 |
| Release | 发布给用户 | 是（如已配置） | GitHub Actions（推送到 `master` 或手动触发） |

## 3. Windows 构建步骤

### 3.1 本地 Debug 构建（不签名）
```bash
# 1. 编译 C++ 扩展
python setup.py build_ext --inplace

# 2. 运行测试（可选）
pixi run test

# 3. PyInstaller 打包
pixi run python -m PyInstaller support/veusz_windows_pyinst.spec \
  --distpath support/dist --workpath support/build
```
> 输出位置：`support/dist/veusz_main/` 目录，可直接运行 `veusz.exe`。

### 3.2 CI Release 构建（含签名）
GitHub Actions 工作流 `.github/workflows/build-binary-windows.yml` 会在以下条件自动触发：
- 推送到 `master` 分支
- 手动触发（`workflow_dispatch`）

**签名流程**：
- 若 `SIGNTOOL_PFX` 和 `SIGNTOOL_PWD` 已配置，则自动调用 `signtool` 签名。
- 若未配置，**跳过签名步骤**（不影响安装包生成），并输出警告日志。

**跳过签名的实现示例**（在 workflow 中添加条件）：
```yaml
- name: Sign executable (Windows)
  if: env.SIGNTOOL_PFX != ''  # 仅当 Secret 存在时执行
  run: signtool sign /fd sha256 /a ...
```

### 3.3 NSIS 安装程序（可选）
```bash
cd support
python veusz_windows_make_nsi.py veusz_windows_setup.nsi
makensis veusz_windows_setup.nsi
# 输出：support/installer_out/veusz-<VER>-windows-x64-setup.exe
```

## 4. macOS 构建

```bash
# 使用 PyInstaller spec
pixi run python -m PyInstaller support/veusz_mac_pyinst.spec \
  --distpath support/dist --workpath support/build
```

**公证（Notarization）**：
- 需要配置 `APPLE_ID`、`TEAM_ID`、`APP_PWD` 三个 Secrets。
- 若未配置，跳过公证步骤，生成的 `.dmg` 仍可使用（但用户需要手动允许运行）。

## 5. Linux 构建（AppImage）

```bash
pixi run python -m PyInstaller support/veusz_linux_pyinst.spec \
  --distpath support/dist --workpath support/build
```
> 输出一个可执行的 AppImage 文件，无需签名。

## 6. 发布产物

| 平台 | 产物路径 | 备注 |
|------|----------|------|
| Windows | `support/dist/veusz_main/` 或 `support/installer_out/*.exe` | 含/不含签名均可 |
| macOS | `support/dist/veusz_main.app` 或 `.dmg` | 公证非必需 |
| Linux | `support/dist/veusz_main.AppImage` | 开箱即用 |

## 7. 常见发布问题

| 问题 | 解决方案 |
|------|----------|
| PyInstaller 找不到 `helpers/*.pyd` | 先执行 `python setup.py build_ext --inplace` |
| NSIS 构建失败 | 安装 NSIS 3.x，确保 `makensis` 在 PATH 中 |
| macOS 公证超时 | 检查网络和 Apple 账号状态，或跳过公证直接分发 |
| GitHub Actions 签名步骤失败 | 检查 Secret 是否过期或 Base64 格式错误，若无关可临时禁用签名步骤 |


