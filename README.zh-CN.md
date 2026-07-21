# 亚马逊标题优化与审核 Skill

[English](README.md)

这是一个面向 Codex 的开源 Skill，用于跨品类改写和审核亚马逊商品标题。

仓库提供两个可独立安装的版本：

- `optimize-amazon-titles`：英文指令与英文界面
- `optimize-amazon-titles-zh`：中文指令与中文界面

它把类目结构、关键词优先级、商品属性和确定性校验结合起来，检查标题与 Item Highlights 字符数、重复词、禁用字符、必要属性、兼容关系、促销语言和需要证据支持的声明。

> 本项目是独立的卖家运营工具，与 Amazon 不存在隶属、授权、赞助或背书关系。

## 为什么做这个 Skill

亚马逊宣布，从 2026 年 7 月 27 日起，除媒介类目外，商品标题必须控制在 75 个字符以内，空格也计算在内，同时增加 125 字符的 Item Highlights 字段。

如果只是把旧标题机械截短，很容易误删型号、尺寸、数量、变体和适配关系。因此，这个 Skill 不把标题优化理解成“删到 75 个字符”，而是重新判断信息优先级：

- 哪些信息必须留在标题中防止买错
- 哪些核心关键词值得占据标题位置
- 哪些内容应该移到 Item Highlights、五点、描述或后台词
- 哪些夸张、重复或无证据内容应该删除

## 主要能力

- 单条标题改写、审核和多方案对比
- CSV、JSON 和 Excel 批量处理流程
- 覆盖常见消费品、服装、电子、汽车、工业、美妆、食品、婴幼儿、玩具和套装等品类
- 根据商品属性和关键词数据确定标题优先级
- 输出推荐标题、Item Highlights、关键词去留和修改原因
- 标记兼容性、父子变体、合规品类和声明证据风险
- 同时统计 Unicode 字符数和 UTF-8 字节数
- 输出 `READY`、`READY_WITH_WARNINGS` 或 `MANUAL_REVIEW`

Skill 默认只提供修改建议和审核结果，不会自动写回 Seller Central。

## 安装

克隆仓库后，把中文版 `optimize-amazon-titles-zh` 文件夹复制到 Codex 全局 Skills 目录。

Windows PowerShell：

```powershell
Copy-Item -Recurse .\optimize-amazon-titles-zh "$HOME\.codex\skills\optimize-amazon-titles-zh"
```

macOS 或 Linux：

```bash
cp -R ./optimize-amazon-titles-zh ~/.codex/skills/optimize-amazon-titles-zh
```

如果没有立即出现在 Skill 列表中，请新建一个 Codex 任务后再调用。

## 使用方法

```text
使用 $optimize-amazon-titles-zh，审核并改写这批亚马逊标题。
保留核心关键词和防止误购的属性，输出推荐标题、Item Highlights、
迁移和删除的词、风险提示及审核状态。
```

处理表格时：

```text
使用 $optimize-amazon-titles-zh 处理这个 Excel。
保留原始字段，并新增 recommended_title、char_count、item_highlights、
retained_terms、moved_terms、deleted_terms、errors、warnings、
review_status 和 review_reason。
```

## 独立校验脚本

脚本只使用 Python 标准库。

```powershell
python .\optimize-amazon-titles-zh\scripts\validate_titles.py `
  --title "RoadForge Front Wheel Bearing Hub, Compatible with Audi A1 2010-2019" `
  --brand "RoadForge" `
  --required "Wheel Bearing Hub" `
  --required "Audi A1" `
  --referenced-brand "Audi"
```

批量文件：

```powershell
python .\optimize-amazon-titles-zh\scripts\validate_titles.py `
  --input .\examples\titles.csv `
  --output .\title-audit.csv
```

## 测试

```powershell
python -m unittest discover .\optimize-amazon-titles-zh\scripts -p "test_*.py" -v
python -m py_compile .\optimize-amazon-titles-zh\scripts\validate_titles.py
```

## 规则更新

亚马逊政策和 Product Type Schema 会变化。Skill 在 `references/policy-core.md` 中保存了带日期的规则基线，并要求在批量或生产敏感任务前重新核对官方来源。最终应以目标站点 Seller Central 和当前 Product Type Definition 为准。

## 开源协议

[MIT](LICENSE)
