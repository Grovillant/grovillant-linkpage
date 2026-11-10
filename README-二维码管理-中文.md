# Grovillant 二维码管理与印刷

设计师先看 print-pack/v1.0.0/PRINT-README-中文.md；老板先看 qr/管理报告-中文.md。

注册表唯一来源：qr/registry.json。vercel.json、q/*/index.html 和 qr-analytics.js 是生成文件。印刷包是只增不改的版本快照。
旧根目录二维码文件仍保留用于历史识别；今天交付只取 print-pack/v1.0.0。

## 维护命令

    python3 -m pip install -r requirements-qr.txt
    python3 scripts/build_qr_routes.py           # 只检查
    python3 scripts/build_qr_routes.py --write   # 仅生成本地文件
    python3 generate_qr.py --version 1.0.1
    python3 scripts/validate_qr.py --pack print-pack/v1.0.1
    python3 scripts/validate_qr.py --pack print-pack/v1.0.1 --online

图像验收另需 cv2 与 numpy；本次使用 OpenCV 4.13.0、numpy 2.2.4。SVG 为自包含的矢量方块和白色底，PNG 是 RGB 无透明底。
同样的注册表、脚本、依赖和版本在不同输出根目录重生成，应逐字节相同。
默认输出目录若已存在即退出，绝不静默覆盖。改版使用新版本；交付旧版不删。

## 输入输出与执行边界

- registry() 输入 UTF-8 JSON：固定 HTTPS 品牌域名、唯一 qr_id、唯一稳定 URL、物料、负责人角色、active/retired、日期、版本、变更、回滚、不可停用。运行时断言错误即拒绝继续。
- 跳转配置：每条短路径及尾斜线返回可更改的 307；静态托管不识别 Vercel 配置时使用原网页跳转。注册表的目标与 HTML/JS 必须完全相同。
- 生成器输入 --version x.y.z 和可选 --output-root，输出只读交付快照和 SHA-256；不读取凭据，无网络，无生产写入。版本目录是幂等键；重复调用非零退出。中断留下未完成版本目录时先人工检查，另用新版本重建。
- 校验器成功输出 JSON、退出 0；静态/图像失败非零并报断言；线上失败输出 UNVERIFIED 后退出 2。线上每个入口一次 GET，超时 12 秒、并发最多 3，不重试；自动 HTTP 重定向有 urllib 上限。
- 本地 HTTP 只读模拟 Vercel 跳转；环境不准开端口则使用明确标注的离线路由模型，不能声称已测真实 HTTP。在线模式支持识别旧 meta refresh，但不执行网页 JS。
- 不把校验原始日志、客户数据、凭据、运行状态提交 Git；报告只提交汇总证据。运行输出另存仓库外或被忽略的 qr-runtime/。

## 每次维护

1. 老路径永久保留，retired 仅表示不再新印，访问继续转到有效替代页，may_disable 始终 false。退役时登记 replacement_url 和变更原因，不能返回 404。
2. 改目标：修改注册表，保留老 UTM，增加 changes，更新 last_review_date/version，重新生成跳转并校验；二维码字节无需变更。
3. 加物料：新建未使用过的 /q/小写英文名称；登记专用 campaign、负责人、日期和用途。不得复用旧 qr_id 给不同用途。生成配置、出新包并验收；新路径未经授权上线与真机验证不能开印。
4. 同一物料需要区分批次/展会/年份时增加全新路径（例如 /q/fair-2027），不能靠换目标来重定义旧码归属。旧码历史仍算旧渠道。
5. 回滚：从上一已验收提交恢复注册表及生成配置，再按发布流程上线；恢复旧根页面联系方式时只改 index.html。不得删除旧印刷资产。
6. 每月首个工作日由品牌负责人巡检；登记路径、日期、状态、目标、UTM、两联系按钮、问题与处理人。只保留渠道汇总和内部批次登记，不记录个人扫描轨迹。

统计过滤校验（离线，不发送事件）：node scripts/test_qr_analytics.cjs。只保留登记的 UTM；后台是否能按 UTM 出报表须核验套餐及生产配置，见管理报告。
