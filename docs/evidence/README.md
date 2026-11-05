# 证据说明

- interviews.json：本轮实际调用虚拟角色返回的36轮基础问答、36条事实与模型审计。虚拟角色由实验室平台模型扮演，不能当作真实公司员工采访。
- virtual-reviews.json：后续验收、三方评审、交接复述与事件题目的实际平台回答；real_customer_signoff=false，不伪造客户签字。
- lab-report.json：平台自动生成的发现报告。它是未独立核实的合成分析材料，若建议与最终无AI规则方案不一致，以仓库中的需求与方案文档为准。
- import-result.json：平台确认导入的事实数量；导入后仍属于待核实证据。
- provenance.json：当前同场景新练习的ID及返回地址。原用户练习属于另一Cookie会话，未绕过访问控制读取。
- verification.json：本地真实执行的三轮测试、HTTP闭环、源码哈希和本地数据库恢复。它不证明真实系统接入、生产恢复或真实用户UAT。
- scenario-context.json：平台公开场景背景，不含私有Cookie或真实个人数据。
- training-sync.json（同步完成后生成）：逐项写回实验室的27条结论及状态回读；未伪造任何阶段关卡批准。

本项目实际完成23项可独立验证的训练任务，四项需真实业务验证的任务维持进行中。全部27项均有结论、证据、负责人和交付材料。API脚本使用的Cookie和GitHub登录令牌未提交。
