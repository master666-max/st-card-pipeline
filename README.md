# st-card-pipeline

**从长篇小说语料量产 SillyTavern 角色卡与世界书的方法论 + 工具链。**

从一部 517 章、约 550 万字的长篇小说全本（含证据可回链的正典库）上实战验证过的方法中，抽取出的可复用部分：不含任何小说文本、角色卡成品或个人数据——只有机制、参数、工具与结论。

## 它解决什么

- **角色卡不像活人** → 口吻指纹归纳（统计检验）+ 盲认测试判卷 + 修复闭环，实测把盲认成绩从抛硬币线拉到 62.5%；
- **剧情推进要手动改卡** → 阶段化双态世界书：「卡不动、状态走世界书」，事件词驱动前态/后态自动翻转（身份交底、伏笔兑现）；
- **多卡/群聊设定打架** → 共通库（全局挂载）+ 专属库（卡内嵌）分库架构，附六型 schema 与边界三问；
- **AI 味重** → 定量画像：生成台词比原话长 47%、语气词密度高 55%，给出两个硬靶（句长砍 30%、语气词配额）。

## 凭什么能通

- 全部数字来自单次完整实战（四假设终审 + 世界书笔法五实验 + 动态面实聊判卷），见 [docs/04](docs/04-实验与判卷结论.md)；
- PNG 打包按 SillyTavern v1.19.0 源码级规格实现（chara/ccv3 双 chunk，ccv3 优先），回读三关对账；
- 阶段化双态机制经静态三关验证（翻转词碰撞扫描 / 前缀陷阱禁用 / 前后键表一致性断言）；真机翻转实测进行中。

## 快速开始

```bash
# 0) 自测：编译全部工具 + 合成数据跑通四件（零依赖上游语料；PNG 件需 Pillow）
py -X utf8 selftest.py

# 1) 打包角色卡 PNG（v2/v3 双 chunk；无底图时自动生成占位图）
py -X utf8 tools/png_pack.py pack card.json card.png
py -X utf8 tools/png_pack.py verify card.json card.png

# 2) 关系断言聚簇（正典 relation 记录目录 → 关系簇库 + 概览表）
py -X utf8 tools/pair_cluster.py --src <relation_json目录> --outdir out

# 3) 阶段化双态条目并入卡书/独立世界书（按 comment 标记拆分 专属/共通）
py -X utf8 tools/merge_staged.py --staged examples/staged_entries_example.json \
    --card card.json --worldbook common.json \
    --card-out card_v2.json --worldbook-out common_v2.json --card-version 0.2

# 4) 实聊漂移量化（动态面判卷）
py -X utf8 tools/chat_drift.py --src chat.jsonl --out 全文.md --sig 诶,拜托

# 5) 双态判卷匿名化（甲/乙随机，映射与判卷侧物理隔离）
py -X utf8 tools/anonymize_cards.py --dir . --cards a.json,b.json --mapping-out 映射.json

# 6) 发布前隐私零命中扫描（本仓自带的门，建议用于你自己的衍生仓）
py -X utf8 tools/scan_privacy.py <目录> --forbid 自定义禁词1,禁词2
```

## 文档地图

| 文档 | 内容 |
|---|---|
| [01-管线总览](docs/01-管线总览.md) | 第一性原理五条 + 七阶段生成管线 + 判卷仪器 + 上游最小契约 |
| [02-阶段化双态世界书](docs/02-阶段化双态世界书.md) | 「卡不动、状态走世界书」完整机制：双态对模板 / 失效模式 F1-F9 / 群聊兼容 |
| [03-共通与专属分库](docs/03-共通与专属分库.md) | 六型 schema / 预算账 / 边界三问 / REL keys 纪律 / 升级扩展位 |
| [04-实验与判卷结论](docs/04-实验与判卷结论.md) | H1-H4 终审 / 笔法五实验 / AI 味定量 / 判卷工程纪律 |

## 工具清单

| 工具 | 一句话 |
|---|---|
| `png_pack.py` | 角色卡 PNG 打包/回读/对账（chara_card_v2 + v3 双 chunk，共享字段逐字一致断言） |
| `pair_cluster.py` | 关系断言 → 无向对聚簇（强度=记录数+章跨度），多卡关系网分库的底料 |
| `merge_staged.py` | 阶段化双态条目 → 按库归属标记并入卡内嵌书/独立世界书 |
| `chat_drift.py` | ST 聊天 JSONL → 漂移量化曲线（签名词/语气词/句长可参数化） |
| `anonymize_cards.py` | 判卷匿名化（甲/乙随机分配，映射留档） |
| `scan_privacy.py` | 隐私零命中扫描门（正则类 + 自定义禁词，命中即退出码 1） |

## 安全模型

- **本仓不含**：小说原文/引文、角色卡成品、判卷对话记录、任何 API key 或个人路径；
- 文档示例全部为合成内容（「夜鸦/星织/灰港城」等），机制参数为真实实战值；
- `scan_privacy.py` 是把本流程发布出去时用的最后一道门：正则类（用户目录/token/私钥/邮箱/内网 IP）+ 自定义禁词，零命中才放行；
- 上游语料与成品卡的版权归属原作者/ respective 权利人；本仓只含方法与工具。

## 已知限制

- 全部数字来自**单一小说语料的单轮实战**，跨语料泛化未验证；
- 阶段化双态的 ST 真机翻转实测进行中（结果回填 docs/02 §五）；
- 工具按 Windows（`py -X utf8`）调教，其他平台请自行替换解释器调用方式；
- `png_pack.py` 依赖 Pillow（仅占位图生成需要，pack 已有底图时不需要）。

## License

[MIT](LICENSE)
