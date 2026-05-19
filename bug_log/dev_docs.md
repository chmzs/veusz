# Veusz 开发成果文档

> 本文档记录 2025 年 Veusz 绘图软件的开发成果，包括新增功能、bug 修复和技术细节。

## 目录

1. [XY 图置信区间（CI）列选择](#1-xy-图置信区间ci-列选择)
2. [Bar 图置信区间（CI）列选择](#2-bar-图置信区间ci-列选择)
3. [Rectangle 显式边界模式](#3-rectangle-显式边界模式)
4. [渐变色填充功能](#4-渐变色填充功能)
5. [技术要点总结](#5-技术要点总结)

---

## 1. XY 图置信区间（CI）列选择

### 功能描述

为 XY 图（PointPlotter）添加置信区间（Confidence Interval）列选择功能，允许用户从数据集中指定 CI 的上下界，而不仅限于使用内置的 serr/nerr/perr 列。

### 新增设置项

| 设置名 | 类型 | 说明 |
|--------|------|------|
| `ciMode` | ChoiceSwitch | CI 模式：空（默认）、custom（自定义数据集）、std（标准差模式） |
| `ciXMin` | Str | X 轴 CI 下界数据集 |
| `ciXMax` | Str | X 轴 CI 上界数据集 |
| `ciYMin` | Str | Y 轴 CI 下界数据集 |
| `ciYMax` | Str | Y 轴 CI 上界数据集 |
| `ciXError` | Str | X 轴误差数据集（配合 multiplier 使用） |
| `ciYError` | Str | Y 轴误差数据集（配合 multiplier 使用） |
| `ciMultiplier` | Float | 误差乘数（如 2 表示 2 倍标准差），默认 1.0 |

### CI 模式说明

- **空模式（默认）**：使用数据集内置的 serr/nerr/perr 列
- **std 模式**：使用 ciXError/ciYError 数据，配合 multiplier 计算 CI 范围
- **custom 模式**：直接使用 ciXMin/ciXMax/ciYMin/ciYMax 数据集作为 CI 边界

### 关键代码

#### 显示函数（控制参数可见性）

```python
# veusz/widgets/point.py

def _ciModeShowfn(val):
    """Show/hide CI settings based on ciMode value."""
    if val == 'custom':
        return (('ciXMin', 'ciXMax', 'ciYMin', 'ciYMax'),
                ('ciXError', 'ciYError', 'ciMultiplier'))
    elif val == 'std':
        return (('ciXError', 'ciYError', 'ciMultiplier'),
                ('ciXMin', 'ciXMax', 'ciYMin', 'ciYMax'))
    else:
        return ((), ('ciXMin', 'ciXMax', 'ciYMin', 'ciYMax',
                    'ciXError', 'ciYError', 'ciMultiplier'))
```

#### ChoiceSwitch 设置定义

```python
s.add( setting.ChoiceSwitch(
    'ciMode',
    ['', 'custom', 'std'],
    '',
    showfn=_ciModeShowfn,
    descr=_('Confidence interval mode'),
    usertext=_('CI mode'),
    formatting=True) )
```

#### _plotErrors 方法中的 CI 处理逻辑

```python
# veusz/widgets/point.py - _plotErrors 方法（约 line 588-679）

# std 模式：data +/- error * multiplier
if ci_mode == 'std':
    if s.ciYError:
        error_data = ds.data.astype(float) * multiplier
        ymin = yvals - error_data
        ymax = yvals + error_data

# custom 模式：直接使用指定数据集
elif ci_mode == 'custom' or s.ciXMin or s.ciXMax or s.ciYMin or s.ciYMax:
    if s.ciXMin:
        xmin = ds.data.astype(float)
```

### 注意事项

1. **ChoiceSwitch 的 showfn 必须是模块级函数**，不能是类内 @staticmethod，否则会报错 "unexpected keyword argument 'showfn'"
2. **`formatting=True`** 确保设置在格式化面板可见
3. **空数组检查**：读取数据集时需检查 `len(ds.data) > 0`

---

## 2. Bar 图置信区间（CI）列选择

### 功能描述

为 Bar 图（BarPlotter）添加置信区间列选择功能，支持自定义 Y 轴 CI 边界。

### 新增设置项

| 设置名 | 类型 | 说明 |
|--------|------|------|
| `ciMode` | ChoiceSwitch | CI 模式：空、custom、std |
| `ciYMin` | Str | Y 轴 CI 下界数据集 |
| `ciYMax` | Str | Y 轴 CI 上界数据集 |
| `ciYError` | Str | Y 轴误差数据集 |
| `ciMultiplier` | Float | 误差乘数，默认 1.0 |

### 关键代码

#### 显示函数

```python
# veusz/widgets/bar.py

def _barCiModeShowfn(val):
    """Show/hide CI settings based on ciMode value."""
    if val == 'custom':
        return (('ciYMin', 'ciYMax'), ('ciYError', 'ciMultiplier'))
    elif val == 'std':
        return (('ciYError', 'ciMultiplier'), ('ciYMin', 'ciYMax'))
    else:
        return ((), ('ciYMin', 'ciYMax', 'ciYError', 'ciMultiplier'))
```

#### calculateErrorBars 方法增强

```python
# veusz/widgets/bar.py - calculateErrorBars 方法

def calculateErrorBars(self, dataset, vals, ciMode='', ciYMin='', ciYMax='',
                       ciYError='', ciMultiplier=1.0):
    """Get values for error bars."""
    if ciMode == 'std' and ciYError:
        err_ds = self.document.getData(ciYError)
        if err_ds is not None:
            s = N.nan_to_num(err_ds.data.astype(float)) * ciMultiplier
            minval = vals - s
            maxval = vals + s
            return minval, maxval

    elif ciMode == 'custom':
        if ciYMin:
            min_ds = self.document.getData(ciYMin)
            if min_ds is not None:
                minval = min_ds.data.astype(float)
        if ciYMax:
            max_ds = self.document.getData(ciYMax)
            if max_ds is not None:
                maxval = max_ds.data.astype(float)
        return minval, maxval

    # Default: use dataset's built-in error columns
    ...
```

#### drawErrorBars 调用更新

```python
minval, maxval = self.calculateErrorBars(
    dataset, yvals,
    ciMode=s.ciMode,
    ciYMin=s.ciYMin,
    ciYMax=s.ciYMax,
    ciYError=s.ciYError,
    ciMultiplier=s.ciMultiplier
)
```

---

## 3. Rectangle 显式边界模式

### 功能描述

为 Rectangle 添加两种定位模式：
- **center 模式（默认）**：使用 xPos/yPos（中心点）+ width/height
- **bounds 模式**：使用 xmin/xmax/ymin/ymax（直接指定边界）

### 新增设置项

| 设置名 | 类型 | 说明 |
|--------|------|------|
| `rectPosition` | ChoiceSwitch | 定位模式：center、bounds |
| `xmin` | DatasetExtended | 最小 X 值列表 |
| `xmax` | DatasetExtended | 最大 X 值列表 |
| `ymin` | DatasetExtended | 最小 Y 值列表 |
| `ymax` | DatasetExtended | 最大 Y 值列表 |

### ChoiceSwitch 定义

```python
# veusz/widgets/shape.py - Rectangle.addSettings

@staticmethod
def _rectPosShowfn(val):
    """Show/hide settings based on rectPosition value."""
    if val == 'bounds':
        return (('xmin', 'xmax', 'ymin', 'ymax'),
                ('xPos', 'yPos', 'width', 'height'))
    else:
        return (('xPos', 'yPos', 'width', 'height'),
                ('xmin', 'xmax', 'ymin', 'ymax'))

s.add( setting.ChoiceSwitch(
    'rectPosition',
    ['center', 'bounds'],
    'center',
    showfn=_rectPosShowfn,
    descr=_('Use center+size or explicit bounds to place rectangle'),
    usertext=_('Rectangle position'),
    formatting=False) )
```

### 坐标转换方法

```python
# veusz/widgets/shape.py - Rectangle 类

def _getBoundsCoords(self, posn, xsetting='xmin', ysetting='ymin',
                     x2setting='xmax', y2setting='ymax'):
    """Calculate bounds coordinates from axes or relative values."""
    if s.rectPosition == 'bounds':
        # 从轴坐标转换
        axes = self.parent.getAxes((s.xAxis, s.yAxis))
        xmin = axes[0].dataToPlotterCoords(posn, xmin)
        ymin = axes[1].dataToPlotterCoords(posn, ymin)
        xmax = axes[0].dataToPlotterCoords(posn, xmax)
        ymax = axes[1].dataToPlotterCoords(posn, ymax)
    else:
        # 从相对坐标转换
        xmin = posn[0] + (posn[2]-posn[0])*xmin

def _getBoundsFromGraph(self, posn, xmin_plt, xmax_plt, ymin_plt, ymax_plt):
    """Calculate data coordinates given plotter coordinates."""
    if s.rectPosition == 'bounds':
        # 从图坐标转换回数据坐标
        xmin = axes[0].plotterToDataCoords(posn, xmin_plt)
        ...
```

### 绘制逻辑

```python
def draw(self, posn, phelper, outerbounds=None):
    if s.rectPosition == 'bounds':
        # 使用显式边界绘制
        xmin, ymin, xmax, ymax = self._getBoundsCoords(posn)
        for i in range(len(xmin)):
            x1, y1 = xmin[i], ymin[i]
            x2, y2 = xmax[i], ymax[i]
            wp, hp = abs(x2 - x1), abs(y2 - y1)
            # ... 绘制矩形
    else:
        # 使用中心+尺寸模式（调用父类）
        BoxShape.draw(self, posn, phelper, outerbounds)
```

### 重要提示

1. **命名冲突**：FreePlotter 已有 `positioning` 设置，改用 `rectPosition` 避免冲突
2. **空数组检查**：bounds 模式下需检查 `len(xmin) == 0 or len(ymin) == 0 or len(xmax) == 0 or len(ymax) == 0`
3. **支持数据集**：xmin/xmax/ymin/ymax 支持 DatasetExtended，可传入数据集或表达式

---

## 4. 渐变色填充功能

### 功能描述

为 Fill 设置添加渐变色填充支持，支持线性渐变和径向渐变。

### 新增文件

- `veusz/utils/gradient.py` - 渐变工具模块
- 修改 `veusz/utils/extbrushfilling.py` - 集成渐变填充

### GradientConfig 类

```python
# veusz/utils/gradient.py

class GradientConfig:
    """Configuration for a gradient fill."""
    def __init__(self, enabled=False, grad_type='linear', angle=90,
                 stops=None, transparency=0):
        self.enabled = enabled
        self.type = grad_type  # 'linear' or 'radial'
        self.angle = angle      # 0-360 degrees
        self.stops = stops or [(0.0, '#ff0000'), (1.0, '#0000ff')]
        self.transparency = transparency  # 0-100
```

### 预设渐变

```python
PRESETS = {
    'temperature': {
        'name': 'Temperature (Blue-White-Red)',
        'stops': [(0.0, '#0066ff'), (0.5, '#ffffff'), (1.0, '#ff3300')]
    },
    'elevation': {
        'name': 'Elevation (Green-Yellow-Red)',
        'stops': [(0.0, '#00aa00'), (0.5, '#ffff00'), (1.0, '#ff0000')]
    },
    'viridis': {...},
    'plasma': {...},
    'inferno': {...},
    # ... 更多预设
}
```

### 渐变渲染

```python
# veusz/utils/extbrushfilling.py

def _brushExtFillPathGradient(painter, extbrush, path, stroke=None, dataindex=0):
    """Fill a path with a gradient brush."""
    gradient_setting = extbrush.get('Gradient')
    config = gradient_module.get_gradient_config(gradient_setting)
    if not config.enabled:
        return

    bb = path.boundingRect()
    qt_gradient = gradient_module.create_gradient_from_config(config, bb)
    brush = qt.QBrush(qt_gradient)

    if stroke is None:
        painter.fillPath(path, brush)
    else:
        painter.save()
        painter.setPen(stroke)
        painter.setBrush(brush)
        painter.drawPath(path)
        painter.restore()
```

### 渐变设置集成

在 `FillSet.normalize()` 中扩展支持 `len(fill) == 3 or len(fill) == 10` 的情况：
- 3 元素：`('solid', 'auto', False)` - 默认实色填充
- 10 元素：完整渐变配置 `('gradient', 'auto', False, enabled, type, angle, stops, transparency, ...)`

---

## 5. 技术要点总结

### 5.1 ChoiceSwitch 最佳实践

```python
# ✅ 正确：模块级函数
def _ciModeShowfn(val):
    ...

class PointPlotter:
    s.add(setting.ChoiceSwitch('ciMode', ['', 'custom', 'std'], '',
                              showfn=_ciModeShowfn, ...))

# ❌ 错误：类内 @staticmethod
class PointPlotter:
    @staticmethod
    def _ciModeShowfn(val):
        ...
```

### 5.2 DatasetExtended vs Str

| 类型 | 用途 | 说明 |
|------|------|------|
| `DatasetExtended` | 需要表达式支持 | 可输入数据集名或计算表达式 |
| `Str` | 简单字符串 | 仅存储数据集名称 |

### 5.3 坐标转换流程

```
数据坐标 → dataToPlotterCoords → 绘图坐标
绘图坐标 → plotterToDataCoords → 数据坐标
```

### 5.4 FieldFloat/FieldBool 参数注意

```python
# ✅ 正确：不含 description 参数
field.FieldFloat('span', _('Span'), default=0.3, minval=0.01, maxval=1.0)

# ❌ 错误：不含 description
field.FieldFloat('span', _('Span'), default=0.3, minval=0.01, maxval=1.0,
                descr=_('Description'))  # 报错
```

### 5.5 缓存清除

修改 Python 源文件后，删除 `__pycache__/` 中的 `.pyc` 文件以确保新代码生效：
```bash
rm veusz/plugins/__pycache__/*.pyc
```

---

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `veusz/widgets/point.py` | 修改 | 添加 CI 列选择功能（约 +150 行） |
| `veusz/widgets/bar.py` | 修改 | 添加 CI 列选择功能（约 +50 行） |
| `veusz/widgets/shape.py` | 新增 | Rectangle bounds 模式（约 +220 行） |
| `veusz/utils/gradient.py` | 新增 | 渐变工具模块（约 +320 行） |
| `veusz/utils/extbrushfilling.py` | 修改 | 集成渐变填充 |
| `veusz/setting/setting.py` | 修改 | FillSet.normalize() 扩展 |
| `veusz/plugins/__init__.py` | 临时修改 | LOESS 插件（已移除） |

---

## 版本信息

- **Veusz 版本**: 4.2.1
- **开发日期**: 2025
- **Python 环境**: pixi (conda-forge)
- **主要依赖**: PyQt6, numpy, scipy, astropy

---

*文档生成时间: 2025*