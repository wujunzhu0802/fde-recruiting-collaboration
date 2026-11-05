# 08 上线交接

> 合成训练成果。任务状态区分已完成的资料/代码与仍待实际用户或生产授权的验证。

把通过试点的版本交给具名负责人，明确上线和回退责任。

## 审查上线准备

任务编号：`handoff-readiness`。状态：进行中。责任角色：顾明岚 / 秦芮 / 傅景。

交付：上线准备检查与三方评审。

已分别向业务、技术、质量虚拟角色发出上线评审问题，保留各自回答，不合并为默认同意。本机演练可复现，但生产SSO、授权样本、正式接口、实际UAT和预算签核缺失，正式上线结论为NO-GO。只能交付训练原型与文档，不能称已获得三方上线批准。

证据位置：docs/08-handoff.md；docs/evidence/interviews.json；docs/evidence/verification.json；docs/evidence/virtual-reviews.json；证据：virtual-reviews,verification。

## 演练发布与回滚

任务编号：`handoff-release`。状态：已完成。责任角色：秦芮 / 唐映秋。

交付：发布计划与回滚演练记录。

交付版本1.0.0，发布窗口与灰度对象限本机合成演练。先冻结源码哈希并运行回归，备份数据库；出现旧版默认通过、异常增多或授权问题立即停止；恢复已知快照并核对一份已确认样本。scripts/verify.py已经真实执行本地备份→注入故障单→恢复→确认已知记录，仅证明本地恢复。

证据位置：docs/08-handoff.md；docs/evidence/interviews.json；docs/evidence/verification.json；证据：verification。

## 完成运维和用户交接

任务编号：`handoff-transfer`。状态：进行中。责任角色：秦芮 / 唐映秋 / 叶书。

交付：交接清单、运行手册与签收记录。

已提供运行手册、API契约、源代码、测试、流程图和未结风险，并向虚拟系统与协调角色提出交接复述问题。建议技术接收秦芮、流程接收唐映秋、业务接收顾明岚/叶书；这些是场景责任映射，不是真实人员签收。生产权限、支持渠道和具名签收日期待真实项目确认。

证据位置：docs/08-handoff.md；docs/evidence/interviews.json；docs/evidence/virtual-reviews.json；证据：virtual-reviews。

## 关卡结论

业务、技术和风险角色的上线准备及交接决定有依据。

本阶段文档与演练证据可审查；真实业务批准、真实UAT及正式签收均不得以自检代替。
