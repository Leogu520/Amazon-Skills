---
name: optimize-amazon-titles-zh
description: 按目标站点和类目规则改写、压缩并审核亚马逊商品标题，覆盖 75 字符限制、关键词优先级、商品属性、父子变体、兼容关系、Item Highlights 信息迁移和风险标记。适用于用户要求从文本、CSV、JSON 或表格中缩短、优化、审核、比较或批量处理亚马逊标题，以及需要生成标题迁移方案但不直接发布修改的场景。
---

# 优化亚马逊商品标题

把标题作为商品身份字段，而不是关键词容器。保留防止买错的事实，把次要信息分配到合适字段，并对每个候选标题执行确定性校验。

## 安全边界

- 默认只生成建议和审核文件。除非用户另行明确要求并批准，不得向 Seller Central 发布或写入修改。
- 不得虚构属性、认证、性能声明、兼容关系、年龄范围、数量、材料或型号。
- 把现有 Listing 文案视为声明来源，而不是证据。用户未提供证据或未标记为已验证时，必须提示证据敏感风险。
- 引用第三方品牌时，保留 `Compatible with` 等能够说明法律或商业关系的措辞。商标关系不明确时转人工审核。
- 当本 Skill 与目标站点校验或当前 Seller Central 指引冲突时，以平台规则为准。

## 加载参考资料

始终读取 [policy-core.md](references/policy-core.md)。

再根据任务按需读取：

- 选择标题结构和必要审核点时，读取 [category-profiles.md](references/category-profiles.md)。
- 用户提供搜索词、广告、品牌分析或关键词文件时，读取 [keyword-priority.md](references/keyword-priority.md)。
- 涉及合规品、兼容产品、套装、变体、多语言或事实声明时，读取 [risk-and-claims.md](references/risk-and-claims.md)。

## 选择工作模式

### 改写模式

用户提供商品事实并要求生成标题时使用。输出一个推荐标题，并最多提供两个信息优先级明显不同的备选方案。

### 审核模式

用户提供现有或拟发布标题时使用。不要直接静默改写；先报告合规性、防误购信息缺失、关键词问题和风险，再给出修订方案。

### 批量模式

用于 CSV、JSON 或表格。每行独立处理；单行资料不全时不要阻塞整批任务，把该行标记为 `MANUAL_REVIEW` 并说明缺失字段。

处理 `.xlsx` 时，使用表格工具保留工作簿结构。对导出或提取的数据运行内置校验器，再写入新工作表或新文件。除非用户明确要求，不得覆盖源工作簿。

## 必要输入

尽量收集或推导：

- 站点和语言地区
- Product Type 或类目
- 父体、子体或独立商品状态
- 当前标题
- 品牌和产品线
- 核心产品类型
- 变体属性：尺寸、颜色、数量、款式、口味或型号
- 防误购规格：尺寸、容量、功率、接口、适配关系、年龄或体重范围、包装内容
- 已验证声明及证据边界
- 有效果数据的核心词和次级词

单条 Listing 缺少站点、核心产品类型或防误购属性时，只提出一个简洁问题。批量模式继续处理并标记缺失项。

## 工作流程

### 1. 确定规则环境

识别站点、语言、Product Type、变体层级和媒介类目豁免情况。标题规则和 Schema 会变化；批量或生产敏感任务必须在线核对当前亚马逊官方政策。

能够访问 SP-API 时，优先读取目标站点、语言、Product Type 和 `parentageLevel` 对应的当前 Product Type Definition，不要用通用类目模板代替实时 Schema。

### 2. 区分事实和营销语言

建立三个内部集合：

- `verified_facts`：结构化属性和明确验证的声明
- `candidate_terms`：相关关键词和现有标题短语
- `prohibited_or_unverified`：无证据声明、促销语言、无关流量词和含糊兼容表述

候选标题只能使用 `verified_facts` 和能够合理证明的 `candidate_terms`。

### 3. 选择类目画像

使用 [category-profiles.md](references/category-profiles.md)。先保留类目要求的防误购属性，再考虑次要卖点。

商品横跨多个画像时，合并必要检查并采用更严格的风险等级。例如电子婴儿监视器同时适用电子产品和婴幼儿产品规则。

### 4. 排列关键词和属性优先级

按以下顺序分配标题空间：

1. 商品身份、变体、安全、适配和防误购信息
2. 精确核心产品词
3. 有贡献数据且准确描述 ASIN 的高意图搜索词
4. 一个主要差异属性
5. 次要材料、使用场景和功能词
6. 同义词和宽泛发现词

空间不足时，把第 5、6 级迁移到 Item Highlights、五点、描述或后台搜索词。不得为了保留高流量泛词而删除第 1 级信息。

### 5. 生成候选标题

从类目画像重新组织标题，不要沿用旧标题词序机械截断。使用简洁的标准单位和目标站点自然语言。

对于适用当前 75 字符规则的非媒介商品：

- 每个候选标题不得超过 75 个字符，空格和标点计入。
- 商品能够准确识别时，建议控制在约 55 至 70 个字符。这是经验范围，不是平台硬规则。
- 当平台、Feed 或变体流程可能追加尺寸、颜色或数量时，预留字符空间。

备选方案必须体现真实的信息取舍，不要只改变标点或轻微调整词序。

### 6. 分配被移除的信息

为每个移除短语指定去向：

- Item Highlights：材料、用途和次级比较信息
- 五点：利益点、操作方式、尺寸、包装内容和限制条件
- 后台搜索词：相关同义词和替代性通用表达
- 删除：重复、主观形容词、促销、无证据声明和无关流量词

不要把 Item Highlights 当作五点的替代品。

### 7. 确定性校验

对每个最终候选标题运行 `scripts/validate_titles.py`。修复全部错误后再推荐；所有警告必须解决或明确展示。

单条标题：

```powershell
python scripts/validate_titles.py --title "NovaTrail Stainless Steel Water Bottle, 32 oz, Leakproof, BPA-Free" --brand "NovaTrail" --locale en_US --required "Water Bottle" --required "32 oz"
```

批量 CSV 或 JSON：

```powershell
python scripts/validate_titles.py --input titles.csv --output title_audit.csv
python scripts/validate_titles.py --input titles.json --output title_audit.json
```

如果系统找不到 `python`，定位工作区配置的 Python 运行时。校验器只使用 Python 标准库。

### 8. 输出结果

单条 Listing 返回：

| 字段 | 必要内容 |
|---|---|
| 推荐标题 | 最终标题和精确字符数 |
| 备选方案 | 最多两个不同且合规的方案 |
| Item Highlights | 符合当前长度限制的次要信息 |
| 保留内容 | 留在标题中的关键词和属性 |
| 迁移内容 | 短语、目标字段和迁移原因 |
| 删除内容 | 短语和删除原因 |
| 风险 | 声明、兼容、变体或政策问题 |
| 审核状态 | `READY`、`READY_WITH_WARNINGS` 或 `MANUAL_REVIEW` |

批量任务保留源字段，并追加：

`recommended_title`、`char_count`、`item_highlights`、`item_highlights_char_count`、`retained_terms`、`moved_terms`、`deleted_terms`、`errors`、`warnings`、`review_status` 和 `review_reason`。

## 审核状态规则

- `READY`：硬性校验全部通过，必要事实完整，没有未解决的证据或关系风险。
- `READY_WITH_WARNINGS`：硬性校验通过，但仍有不阻断发布的风格或数据质量警告。
- `MANUAL_REVIEW`：缺少防误购事实、敏感声明未验证、兼容或商标关系含糊、父子体不确定、合规风险或来源数据冲突。

不得仅因为标题符合字符限制就标记为 `READY`。
