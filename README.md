# amazon-ops-playbook

亚马逊运营全链路技能包：**取数诊断 → Listing 文案 → 主副图提示词 → A+ 规划 → 广告方案 → 广告组配置 → 结构图**。

丢一个竞品 ASIN 链接，一口气跑完七步。自带一个零依赖校验器，把最容易返工的地方用机器卡住：字符数超限、关键词跨模块重复、两版描述不一致。

## 为什么做这个

写 listing 和投广告是两件事，但它们的失败原因是同一类：**靠感觉**。

- 标题凭手感写到 78 个字符，上架后被平台截断
- 关键词在每个模块都塞一遍，读起来像词表
- 五点写的是参数，不是买家能拿到的好处
- 广告预算「参考同行」，说不清 £18 是怎么来的

这个技能包把能机器判定的部分做成脚本，把不能判定的部分做成检查清单。

## 目录结构

```
amazon-ops-playbook/
├── SKILL.md                          # 七步主流程、三条铁律、交付契约、自检闸门
├── references/
│   ├── 01-listing-spec.md            # 页面文案规范：关键词策略 / 字符上限 / 五点 / 双版描述 / 搜索词
│   ├── 02-ads-playbook.md            # 广告：结构 / 命名 / 关键词分层 / 预算推导 / 三阶段 / ACOS
│   ├── 03-data-sourcing.md           # 取数口径：来源优先级 / 抓取字段 / 降级方案 / 数据质量判断
│   ├── 04-compliance.md              # 合规：禁用词 / 需取证词 / Title Case / 类目风险
│   └── 05-image-prompts.md           # 主图 / 副图 / A+ 的作图提示词模板（六要素）
├── scripts/
│   └── check_listing.py              # 零依赖校验器
├── assets/
│   ├── listing-output-template.md    # 交付稿骨架
│   ├── ads-plan-template.md          # 广告方案骨架
│   ├── adgroup-config-template.csv   # 广告组配置表
│   └── ads-structure-template.html   # 广告结构示意图（浅色单文件）
└── examples/
    └── example-listing.json          # 校验器输入示例（可直接跑）
```

## 安装

放进技能目录即可：

```bash
# 用户级（所有项目可用）
cp -r amazon-ops-playbook ~/.workbuddy/skills/

# 项目级（随仓库共享）
cp -r amazon-ops-playbook .workbuddy/skills/
```

Windows 路径为 `%USERPROFILE%\.workbuddy\skills\`。

> 支持 Claude Code 等使用 `SKILL.md` 约定的环境：把目录放进对应的 skills 目录即可，脚本不依赖任何第三方库。

## 使用

直接说要做什么，技能会自动触发：

- 「按这个竞品链接 B0XXXXXXXX 做一套，英国站」
- 「帮我写这个产品的 listing，图在附件」
- 「这套页面做 A+ 文案和作图提示词」
- 「给 B0XXXXXXXX 出广告方案和广告组配置」
- 「画一张广告结构示意图」

## 单独用校验器

不依赖技能，可以独立跑：

```bash
python3 scripts/check_listing.py examples/example-listing.json
python3 scripts/check_listing.py my-listing.json --json-report report.json
```

退出码：`0` = 无 ERROR（可交付），`1` = 存在 ERROR，`2` = 输入格式错误。

### 它检查什么

**硬指标**
- Title ≤ 75 字符、Item Highlights ≤ 125 字符、Search Terms ≤ 250 字节
- 五点是否 5 条、是否以【卖点标题】开头
- HTML 描述是否只用了 `p / br / b / ul / li`，有无内联样式、脚本、图片、外链
- 双版描述长度与段落一致性

**关键词**
- 七分类覆盖率（核心词 100%、长尾词 ≥80%）
- 跨模块冲突：Title ↔ Item Highlights、Item Highlights ↔ Search Terms、五点重复主攻
- 「分配表说放在 Title，正文里却找不到」这类标注与内容不符
- 长尾词里包含核心词时**不会**误报为重复（这是有意设计的）

**合规**
- 绝对化词（error 级）与疑似促销词（warning 级）
- 需取证词提示：waterproof / heavy duty / food safe / medical grade …
- 品牌名、ASIN 残留
- Title Case 中的介词、冠词、连词大小写

### 示例输出

```
[硬指标]（OK=达标, !=未达标；是否阻断见下方问题清单）
  OK Title 字符数              72  (限 75)
  OK Item Highlights 字符数    70  (限 125)
  OK Search Terms 字节数       63  (限 250)
  OK 五点条数                   5  (限 5)
  OK 核心词覆盖率              3/3  (限 100%)
  OK 长尾词覆盖率             100%  (限 >=80%)

[关键词覆盖]
  核心词    vanity chair            Title / 五点#2 / 五点#3 / 描述
  长尾词    swivel vanity chair     五点#3
  场景词    bedroom                 Item Highlights / 五点#2 / 描述

[问题清单]
  无

ERROR 0  |  WARN 0
RESULT: PASS
```

## 需要自己替换的部分

| 位置 | 默认内容 | 建议 |
|---|---|---|
| `references/01-listing-spec.md` | 75 / 125 字符上限 | 平台规则变更时同步更新；不同类目上限可能不同 |
| `references/02-ads-playbook.md` §2 | 通用命名模板 | **团队有内部广告规范时，整体替换这一节** |
| `references/04-compliance.md` | 通用禁用词与需取证词 | 按类目和目标市场补充本地化违禁词 |
| `scripts/check_listing.py` 顶部常量 | 禁用词表 | 补充你所在站点的违禁词 |

## 设计原则

1. **不编造**：参数只能来自产品资料或实测数据，缺就标「待确认」
2. **硬指标先过机器**：能用脚本判定的绝不用肉眼
3. **一个词只主攻一个位置**：75 字符的标题装不下所有词，靠分配而不是堆砌
4. **结论必须挂证据**：广告预算与出价要能写出推导式
5. **轻交付**：HTML 一律浅色单文件，Markdown 优先

## 免责

- 平台规则、字符上限、广告后台字段会变化，使用前请核对当前生效的官方要求。本仓库是工作流与方法论，不是平台政策的权威来源。
- 广告预算、出价、ACOS 的数值都是推导示例，不构成投放效果承诺。
- 示例中的品牌与 ASIN 仅用于说明格式。

## License

MIT
