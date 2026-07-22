# 亚马逊标题政策基线

最近核验：2026-07-21

本文件仅作为政策基线，不能替代目标站点当前帮助页面或 Product Type Definition Schema。

内置校验器基线：`US`/`en_US` 和 `UK`/`en_GB`。这些环境仍必须提供 `marketplace`、`locale`、`product_type` 和 `parentage_level`。其他环境继续执行 75/125 字符后备检查，但在核验目标站点当前 Schema 前统一返回 `MANUAL_REVIEW`。

## 当前基线

- 从 2026 年 7 月 27 日起，除媒介类目外，所有类目的商品标题不得超过 75 个字符，空格计入。
- Item Highlights 提供另外 125 个字符，用于材料、推荐用途和比较信息。
- 亚马逊表示 Item Highlights 可被搜索，并与标题一起显示在搜索结果和详情页。
- 生效后仍超过 75 个字符的标题，可能被逐步更新为亚马逊 AI 推荐版本。
- 在该过程中 Listing 保持在售。
- 品牌所有者在推荐修改实施前有 14 天审核期。
- 最近核验时，图书和 DVD 不受本次 75 字符变更影响。
- 最近核验时 Item Highlights 仍在逐步上线，部分卖家反馈报错或无法保存。字段不可用时，在审核输出中保留拟迁移文本并标记“待发布”，不得以此为理由继续保留不合规长标题。

主要来源：

- 美国公告：https://sellercentral.amazon.com/seller-forums/discussions/t/145b6d0f-999c-4555-896c-c694bda2e470
- Amazon Q&A：https://sellercentral.amazon.com/seller-forums/discussions/t/ac660707-60c7-43e3-a3fd-420d7321cc4e
- 媒介类目说明：https://sellercentral.amazon.com/seller-forums/discussions/t/ae5ffd79-c7f5-4f3e-8739-fb87bb77b6f4
- 英国公告：https://sellercentral.amazon.co.uk/seller-forums/discussions/t/33f0a42a-17f1-46ef-b110-ba7512a3c881
- 德国公告：https://sellercentral.amazon.de/seller-forums/discussions/t/d24be94b-9ca5-437f-a7c2-1f4f7462a15f
- Item Highlights 上线问题：https://sellercentral.amazon.com/seller-forums/discussions/t/03248ae4-c13b-4c63-aa37-03b42b285d70

## 现有通用标题规则

2025 年 1 月 21 日政策建立了以下通用要求：

- 在 2026 年字段拆分前，大多数 Product Type 的标题上限为 200 个字符，空格计入。
- 除非属于品牌名称的一部分，标题不得使用 `!`、`$`、`?`、`_`、`{`、`}`、`^`、`¬` 和 `¦`。
- 同一个词在标题中不得出现两次以上；介词、冠词和连词除外。

2026 年公告改变标题长度和字段分配，但没有说明上述其他规则已经废止。除非当前 Seller Central 指引或 Product Type Schema 另有规定，继续执行这些规则。

来源：https://sellercentral.amazon.com/seller-forums/discussions/t/b2b15728-0d43-453e-974f-59eb63f73059/

## Schema 和站点检查

能够通过认证访问时，使用 Product Type Definitions API：

- 搜索目标站点可用的 Product Type。
- 使用 `marketplaceIds`、`locale` 和 `parentageLevel` 获取精确 Schema。
- 使用 `requirementsEnforced=ENFORCED` 执行提交级校验。
- 检查字符串长度、枚举、必填属性和变体约束。
- 同时计算可见字符数和 UTF-8 字节数。亚马逊 Meta-Schema 支持 `maxUtf8ByteLength`，非 ASCII 文本可能受字节限制。

官方文档：

- https://developer-docs.amazon.com/sp-api/docs/search-available-product-type-definitions
- https://developer-docs.amazon.com/sp-api/lang-en_EN/docs/retrieve-a-product-type-definition
- https://developer-docs.amazon.com/sp-api/docs/product-type-definition-meta-schema

## 政策刷新规则

以下任一情况必须重新核对官方来源：

- 任务发生在最近核验日期之后，并涉及批量或生产敏感修改。
- Seller Central 拒绝本地校验器通过的标题。
- 目标站点、Product Type 或字段行为与本基线不同。
- Item Highlights 不可用、无法保存或显示方式不同。

不要承诺 Item Highlights 与 Title 具有相同的排名权重。亚马逊只说明二者可搜索，并未公布相同字段权重。

内置校验器统计 Unicode Code Point 和 UTF-8 字节。重复词检测主要适用于空格分词语言。最终接收结果以 Seller Central 和当前 Product Type Schema 为准，尤其是 CJK 文本、组合字符和站点特定分词。

校验器的完整促销词、重复词、兼容关系和证据声明模式以英文为主。非英文标题只执行长度和硬性字符检查，并增加 `UNSUPPORTED_TITLE_LANGUAGE`；不得把结果描述为完整审核。

`media_exempt` 不是豁免证据。内置校验器只对完整匹配政策环境中的 `ABIS_BOOK`、`BOOK`、`BOOKS` 或 `DVD` Product Type 应用本地豁免。其他豁免请求继续执行 75 字符后备检查并转人工审核。
