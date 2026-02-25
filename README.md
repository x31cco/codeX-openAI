# PDCP 解析增强（面向 Wireshark 集成）

该仓库提供了一个可直接嵌入 dissector 的 PDCP 解析核心，重点补齐了 5G NR 最新常用配置：

- NR DRB 18-bit SN 数据 PDU 解析
- NR SRB/DRB 12-bit SN 数据 PDU 解析
- PDCP Control PDU 中 STATUS REPORT 的 FMC/bitmap 解析（含 18-bit SN 场景）
- 按 RAT + Bearer 类型校验合法 SN 配置，避免错误解码

> 受当前环境网络策略限制，无法直接从 GitHub 拉取 wireshark 主仓（HTTPS CONNECT 403）。
> 该实现以“可迁移核心解析逻辑 + 自动化测试”的形式交付，便于后续直接移植到 `packet-pdcp-*` dissector。
