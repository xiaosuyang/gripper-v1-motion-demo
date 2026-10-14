# 力控夹爪 V1.0 · 开闭运动交互演示

单页 WebGL 演示站：几何**直接取自 SolidWorks 导出的 `装配体-左手.STEP`**（非手工示意模型），
按运动关系分为 6 组网格（半透明壳体 / 静止结构件 / 电机+传感器板 / 左指运动件 / 右指运动件 / 0.5 模齿轮），
可任意旋转视角观看开闭过程，并实时显示开口尺寸。

- 在线地址（GitHub Pages）：见仓库 Settings → Pages，形如 `https://<user>.github.io/<repo>/`
- 在线地址（QW Pages 镜像）：`https://ezp935dc.qwenwork.host/`

## 操作

| 操作 | 功能 |
|---|---|
| 拖拽 | 轨迹球旋转（无角度限制，可翻越顶/底） |
| 滚轮 / 双指 | 缩放 |
| Shift 或右键拖拽 | 平移 |
| 双击 | 复位视角 |
| 「开口」滑块 / 播放 | 控制开闭（0–70 mm，含真实行程约束） |
| 外壳半透明 | 切换壳体透明度以观察内部齿条-齿轮-导轨联动 |

## 目录

```
index.html      单页应用（Three.js r128 + 自研轨迹球控制 + 二进制 STL 解析）
stl/*.stl       6 组二进制 STL（OpenCascade 三角化，线性弦高 0.18 mm，共约 16.5 万三角面）
```

## 重新生成网格（CAD 改版后）

网格由 OpenCascade (OCP) 从 STEP 三角化得到：

```bash
pip install cadquery-ocp
python tools/dump_groups.py     # 由 STEP 生成 包围盒→运动分组 映射 tools/groups.json
python tools/export_ocp.py      # 按分组三角化并写出 stl/*.stl
```

分组规则见 `tools/export_stl.py` 中的 `classify()`（壳体/固定盖板、静止结构、电机与 PCB、
左右手指运动件、齿轮）。STEP 文件（53 MB）不入仓库，需自备。
注意：gmsh 无法剖分该模型中的周期（闭合）B 样条曲面，故不使用 gmsh。

## 运动学约定

模型位姿开口 30.2 mm；单侧位移 δ ∈ [−15.1, +20] mm，开口 = 30.2 + 2δ。
+20 mm 上限来自 MGN9 滑块到导轨端部的余量（而非齿条啮合），齿轮按节圆半径 R = 10 mm 同步转动。
