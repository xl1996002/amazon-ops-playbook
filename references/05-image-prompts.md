# 图片与 A+ 作图提示词

> 用途：把产品写成一套可交给图像模型（ChatGPT / Midjourney / 即梦等）的提示词。
> **提示词不描述产品不具备的属性**——写进去的每一个细节都要能在产品图里找到对应。

## 1. 提示词六要素（缺一个就会跑偏）

| 要素 | 写什么 | 反例 |
|---|---|---|
| 画面主体 | 产品本身 + 关键结构（几个部件、怎么组合） | 「a shelf」 ✗ |
| 构图 | 视角（正面/45°/俯拍/平视）、产品占画面比例、留白位置 | 「wide shot」 ✗ |
| 风格 | 商业产品摄影 / 生活方式场景 / 极简棚拍 | 「beautiful」 ✗ |
| 光线 | 柔光箱 / 自然窗光 / 侧逆光，光源方向 | 「good lighting」 ✗ |
| 色调 | 主色 + 辅色 + 情绪（暖木色、冷灰、燕麦白） | 「nice colors」 ✗ |
| 比例 | 1:1（主图）/ 4:5 / 16:9（A+ 横幅） | 不写会得到意外长宽比 |

统一附加：`product photography, photorealistic, high resolution, no text, no watermark, no logo`

## 2. 主图提示词模板

```
{产品全称与关键结构}, centered on pure white seamless background (RGB 255,255,255),
straight-on eye-level view, product fills 85% of the frame, fully visible without cropping,
soft even studio lighting from front-left, no shadow on background, minimal contact shadow only,
commercial e-commerce product photo, ultra sharp focus, 1:1 square
--no text, watermark, logo, props, hands, extra objects
```

**主图硬约束**：纯白底、产品占比 ≥85%、完整不裁切、不加文字水印、不用场景和道具。

## 3. 副图提示词模板（按类型选，最多 6 张）

### 3.1 使用场景图

```
{产品} in use in a {目标国家典型空间: compact UK kitchen / small Berlin apartment},
{具体动作或摆放状态}, {人物手部或环境线索}, natural window light from the {方向},
warm neutral palette, shallow depth of field, lifestyle product photography, 4:5
```

### 3.2 尺寸对比图

```
{产品} next to {参照物: a standard dinner plate / a hand / a 15 inch laptop} for scale,
same plane and same distance from camera, clean light grey background,
flat side view showing true proportions, technical clarity, 1:1
```

### 3.3 细节特写图

```
extreme close-up of {具体部位: the welded joint / the rounded rim / the fabric weave},
macro lens, raking side light to reveal surface texture, shallow depth of field,
neutral background, 1:1
```

### 3.4 功能图解图

```
{产品} shown at the exact angle that reveals {功能结构}, one single clean composition,
soft directional light casting a defined shadow, plain background leaving empty space
on the {left/right} for callout labels, 1:1
```

> 图上的标注文字不要交给图像模型生成（会拼错），出图后在设计工具里加。

### 3.5 包装内容图

```
all items included in the box laid out in a neat flat-lay: {逐项列出配件},
evenly spaced on a light neutral surface, top-down view, soft shadowless lighting, 1:1
```

### 3.6 差异化对比图

```
split composition: left half shows {普通产品做法}, right half shows {本品做法},
same lighting and same scale on both sides, clean minimal background, 4:5
```

## 4. A+ 模块图提示词

A+ 按「视觉叙事顺序」规划，不是把副图放大。默认五段：

| 顺序 | 模块 | 提示词要点 | 比例 |
|---|---|---|---|
| 1 | 场景横幅 | 目标国家真实生活场景，产品在画面 1/3 处，留出文字区 | 16:9 或 3:1 |
| 2 | 痛点对比 | 左右分屏，同光线同尺度 | 1:1 或 4:5 |
| 3 | 功能图解 | 单一功能结构特写，留标注位 | 1:1 |
| 4 | 材质细节 | 微距质感，侧逆光 | 1:1 |
| 5 | FAQ / 对比表 | 干净背景的产品正面图，供叠文字 | 1:1 |

A+ 提示词模板：

```
{场景描述}, {产品} placed {位置}, {目标国家室内特征: sash window, radiator, wooden floor},
natural daylight, {色调}, generous negative space on the {left/right} for headline text,
editorial lifestyle photography, 16:9
```

## 5. 负面提示词（每次都要带）

```
--no text, letters, watermark, logo, brand mark, distorted product, extra parts,
wrong proportions, blurry, low resolution, plastic-looking, oversaturated, collage
```

## 6. 输出格式

每张图给两条信息，不要只给英文提示词：

```
【图 1｜主图】white background, product fills 85%
Purpose: 搜索结果页第一眼识别产品是什么
Prompt: {英文提示词全文}

【图 2｜使用场景】compact UK kitchen worktop
Purpose: 让买家看到"我家也能放下"
Prompt: {英文提示词全文}
```

中文说清「这张图要说服买家什么」，英文负责给模型执行。

## 7. 合规注意

- AI 生成的图**不能出现文字**（模型会把字拼错，且可能生成违规宣称）
- 不能凭空加配件、改材质、改数量——买家收到货对不上会直接退货 + 差评
- 场景图里的空间要符合目标国家实际（UK 厨房台面窄、DE 常见斜顶）
- 不生成对比竞品品牌的画面
- 出图后必须人工比对实拍图，比例与结构失真就重出
