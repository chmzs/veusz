# Veusz Fork 功能开发计划与设计文档

- **文档状态**：活跃（每批次完成后更新"批次状态表"）
- **基线**：`upstream/master`（veusz/veusz）+ 本 fork `dev` 分支
- **版本**：v4.2.1.1
- **最近更新**：2026-08-05

> 本文档是 fork 功能开发的可执行蓝图，用于交接工作与持续开发。
> 每批次：目标 → 改动文件 → 测试 → 验收 → 状态更新。

---

## 一、背景与目标

本 fork 在 Veusz（PyQt6 科学绘图，Jeremy Sanders 原版）之上新增了 5 大功能。
当前状态：**功能可用但集成不完整**——渐变填充是"附加式"接进来的，导致：

- 透明度机制分裂：实色/阴影填充尊重 brush 透明度，渐变填充忽略
- 每数据集渐变走不通（bar 等 FillSet 系）
- 点图填充逻辑重复且 fallback 不一致
- Rectangle bounds 模式有长度崩溃与无交互问题

**已确认的优先级决策：**
1. 先修"乱"（透明度、渐变集成、bug），再增新功能
2. bar 图**不新增绝对宽度**（保持 barfill/groupfill 比例模式）
3. 渐变填充**全量扩展**到非 BrushExtended 的 fill（箭头、箱线图标记、3D 等）

---

## 二、现有功能清单（相对 upstream/master）

| # | 功能 | 文件 | 说明 |
|---|------|------|------|
| F1 | CI 列选择（XY 图） | `veusz/widgets/point.py` | `ciMode` 三态：空/custom/std；custom 用 `ciXMin/ciXMax/ciYMin/ciYMax` 数据集，std 用 `ciXError/ciYError/ciMultiplier` |
| F2 | CI 列选择（Bar 图） | `veusz/widgets/bar.py` | 同上，仅 Y 方向 |
| F3 | Rectangle 显式边界模式 | `veusz/widgets/shape.py` | `rectPosition`：center/bounds；bounds 用 `xmin/xmax/ymin/ymax` 数据集 + 轴坐标转换 |
| F4 | 渐变填充 | 新 `gradient.py` + 改 `extbrushfilling.py`/`collections.py`/`setting.py`/`controls.py` | 线性/径向、预设、色标编辑器、预览 |
| F5 | fillto/filltoValue | `function.py`/`point.py` | 函数图/点图填充到指定边：auto/top/bottom/left/right/custom |
| F6 | fillto 默认值修复 | `collections.py` | `PlotterFill` 默认 `'auto'`、`PointFill` 默认 `'top'`（已提交） |

### 关键架构位置

```
veusz/utils/gradient.py          # 渐变核心（fork 新增）
  GradientConfig                 # enabled/type/angle/stops/transparency
  create_linear/radial_gradient  # 创建 Qt 渐变
  _add_gradient_stops            # 应用 transparency 到色标
  PRESETS / get_preset / list_presets

veusz/utils/extbrushfilling.py   # 统一填充渲染入口
  brushExtFillPath               # 唯一入口：渐变短路 or 实色/阴影
  _brushExtFillPathGradient      # 渐变路径（透明度 bug 所在）
  fillToEdgePolygon              # fillto helper

veusz/setting/collections.py     # 设置树定义
  BrushExtended                  # 含 Gradient 子设置 (line 251)
  PlotterFill / PointFill        # fillto 定义

veusz/setting/setting.py         # 设置类型
  FillSet                        # 每数据集填充（3/10 元素）
  GradientFill                   # 渐变设置（dict）
  Brush/Line                     # 基础填充/描边

veusz/setting/controls.py        # UI 控件
  FillSet / _FillBox             # 每行填充编辑
  GradientFill                   # 渐变编辑面板
```

---

## 三、架构问题诊断（"乱"的根源）

### 3.1 渐变是并行渲染路径，透明度机制分裂

`brushExtFillPath`（extbrushfilling.py:225）是唯一渲染入口。fork 在它前面加了渐变短路分支：

```python
if gradient_module.is_gradient_enabled(extbrush.get('Gradient')):
    _brushExtFillPathGradient(...)   # 短路
    return
style = extbrush.style ...            # 实色/阴影路径，含 setAlphaF
```

- **实色/阴影路径**：正确应用 `extbrush.transparency`（extbrushfilling.py:246-250）
- **渐变路径**：完全忽略它（extbrushfilling.py:185-223 无 transparency 引用）

### 3.2 渐变自带透明度也锁死为 0

`GradientFill` 设置字典为 `{enabled,type,angle,stops,midpoint}`——**没有 `transparency` 字段**；
UI 控件也没暴露透明度滑块。因此 `config.transparency` 恒为 0。

### 3.3 每数据集渐变走不通（bar 等 FillSet 系）

- `FillSet.normalize`（setting.py:1734）只允许 3/10 元素元组 → **11 元素渐变行被拒绝**
- `returnBrushExtended`（setting.py:1756-1762）已支持 `len>=11` 加载渐变 → **死代码**
- `_FillBox.onSettingChanged`（controls.py:1486-1492）保存行数据时**不含渐变字段** → 改了不持久化

### 3.4 点图填充逻辑重复且不一致

`point.py` 有两个并行填充实现：
- `_drawBezierLine`（point.py:800-827）：if/elif 手写，fallback 到 **top**
- `_drawPlotLine`（point.py:844-860）：调 `fillToEdgePolygon`，fallback 到 **bottom**

同一 brush 值在两种插值下产生不同填充。`'mean'` 分支两处都有但不在 Choice 列表（UI 不可达）。

---

## 四、Bug/Gap 完整清单（带证据）

### 4.1 透明度（最高优先）
| ID | Bug | 证据 |
|----|-----|------|
| T1 | 渐变启用时 `extbrush.transparency` 被忽略，渐变恒不透明 | extbrushfilling.py:185-223 vs :246-250 |
| T2 | `GradientFill` 设置+UI 无透明度字段，`config.transparency` 恒 0 | setting.py:2036-2038, controls.py:2223-2228, gradient.py:86 |
| T3 | 渐变路径不处理 `transparency==100` 跳过填充 | 实色路径有 return（:247-249），渐变无 |

### 4.2 渐变集成
| ID | Bug | 证据 |
|----|-----|------|
| G1 | `FillSet.normalize` 拒绝 11 元素渐变行 | setting.py:1734 `len(fill) not in (3,10)` |
| G2 | `_FillBox` 扩展面板不持久化渐变 | controls.py:1486-1492 |
| G3 | 渐变只注册到 BrushExtended，plain Brush（boxplot 标记/箭头）无渐变 | collections.py:251 |
| G4 | `GradientFill` UI 无透明度滑块；midpoint 只从文本解析 | controls.py:2050-2230 |

### 4.3 Point/CI
| ID | Bug | 证据 |
|----|-----|------|
| P1 | std 模式双重 thin 切片 → 长度失配/退化多边形 | point.py:560-562,574-577 再 :641-642 |
| P2 | `_drawBezierLine` custom+'Auto' 无守卫 → 字符串进轴转换 | point.py:810-812（对比 :855 有守卫） |
| P3 | 两填充路径 fallback 不一致（top vs bottom） | point.py:821-822 vs :352-355 |
| P4 | 'mean' 死代码（不在 Choice） | point.py:804,850 vs collections.py:323-328 |
| P5 | 两套填充实现应去重 | point.py:800-827 vs :844-860 |
| P6 | `fillToEdgePolygon` 不处理 'auto'（潜在陷阱）+ 三个 `return` | extbrushfilling.py:352-355, 373-377 |

### 4.4 Shape Rectangle bounds
| ID | Bug | 证据 |
|----|-----|------|
| S1 | bounds 模式长度不齐 → IndexError（无 cycle 对齐） | shape.py:353-356（对比 BoxShape zip+cycle :144-148） |
| S2 | bounds 模式无交互控制项，updateControlItem 死代码 | shape.py:392 `controlgraphitems=[]` |
| S3 | `_getBoundsCoords`/`_getBoundsFromGraph` 的 else 分支死代码 | shape.py:290-294, 308-317 |
| S4 | bounds 模式需 getAxes parent，放在 page 上静默失败 | shape.py:279-285 |

### 4.5 Bar
| ID | Bug | 证据 |
|----|-----|------|
| B1 | 每数据集渐变被 G1/G2 阻断 | bar.py:386 `returnBrushExtended` |
| B2 | 透明度 per 填充行共享，非真正 per-dataset | FillSet 默认单行 |
| B4 | bar CI 只影响误差条，无填充带（point 有） | bar.py:289+ 无 errorsFilled 等价物 |

### 4.6 测试
| ID | Bug | 证据 |
|----|-----|------|
| TE1 | 测试只覆盖配置类，无渲染、无透明度、无 fillto 渲染 | test_gradient_fill.py:16-212 |

---

## 五、设计原则（遵循上游哲学）

1. **单一渲染入口**：`brushExtFillPath` 是唯一 fill 渲染入口；渐变/实色/阴影统一走它。
2. **透明度统一在 brush 层**：`extbrush.transparency` 对实色/阴影/渐变一律生效；
   渐变色标可再加自己的 alpha（二者复合，`alpha_eff = alpha_brush × alpha_gradient`）。
3. **设置驱动**：渐变是每个 fill brush 的一等属性，扩展为所有 fill 类型共享。
4. **消除重复**：fillto 判定收敛到 `fillToEdgePolygon` 单一 helper。
5. **向后兼容**：默认值保持旧行为，存盘格式尽量兼容（3/10/11 元素）。

---

## 六、开发计划（分批次）

### 批次 0：交接文档 ✅（本文档）
- 产出：`dev-docs/feature-development-plan.md`
- 状态：**完成**

### 批次 1：修复透明度分裂（T1-T3, G4 前半）✅
**目标**：渐变与实色透明度行为一致。
- `veusz/setting/setting.py`：`GradientFill` 默认字典加 `'transparency': 0`；`toUIText/fromUIText` 支持
- `veusz/setting/controls.py`：`GradientFill` 控件加透明度滑块（0-100）
- `veusz/utils/gradient.py`：`create_gradient_from_config` 加 `transparency` 覆盖参数
- `veusz/utils/extbrushfilling.py`：`_brushExtFillPathGradient` 复合 `extbrush.transparency` + `config.transparency`
  - `alpha_eff = (100-t_brush)/100 × (100-t_grad)/100`；任一方 100% → 跳过填充
- 测试：5 个渲染级透明度测试（画渐变 → 查像素 alpha，含复合与全透明跳过）
- 状态：**完成**

### 批次 2：修复 Point/CI（P1-P6）✅
**目标**：CI 填充正确、两条填充路径去重、fallback 一致。
- P1：删 std 分支对 xplotter/yplotter 的重复 thin 切片（统一到入口切一次）
- P2：`_drawBezierLine` custom 分支加 `val != 'Auto'` 守卫
- P3/P5：新增共享 helper `fillToEdgeTargets`，`fillToEdgePolygon` 与 `_drawBezierLine` 统一使用，fallback 一致
- P4：删除两处不可达的 'mean' 分支
- P6：`fillToEdgeTargets` 增加 'auto' 回退注释，删除三重 return
- 测试：7 个 `fillToEdgeTargets` 单元测试（各模式 + custom/'Auto' 守卫）
- 状态：**完成**

### 批次 3：完成渐变对每数据集填充的集成（G1-G2）✅
**目标**：bar/点图每个 dataset 可用渐变+透明度。
- G1：`FillSet.normalize` 允许 11 元素（`len(fill) in (3,10,11)`）
- G2：`_FillBox.onSettingChanged` 把 `e.Gradient` 序列化进 rowdata（index 10）
- 测试：25 渐变测试 + 78 selftests 通过
- 状态：**完成**
- **B4（bar CI 填充带）延后**：这是新功能而非 bug 修复，且几何复杂（grouped/stacked、水平/垂直）。按"先修后增"原则移到新增功能批次（见批次 7）。

### 批次 4：渐变全量扩展（G3）✅（决策：跳过边缘）
**目标**：评估非 BrushExtended 的 fill 渐变扩展。
- **结论（用户拍板）**：渐变已覆盖 ~95% fill（形状/bar/CI/直方图/contour 等，经 `brushExtFillPath`）。
  plain Brush（箱线标记/箭头）因 `setBrush`+循环 draw 模型只能跨视口渐变，视觉价值低，跳过。
  3D 顶点着色渲染模型不同，另行评估。
- 状态：**完成（无需代码变更）**

### 批次 5：修复 Shape Rectangle bounds（S1-S4）✅
**目标**：bounds 模式健壮、可交互。
- S1：draw 循环用模索引 `arr[i % len(arr)]` 对齐（长度不齐不再 IndexError）
- S2：bounds 模式为每个 rect 创建 `ControlResizableBox` 控制项（非 dataset 时），可拖拽/缩放
- S3：`_getBoundsCoords`/`_getBoundsFromGraph` 消除死 else，改为"有 axes 转数据坐标 / 无 axes 用 fractional"单一路径
- S4：rect 放 page（无 getAxes parent）时退化为 fractional 解释，不再静默失败
- 测试：3 个 `TestRectangleBounds` 测试（fractional 降级、axes 转换、长度不齐）
- 状态：**完成**

### 批次 6：测试套件加固（TE1）
**目标**：所有新增功能有渲染级回归测试。
- 渲染到 image → 校验像素；SVG 对比测试补新增功能
- 全量 `pixi run test` + `runselftest.py` 通过
- 状态：**未开始**

### 批次 7（延后）：新增功能（先修后增）
- **B4**：bar 图 CI 填充带（复用 point 的 errorsFilled 思路，按 bar 几何，含 grouped/stacked + 水平方向）
- 状态：**未开始**

### 渐变 UI 改进（已实施，用户要求优先）✅
用**交互式渐变条**替换原来的滚动色标列表：
- 新增 `GradientBar` 组件：点击空白加色标 / 拖拽移动 / 双击换色 / 拖出删除；选中标记高亮
- 新增"选中色标"微调行：Position % + 颜色按钮（精确控制）
- 预览加大到 32px，加棋盘格底纹以显示透明度，预览反映渐变透明度
- 删除废弃的 `ColorStopWidget` 滚动列表
- 测试：3 个 UI 控件测试（load、bar add/set/remove、save round-trip）
- 状态：**完成**

---

## 七、验证策略

每批次验收标准：
1. 新增渲染级测试通过（`pixi run test` 全绿）
2. `VEUSZ_INPLACE_TEST=1 pixi run python tests/runselftest.py` 78/78 通过
3. 手动/脚本渲染目标场景，目视确认（透明度、渐变、CI 带）
4. 更新本文档批次状态表

回归保险：`examples/` 下现有 .vsz 的 selftest 对比文件不变（除有意改动）。

---

## 八、风险与注意

- 渐变扩展会触碰 `makeQBrush`（boxplot 等）→ 需回归测试全量 selftests
- `FillSet` 格式从 3/10 扩到 3/10/11 → 旧文档兼容，新文档需要 normalize 通过
- 透明度复合数学：`alpha_eff = (100-t_brush)/100 × (100-t_grad)/100`，100% 任一方 → 全透明跳过
- 每批独立可回滚；先修后增，避免新功能叠在旧 bug 上

---

## 九、批次状态表

| 批次 | 内容 | 状态 | 提交 |
|------|------|------|------|
| 0 | 交接文档 | ✅ | — |
| 1 | 修复透明度分裂 | ✅ | 44777600 |
| 2 | 修复 Point/CI | ✅ | 批次2提交 |
| 3 | 渐变集成每数据集 (G1-G2) | ✅ | 批次3提交 |
| 3.5 | 渐变 UI 改进 | ✅ | UI提交 |
| 4 | 渐变全量扩展（决策：跳过边缘） | ✅ | — |
| 5 | 修复 Rectangle bounds | ✅ | 待提交 |
| 6 | 测试套件加固 | ⬜ | — |
| 7 | 新增功能（B4） | ⬜ | — |
| 6 | 测试套件加固 | ⬜ | — |
