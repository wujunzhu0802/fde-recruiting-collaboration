# 需求规格与追溯

需求负责人为合成角色，不代表现实授权。所有需求都服务于“先澄清需求，再组织面试”，不评价某个人是否应该被录用。

## REQ-01 条件和字段核对

证据：fsg-recruiting-f10、f11、f15、f31。招聘顾问输入结构化岗位简报，系统保留must/preferred/clarify及原文来源，缺项或待澄清条件阻断交接。不得从“偏好”自动生成硬要求。代码：src/engine.py；测试：required_fields、ambiguous_and_source、preference_never_becomes_hard_condition。拒绝条件：没有来源仍标记可确认。限制：不能判定自然语言分类是否语义正确，必须人工核对。

## REQ-02 版本与反馈对齐

证据：fsg-recruiting-f11、f23、f24、f34。每条反馈必须引用当前岗位版本、已有条件ID和记录位置。旧反馈不覆盖新需求，应转人工处理。测试：stale_feedback、unknown_feedback、duplicate_condition、conflict_and_terminal。生产中的版本有效期、完整版本链尚未实现。

## REQ-03 可追溯的人工闭环

证据：fsg-recruiting-f14、f22、f41、f45。顾问、协调员或质量可创建核对单，质量或客户可确认。阻断项不得通过；修改需新建记录，保留旧单和退回原因。测试：normal_human_review、permissions、blocker_cannot_confirm。演练身份选择不是生产SSO。

## REQ-04 排期核对

证据：fsg-recruiting-f01、f20、f31。同一面试官的时间重叠必须列入冲突，首尾相接允许，日期需有时区。测试：schedule_overlap_and_adjacency、timezone_required。不进行自动邀请或自动日历写入。

## REQ-05 故障与幂等

证据：fsg-recruiting-f32、f35、f44。接口替身可模拟超时和不可用，失败进入人工核对；同幂等键同身份同内容不重复执行，异内容或异身份409。测试：timeout_and_degrade、idempotency_and_collision、concurrent_duplicate（12个并发请求）。

## REQ-06 记录与审计

证据：fsg-recruiting-f43、f45。保存UTC时间、演练身份、规则版本、输入SHA256及人工决定；原始输入与结果保存在本地SQLite。测试：normal_human_review、HTTP闭环、本地备份恢复。缺口：当前记录创建与确认事件，完整的读取日志、长期保留和删除策略未实现，生产不得上线。

## 跨需求边界

不做真实候选人决策，不接真实模型，不读真实简历，不承诺客户结果。请求内容作为资料，不解释为可执行指令（prompt_injection_is_data）。所有接口只绑定127.0.0.1；演练工具不适合暴露公网。
