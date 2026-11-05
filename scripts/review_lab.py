"""Virtual-role confirmation questions; responses are not real user sign-off."""
import json
import os
from pathlib import Path
from http.cookiejar import MozillaCookieJar
import requests

ROOT=Path(__file__).resolve().parents[1]
BASE='https://fde-discovery-lab-67046.app.workbuddy.host'
QUESTIONS=[
 ('r1','07-2 UAT','当前本地规则原型已通过18项单元测试的三轮回归和HTTP人工确认闭环；这只是工程师执行的合成测试，您尚未实际操作。请说明您独立完成“证书偏好已取消但旧反馈仍引用旧版”的任务时，必须看到哪些信息才敢交接？哪些情况应拒绝验收？'),
 ('r5','07-2 UAT','在训练中，清单只展示字段、来源、岗位版本和未结项，不排名或录用候选人。作为客户岗位负责人，确认这份交接清单前您要核对哪些条件？是否仍缺真实操作和原始样本证据？'),
 ('r0','08-1 business review','演练交付为本地只读规则核对工具，不接生产、不发通知。30份需求的业务验收尚待实际用户走查，ROI只是情景测算。请从业务视角明确继续试点的前置条件、谁可叫停，以及哪些缺口阻止正式上线。'),
 ('r3','08-1 technical review','演练代码使用SQLite事务和请求幂等键，检测旧版反馈、字段缺失和排期冲突，接口失败转人工；本地备份恢复已演练。生产SSO、真实接口和读取审计未完成。请从技术视角列出上线阻断项，不能把本地测试当成生产接入成功。'),
 ('r4','08-1 quality review','本轮仅合成数据，规则检查不直接筛除或录用，质量/客户角色才能确认，阻断问题不能通过；真实身份鉴权与跨企业隔离未接入。请说明质量视角是否允许直接正式上线，以及还需哪些依据。'),
 ('r3','08-3 technical handoff','交接演练：请复述读取失败或发现过期版本时应怎样停止影响、找谁确认、如何恢复已知快照。当前回滚记录只证明本地合成数据库恢复，不代表您已签收生产系统。'),
 ('r2','08-3 workflow handoff','交接演练：当缺项清单有未确认条件且排期冲突时，您先交给谁？交接记录必须包含哪些字段？不能只回复“已处理”。'),
 ('r5','09-2 incident','客户投诉旧版证书偏好仍被当成硬条件时，先登记哪些问题与版本？这是合成事件演练。'),
 ('r4','09-2 change control','旧版证书偏好事件中，修订后应保留什么审计和人工复核记录？这是合成变更演练。')]


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf8')
    jar=MozillaCookieJar(str(Path(os.environ['TEMP'])/'recruiting-cookies.txt'));jar.load(ignore_discard=True,ignore_expires=True)
    s=requests.Session();s.cookies.update(jar)
    provenance=json.loads((ROOT/'docs/evidence/provenance.json').read_text(encoding='utf8'))
    params=dict(projectId='fsg-recruiting',moduleId='fsg-recruiting',attemptId=provenance['attemptId'],stage='discovery')
    out=ROOT/'docs/evidence/virtual-reviews.json'
    records=json.loads(out.read_text(encoding='utf8')) if out.exists() else []
    for role,purpose,question in QUESTIONS:
        if any(x['purpose']==purpose and x['role']==role for x in records):continue
        for attempt in range(3):
            try:
                # A timed-out POST may have succeeded. Recover its actual response first.
                r=s.get(BASE+'/api/group-lab/state',params=params,timeout=40)
                r.raise_for_status();state=r.json();d=None
                history=state.get('history',[])
                for i,turn in enumerate(history[:-1]):
                    answer=history[i+1]
                    if turn.get('speaker')=='user' and turn.get('text')==question and answer.get('speaker')=='character':
                        d=dict(reply=answer['text'],audit=answer.get('audit'))
                if d is None:
                    r=s.post(BASE+'/api/group-lab/ask',params=params,json=dict(scenarioId='fsg-recruiting',characterId='fsg-recruiting-'+role,question=question),timeout=120)
                    r.raise_for_status();d=r.json()
                break
            except requests.RequestException:
                if attempt==2:raise
                print('Recovering transient network error',purpose,flush=True)
        records.append(dict(role=role,purpose=purpose,question=question,reply=d['reply'],audit=d.get('audit'),real_customer_signoff=False))
        out.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
        print(purpose,role,'recorded',flush=True)
    print('DONE virtual reviews',len(records),flush=True)


if __name__=='__main__':main()
