# 06 测试评估

> 合成训练成果。任务状态区分已完成的资料/代码与仍待实际用户或生产授权的验证。

证明行为与需求一致，区分模拟验证、真实模型验证与业务验收。

## 建立评估集合

任务编号：`validation-evalset`。状态：已完成。责任角色：傅景 / 秦芮。

交付：评估集与需求覆盖表。

tests/test_workflow.py有18项测试，按正常、边界、对抗、权限和故障分组。重点覆盖偏好不自动转硬条件、旧反馈、未知条件、时区和重叠、提示注入仅作为数据、角色越权、幂等碰撞、12次并发同键、乐观锁、阻断项不能确认。失败成本主要是过期要求传播与越权结论。

证据位置：docs/06-validation.md；docs/evidence/interviews.json；证据：f11,f33,f40,f44。

## 执行测试与重复评估

任务编号：`validation-execute`。状态：已完成。责任角色：项目实施者 / 秦芮。

交付：测试报告与评估结果。

scripts/verify.py对代码快照运行18项测试×3轮，执行HTTP正常到人工确认闭环、401/403/404、静态页面资源检查，并实际执行本地SQLite备份恢复。证据含UTC时间、完整测试日志和源码SHA256。node --check检查前端语法。运行模式为本地规则与合成替身；真实模型、生产集成和真实UAT未执行。

证据位置：docs/06-validation.md；docs/evidence/interviews.json；docs/evidence/verification.json；证据：verification。

## 修复并回归确认

任务编号：`validation-repair`。状态：已完成。责任角色：秦芮 / 傅景。

交付：缺陷闭环与质量结论。

首轮发现SQLite连接上下文只提交未关闭，在Windows清理临时数据库时失败。已改为contextmanager确保commit/rollback后finally关闭；18项测试随后三轮全部通过。未解决项为生产身份、读取审计、真实接口、长期数据保留、完整有效期链和实际用户独立操作；不将这些项目误标为通过。

证据位置：docs/06-validation.md；docs/evidence/interviews.json；docs/evidence/verification.json；证据：verification。

## 关卡结论

评估范围、版本、失败项、修复复测与剩余风险可审查。

本阶段文档与演练证据可审查；真实业务批准、真实UAT及正式签收均不得以自检代替。
