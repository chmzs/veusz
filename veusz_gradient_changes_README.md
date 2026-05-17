# Veusz 渐变填充功能修改

## 概述

此 patch 为 Veusz 添加了多色渐变填充功能，支持：
- 线性渐变和径向渐变
- 自定义颜色停止点
- 预设渐变（Temperature, Elevation, Viridis 等）
- 自定义填充目标（zero, custom value）
- 独立的渐变模块，易于维护

## 修改的文件

### 已修改的文件
1. `veusz/setting/setting.py` - 新增 GradientFill 设置类型
2. `veusz/setting/controls.py` - 渐变编辑器 UI 控件
3. `veusz/setting/collections.py` - BrushExtended 支持渐变
4. `veusz/utils/extbrushfilling.py` - 渲染引擎支持渐变
5. `veusz/widgets/point.py` - XY 曲线支持 zero/custom 填充

### 新增的文件
1. `veusz/utils/gradient.py` - 独立的渐变模块
2. `tests/selftests/gradient_test.py` - 单元测试

## 应用方法

### 方法 1: 使用 patch 命令

```bash
# 应用修改文件的 patch
git apply /path/to/veusz_gradient_changes.patch

# 应用新文件的 patch
git apply /path/to/veusz_gradient_new_files.patch
```

### 方法 2: 手动复制文件

直接复制以下文件到你的 Veusz 源码目录：

- `veusz/setting/setting.py`
- `veusz/setting/controls.py`
- `veusz/setting/collections.py`
- `veusz/utils/extbrushfilling.py`
- `veusz/widgets/point.py`
- `veusz/utils/gradient.py` (新文件)
- `tests/selftests/gradient_test.py` (新文件)

## 预设渐变

| 名称 | 颜色 | 用途示例 |
|------|------|----------|
| temperature | 蓝-白-红 | 温度数据 |
| elevation | 绿-黄-红 | 海拔/高度 |
| grayscale | 黑-白 | 灰度数据 |
| viridis | 紫-绿-黄 | 科学可视化 |
| plasma | 紫-粉-黄 | 科学可视化 |
| inferno | 黑-红-黄 | 科学可视化 |

## 测试

```bash
python tests/selftests/gradient_test.py
```

## GitHub Actions 构建

修改推送到 fork 后，会自动触发构建 workflow。

## 功能详情

### 1. 渐变设置
- 启用/禁用渐变
- 渐变类型：线性/径向
- 线性渐变角度 (0-360°)
- 自定义颜色停止点

### 2. 填充目标
原有的 `Fill to` 选项新增：
- `zero` - 填充到 Y=0 值
- `custom` - 填充到自定义 Y 值

---
生成时间: 2026-05-17