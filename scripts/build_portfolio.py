"""Build nine-stage portfolio from collected virtual interviews and task notes."""
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'

# Each conclusion is independently reviewable; production claims remain pending.
DETAILS=[
('opportunity-trigger','顾明岚 / 林亦舟','已完成','触发事件是客户取消证书偏好后，旧筛选表仍将它当作硬条件（f11）。业务问题不是缺少生成式摘要，而是条件分类、版本和交接来源失配。维持现状会重复核对并传播过期要求，优先验证一页缺项清单的价值。范围限制为招聘需求简报与面试安排；不进行候选人排名、筛除或录用。','f10,f11,f15,f00,f05'),
('opportunity-baseline','林亦舟 / 叶书','已完成','基线为实验室合成样本：40份岗位简报、120条面试安排、返工核对9小时（f12），不能推断为企业月度真实数据。粗算每份简报分摊13.5分钟，仅用于情景分析。正式测量应逐单记录发生时间、接收时间、首次处理和返工处理分钟数；以完整观察窗内全部简报为分母，缺失值单列，林亦舟采集、叶书复核。','f12,f13,f51,f53'),
('opportunity-mandate','顾明岚 / 傅景 / 叶书','已完成','顾明岚决定试点范围；傅景代表审核质量视角，保留停止权；叶书确认结果用途。一线由林亦舟参与，唐映秋负责交接，秦芮负责系统边界。预算约束是四周、两名业务骨干每人每周不超过4小时，不等于已经批准现金预算。真实数据授权、费用审批人和正式签署版Brief仍须补证。','f03,f04,f40,f41'),
('discovery-interviews','林亦舟 / 六角色','已完成','已实际调用六个虚拟角色，每人按六个主题提问，共36轮基础访谈、36条调查事实。原始提问、回答、时间及模型调用审计均保存在evidence/interviews.json；角色分别覆盖业务、一线、交接、技术、质量、客户。后续确认型提问另存virtual-reviews.json。角色回答是合成训练，不是真实员工陈述。','all'),
('discovery-process','唐映秋 / 林亦舟','已完成','还原链路：客户访谈→条件确认→材料整理→排期→反馈归档。流程图含6个判断点：信息是否齐全、客户是否确认、是否发生变更、排期是否冲突、反馈是否完整且版本正确、复核是否通过。每个否定分支有补充、回退或协调路径。群消息先发生、后补填，因此回填时间不能替代实际发生时间。图见flowcharts.md及diagrams/as-is-no-ai.svg。','f01,f13,f20,f23'),
('discovery-evidence','顾明岚 / 秦芮 / 叶书','已完成','四来源收敛：Buyer关注减少重复核对；Operator要求缺项及原行来源；Brief仅有平台合成开场和练习样本描述，缺正式签署材料；Industry用上海外服官网确认业务方向，不证明内部接口。冲突保留：业务希望尽快排期，但顾问要求先澄清条件；采用先确认后交接，紧急情况由具名负责人决定。台账中所有访谈事实标为合成待交叉验证。','f00,f15,f21,f32,f50'),
('definition-prioritize','顾明岚 / 林亦舟','已完成','P0是条件分类、旧版反馈和来源缺失，因为可导致错误要求传播；P1是排期冲突和未结项交接；P2是自然语言摘要与真实系统接入。按风险、发生模式、规则可实现性排序；不以缺乏统计支持的发生频率打虚构分数。先用确定性规则解决结构化核对，保留未分类条件交给人。','f11,f15,f31,f44'),
('definition-requirements','叶书 / 傅景','已完成','REQ-01字段与必备/偏好明确；REQ-02反馈关联岗位版本及条件ID；REQ-03来源定位与人工确认；REQ-04排期重叠核对；REQ-05越权、超时和重复请求处置；REQ-06确认链审计。每项关联证据、输入输出、使用者、代码与测试，详见requirements.md。排除真实候选人决策、外部通知和生产写回。','f22,f31,f32,f41,f45,f52'),
('definition-acceptance','顾明岚 / 傅景 / 叶书','已完成','实验室业务目标：30份需求全部区分硬条件与偏好，反馈全部关联当时版本，每条输出关联来源及人工复核。工程验收覆盖5类用例：正常、边界、对抗、权限、故障；关键规则测试应100%通过，越权确认、旧版默认通过和重复执行允许0例。30份真实业务UAT的完成耗时与采用率尚未测量，不能用单元测试替代。','f02,f42,f51'),
('solution-wedge','顾明岚 / 林亦舟','已完成','比较三种方案：人工统一模板成本最低但持续返工；结构化模板+确定性规则可直接检查缺项、版本和时间冲突；模型摘要增加不确定性且当前无必要。选择第二种，一批次岗位简报、本机合成数据、只读核对、人工确认。按用户补充要求，交付现状无AI流程图；原型不接模型。','f05,f15,f32,f52'),
('solution-architecture','秦芮 / 傅景','已完成','浏览器本地工作台→HTTP接口→规则引擎→SQLite核对单与审计。只读适配器为显式stub；timeout/unavailable是故障注入而非真实上游。顾问/协调员/质量可创建，质量/客户可确认，工程角色不能确认。生产SSO、跨客户隔离、完整读取审计、外部接口和有效期链治理尚未实现，是正式上线阻断项。','f31,f32,f34,f41,f45'),
('solution-plan','顾明岚 / 叶书','已完成','四周工作安排：发现与需求、设计与构建、回归与试点准备、交接与复盘。两名骨干合计最多32小时。情景报价为一次性8000元、月运行300元，并非客户报价或批准预算。以9小时/批、每月4批、节省40%、采用80%、兑现50%、100元/小时为假设，月可兑现576元，净收益276元，回本约29个月，首年ROI约-40.4%，不建议直接扩围。详见roi.md。','f03,f12,f51'),
('build-contract','秦芮 / 唐映秋','已完成','JSON输入字段包括brief、feedback、schedule及演练模式。岗位含job_id/version/owner/location/headcount/source_id/conditions；每项条件有id/kind/text/source，反馈引用brief_version、condition_id、evidence_ref，排期必须带时区。未确认用clarify，缺失留空；不将两者合并成默认通过。examples/normal.json为自己构建的合成样本，不冒充客户文件。','f21,f23,f31,f32'),
('build-implement','林亦舟 / 秦芮','已完成','版本1.0.0可从python -m src.server运行。正常路径：载入样本→规则核对→生成带来源的清单→质量或客户角色确认→保存修订及审计。规则位于src/engine.py，事务和权限位于src/store.py，HTTP与页面位于src/server.py及src/web。模型未接入；所有自然语言仅按原文显示，不执行其中指令。','f14,f15,f22,f45'),
('build-failure','秦芮 / 傅景','已完成','六类异常均有实现与测试：缺字段生成阻断项；旧反馈、排期和乐观锁冲突阻断；越权返回403；接口timeout/unavailable转人工；请求幂等键同内容返回原核对单、异内容409；降级保留原输入且不声称最新状态。SQLite事务保证同键并发只生成一次，审计保存来源指纹、规则版本、身份、确认意见。','f35,f44,f45'),
('validation-evalset','傅景 / 秦芮','已完成','tests/test_workflow.py有18项测试，按正常、边界、对抗、权限和故障分组。重点覆盖偏好不自动转硬条件、旧反馈、未知条件、时区和重叠、提示注入仅作为数据、角色越权、幂等碰撞、12次并发同键、乐观锁、阻断项不能确认。失败成本主要是过期要求传播与越权结论。','f11,f33,f40,f44'),
('validation-execute','项目实施者 / 秦芮','已完成','scripts/verify.py对代码快照运行18项测试×3轮，执行HTTP正常到人工确认闭环、401/403/404、静态页面资源检查，并实际执行本地SQLite备份恢复。证据含UTC时间、完整测试日志和源码SHA256。node --check检查前端语法。运行模式为本地规则与合成替身；真实模型、生产集成和真实UAT未执行。','verification'),
('validation-repair','秦芮 / 傅景','已完成','首轮发现SQLite连接上下文只提交未关闭，在Windows清理临时数据库时失败。已改为contextmanager确保commit/rollback后finally关闭；18项测试随后三轮全部通过。未解决项为生产身份、读取审计、真实接口、长期数据保留、完整有效期链和实际用户独立操作；不将这些项目误标为通过。','verification'),
('pilot-prepare','顾明岚 / 林亦舟 / 唐映秋','已完成','受控试点计划：四周、单一批次、30份合成需求为离线验收目标；真实业务试点另需授权。对照使用相同复杂度、相同口径的人工模板路径；记录逐单首次处理、返工、确认完成与总等待。顾问与协调员兜底。发现旧版默认通过、越权确认或真实个人信息误入立即暂停；采用率与节省时间阈值须业务确认。','f02,f03,f05,f42'),
('pilot-uat','林亦舟 / 叶书','进行中','已向虚拟一线与客户发出确认型问题，回复见virtual-reviews.json。现有证据仅为工程师执行的合成闭环及角色对验收条件的陈述，不等于真实使用者独立完成任务。UAT脚本见pilot-uat.md：正常提交、旧证书偏好/旧反馈、排期冲突、越权及故障转人工。30份用户操作、真实耗时、采用障碍和具名验收待执行，故保持进行中。','virtual-reviews'),
('pilot-value','顾明岚 / 叶书','进行中','尚无同口径的真实试点后数据，不能宣称节省40%已实现。情景ROI为负，只支持继续低成本离线澄清，不支持扩大生产投入。下一决策需完成实际UAT、逐单前后配对、人工复核成本和采用率采样，排除样本难度差异后再决定继续、修改或停止。','f12,f51,virtual-reviews'),
('handoff-readiness','顾明岚 / 秦芮 / 傅景','进行中','已分别向业务、技术、质量虚拟角色发出上线评审问题，保留各自回答，不合并为默认同意。本机演练可复现，但生产SSO、授权样本、正式接口、实际UAT和预算签核缺失，正式上线结论为NO-GO。只能交付训练原型与文档，不能称已获得三方上线批准。','virtual-reviews,verification'),
('handoff-release','秦芮 / 唐映秋','已完成','交付版本1.0.0，发布窗口与灰度对象限本机合成演练。先冻结源码哈希并运行回归，备份数据库；出现旧版默认通过、异常增多或授权问题立即停止；恢复已知快照并核对一份已确认样本。scripts/verify.py已经真实执行本地备份→注入故障单→恢复→确认已知记录，仅证明本地恢复。','verification'),
('handoff-transfer','秦芮 / 唐映秋 / 叶书','进行中','已提供运行手册、API契约、源代码、测试、流程图和未结风险，并向虚拟系统与协调角色提出交接复述问题。建议技术接收秦芮、流程接收唐映秋、业务接收顾明岚/叶书；这些是场景责任映射，不是真实人员签收。生产权限、支持渠道和具名签收日期待真实项目确认。','virtual-reviews'),
('operation-cadence','顾明岚 / 秦芮 / 叶书','已完成','30天每周复盘误报漏报、缺项和未确认积压；60天比较同口径工时与返工、调整字段；90天重新核定价值与保留/退役。关键错误0容忍；未确认项超过2工作日提醒协调员；规则版本不一致即暂停交接。阈值为本项目建议，待业务批准；未接模型，因此不存在模型漂移，监测输入格式和规则版本漂移。','f55,f34,f44'),
('operation-incident','叶书 / 傅景 / 秦芮','已完成','已执行本地过期版本与回滚演练，并向虚拟客户及质量角色发送事件题目。事件时间线：检测旧版证书偏好→停止有问题的资料交接→记录影响范围→人工核对当前版本→恢复已知数据→修正来源→回归旧版反馈、偏好分类、权限与重复请求。真实客户报障、生产恢复时长和关闭签字没有发生；见operations.md及virtual-reviews.json。','virtual-reviews,verification'),
('operation-retrospective','顾明岚 / 叶书 / 秦芮','已完成','本轮形成36条合成访谈事实、无AI判断流程图、规则原型和可复现测试。决定保留离线训练，不宣称生产价值。下一轮优先验证正式Brief及30份UAT，其次补真实接口/身份/读取审计，最后再根据收益判断是否扩展。证据不足的自动筛选和模型摘要不列入当前交付。','all,verification,virtual-reviews'),
]


def main():
    active=json.loads((Path(os.environ['TEMP'])/'recruiting-active.json').read_text(encoding='utf8'))
    interview=json.loads((DOCS/'evidence/interviews.json').read_text(encoding='utf8'))
    details={d[0]:d for d in DETAILS}
    details['operation-observe']=details['operation-cadence']
    details['operation-iterate']=details['operation-retrospective']
    facts=interview['found']
    records=[]
    for i,stage in enumerate(active['curriculum']['stages'],1):
        filename=f'{i:02d}-{stage["id"]}.md'
        text=[f'# {i:02d} {stage["title"]}', '', '> 合成训练成果。任务状态区分已完成的资料/代码与仍待实际用户或生产授权的验证。', '',stage['goal'],'']
        for task in stage['steps']:
            _,owner,status,notes,refs=details[task['id']]
            evidence=f'docs/{filename}；docs/evidence/interviews.json；'+ ('docs/evidence/verification.json；' if 'verification' in refs else '')+('docs/evidence/virtual-reviews.json；' if 'virtual-reviews' in refs else '')+'证据：'+refs
            notes=notes.replace('（f','（fsg-recruiting-f')
            record=dict(stepId=task['id'],owner=owner,status=status,notes=notes,evidence=evidence)
            records.append(record)
            text.extend([f'## {task["title"]}', '',f'任务编号：`{task["id"]}`。状态：{status}。责任角色：{owner}。','',f'交付：{task["output"]}。','',notes,'',f'证据位置：{evidence}。',''])
        text += ['## 关卡结论','',stage['gate']+'。','', '本阶段文档与演练证据可审查；真实业务批准、真实UAT及正式签收均不得以自检代替。']
        (DOCS/filename).write_text('\n'.join(text)+'\n',encoding='utf8')
    (DOCS/'task-records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
    text=['# 六角色访谈与证据台账','','来源是实验室实际在线调用；角色与事实均为合成训练。36/36采集完成，不等于现实证据完整。','']
    for role in interview['scenario']['characters']:
        text += [f'## {role["name"]} · {role["role"]}','']
        for turn in interview['history']:
            if turn.get('characterId')==role['id']:
                text += [('**问：** ' if turn['speaker']=='user' else '**答：** ')+turn['text'],'']
        text += ['### 采集的事实','']
        for f in facts:
            if f['characterId']==role['id']:
                text += [f'- `{f["id"]}` / {f["evidence"]}：{f["text"]}（状态：合成角色陈述，真实场景待核实）']
        text.append('')
    (DOCS/'interviews-and-evidence.md').write_text('\n'.join(text).rstrip()+'\n',encoding='utf8')
    (DOCS/'evidence/scenario-context.json').write_text(json.dumps(dict(project=active['project'],context=active['curriculum']['context'],source='公开业务方向 · 合成演练'),ensure_ascii=False,indent=2),encoding='utf8')
    print('Built nine stage reports, 27 task records, transcript and evidence ledger')


if __name__=='__main__':main()
