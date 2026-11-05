# 09 运营迭代

> 合成训练成果。任务状态区分已完成的资料/代码与仍待实际用户或生产授权的验证。

持续观察价值、质量和成本，形成下一轮业务发现。

## 建立持续运营节奏

任务编号：`operation-observe`。状态：已完成。责任角色：顾明岚 / 秦芮 / 叶书。

交付：30/60/90天运营计划。

30天每周复盘误报漏报、缺项和未确认积压；60天比较同口径工时与返工、调整字段；90天重新核定价值与保留/退役。关键错误0容忍；未确认项超过2工作日提醒协调员；规则版本不一致即暂停交接。阈值为本项目建议，待业务批准；未接模型，因此不存在模型漂移，监测输入格式和规则版本漂移。

证据位置：docs/09-operation.md；docs/evidence/interviews.json；证据：f55,f34,f44。

## 演练事件与变更管理

任务编号：`operation-incident`。状态：已完成。责任角色：叶书 / 傅景 / 秦芮。

交付：事件复盘与变更记录。

已执行本地过期版本与回滚演练，并向虚拟客户及质量角色发送事件题目。事件时间线：检测旧版证书偏好→停止有问题的资料交接→记录影响范围→人工核对当前版本→恢复已知数据→修正来源→回归旧版反馈、偏好分类、权限与重复请求。真实客户报障、生产恢复时长和关闭签字没有发生；见operations.md及virtual-reviews.json。

证据位置：docs/09-operation.md；docs/evidence/interviews.json；docs/evidence/verification.json；docs/evidence/virtual-reviews.json；证据：virtual-reviews,verification。

## 复盘并启动下一轮发现

任务编号：`operation-iterate`。状态：已完成。责任角色：顾明岚 / 叶书 / 秦芮。

交付：项目复盘、迭代清单与作品集。

本轮形成36条合成访谈事实、无AI判断流程图、规则原型和可复现测试。决定保留离线训练，不宣称生产价值。下一轮优先验证正式Brief及30份UAT，其次补真实接口/身份/读取审计，最后再根据收益判断是否扩展。证据不足的自动筛选和模型摘要不列入当前交付。

证据位置：docs/09-operation.md；docs/evidence/interviews.json；docs/evidence/verification.json；docs/evidence/virtual-reviews.json；证据：all,verification,virtual-reviews。

## 关卡结论

运营节奏、事件闭环、复盘及下一轮优先级已确认。

本阶段文档与演练证据可审查；真实业务批准、真实UAT及正式签收均不得以自检代替。
