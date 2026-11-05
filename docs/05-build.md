# 05 构建集成

> 合成训练成果。任务状态区分已完成的资料/代码与仍待实际用户或生产授权的验证。

实现可运行的最小闭环，使规则、模型与人工责任可追溯。

## 落实数据与工具契约

任务编号：`build-contract`。状态：已完成。责任角色：秦芮 / 唐映秋。

交付：数据契约与集成记录。

JSON输入字段包括brief、feedback、schedule及演练模式。岗位含job_id/version/owner/location/headcount/source_id/conditions；每项条件有id/kind/text/source，反馈引用brief_version、condition_id、evidence_ref，排期必须带时区。未确认用clarify，缺失留空；不将两者合并成默认通过。examples/normal.json为自己构建的合成样本，不冒充客户文件。

证据位置：docs/05-build.md；docs/evidence/interviews.json；证据：f21,f23,f31,f32。

## 实现业务闭环

任务编号：`build-implement`。状态：已完成。责任角色：林亦舟 / 秦芮。

交付：原型代码与版本说明。

版本1.0.0可从python -m src.server运行。正常路径：载入样本→规则核对→生成带来源的清单→质量或客户角色确认→保存修订及审计。规则位于src/engine.py，事务和权限位于src/store.py，HTTP与页面位于src/server.py及src/web。模型未接入；所有自然语言仅按原文显示，不执行其中指令。

证据位置：docs/05-build.md；docs/evidence/interviews.json；证据：f14,f15,f22,f45。

## 实现异常与审计

任务编号：`build-failure`。状态：已完成。责任角色：秦芮 / 傅景。

交付：异常处理与审计样例。

六类异常均有实现与测试：缺字段生成阻断项；旧反馈、排期和乐观锁冲突阻断；越权返回403；接口timeout/unavailable转人工；请求幂等键同内容返回原核对单、异内容409；降级保留原输入且不声称最新状态。SQLite事务保证同键并发只生成一次，审计保存来源指纹、规则版本、身份、确认意见。

证据位置：docs/05-build.md；docs/evidence/interviews.json；证据：f35,f44,f45。

## 关卡结论

指定版本可复现运行，异常和人工交接路径完整。

本阶段文档与演练证据可审查；真实业务批准、真实UAT及正式签收均不得以自检代替。
