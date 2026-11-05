"""Export submission formats and four existing platform materials with provenance."""
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'


def write(path,text):
    # Canonical LF bytes keep source hashes identical after Git normalization.
    path.write_bytes((text.rstrip()+'\n').encode('utf8'))


def main():
    interviews=json.loads((DOCS/'evidence/interviews.json').read_text(encoding='utf8'))
    reviews=json.loads((DOCS/'evidence/virtual-reviews.json').read_text(encoding='utf8'))
    roles={r['id']:r for r in interviews['scenario']['characters']}
    records=[]
    history=interviews['history']
    for i,turn in enumerate(history[:-1]):
        answer=history[i+1]
        if turn['speaker']!='user' or answer['speaker']!='character':continue
        role=roles[turn['characterId']]
        records.append(dict(id=f'INT-{len(records)+1:03d}',kind='基础访谈',role_id=role['id'],name=role['name'],
                            role=role['role'],at=answer['at'],question=turn['text'],answer=answer['text'],
                            evidence_ids=answer.get('factIds',[]),source='evidence/interviews.json'))
    for r in reviews:
        role=roles['fsg-recruiting-'+r['role']]
        records.append(dict(id=f'INT-{len(records)+1:03d}',kind=r['purpose'],role_id=role['id'],name=role['name'],
                            role=role['role'],at=(r.get('audit') or {}).get('at',''),question=r['question'],answer=r['reply'],
                            evidence_ids=[],source='evidence/virtual-reviews.json'))
    assert len(records)==45 and len(interviews['found'])==36
    write(DOCS/'访谈记录.json',json.dumps(dict(project='fsg-recruiting',nature='合成训练；非真实公司员工访谈',
          basic_interviews=36,followup_interviews=9,records=records),ensure_ascii=False,indent=2))
    with (DOCS/'访谈记录.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['id','kind','name','role','at','question','answer','evidence_ids','source']
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader()
        for row in records:
            row=dict(row,evidence_ids=';'.join(row['evidence_ids']))
            # Export text safely for spreadsheet applications.
            w.writerow({k:("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v) for k,v in row.items()})
    parts=['# 访谈记录','','36轮基础访谈 + 9轮确认型访谈，共45条问答。均为实际调用实验室虚拟角色返回的合成内容，不代表真实员工或真实验收。',
           '', '[JSON结构化记录](访谈记录.json) / [CSV表格记录](访谈记录.csv) / [36事实台账](interviews-and-evidence.md)','']
    for r in records:
        parts.extend([f'## {r["id"]} · {r["name"]} / {r["role"]}', '',f'类别：{r["kind"]}；时间：{r["at"]}。','',
                      '**问：** '+r['question'],'','**答：** '+r['answer'],'',
                      '证据编号：'+('、'.join(r['evidence_ids']) or '确认型问答，未另增事实编号')+'。',''])
    write(DOCS/'访谈记录.md','\n'.join(parts))

    # Freeze only public module fields, never session cookies or account details.
    source_path=DOCS/'evidence/original-materials-source.json'
    if not source_path.exists():
        active=json.loads((Path(os.environ['TEMP'])/'recruiting-active.json').read_text(encoding='utf8'))
        data=dict(caseInfo=active['curriculum']['modules'][0]['caseInfo'],context=active['curriculum']['context'])
        write(source_path,json.dumps(data,ensure_ascii=False,indent=2))
    else:
        write(source_path,source_path.read_text(encoding='utf8'))
    data=json.loads(source_path.read_text(encoding='utf8'));c=data['caseInfo'];ctx=data['context'];rs=c['roles']
    output=DOCS/'original-materials';output.mkdir(exist_ok=True)
    common=f'项目：{c["company"]} · {c["title"]}。\n\n> 平台原有合成训练资料的Markdown等价导出；不是正式客户文件。编号：'
    brief=['# 客户简报','',common+'fsg-recruiting-01。','',f'行业：{c["industry"]}。业务现场：{c["room"]}。','',
           '## 客户提出的问题','',c['opening'],'','## 项目目标与范围','',ctx['problem'],'',
           '需建立的基线：'+ctx['baseline'],'','调查样本：'+ctx['sample'],'','边界：'+ctx['boundary'],'','## 需要核实的角色诉求','']
    for r in rs:brief.append(f'- {r["name"]}（{r["role"]}）：{r.get("request") or r.get("task") or r["intro"]}')
    brief.extend(['','资料性质：'+c['source']+'。上述诉求尚不等于确认需求；不预设根因、预算或承诺收益。','','## 平台列出的公开背景来源',''])
    for s in c['sources']:brief.append(f'- [{s["title"]}]({s["url"]})')
    request=['# 现状信息请求表','',common+'fsg-recruiting-02。','',f'以“{ctx["sample"]}”为样本。全部条目为待索取资料，实际持有人、版本和权限需访谈确认。','']
    for r in rs:
        request.extend([f'## {r["name"]} · {r["role"]}','',r.get('problem') or r.get('task') or r['intro'],'',
                        f'围绕“{r.get("request") or r.get("focus") or c["title"]}”，提供最近一次处理记录、输入输出、交接对象、异常及适用规则，核对原话与实际过程；记录日期、版本、脱敏范围和可访问位置。',''])
    request.extend(['指标核对：'+ctx['baseline'],'','每份资料补记：名称／来源人／版本／样本时间窗／权限／已取得或待补／与角色陈述的差异。'])
    questions=['# 业务发现访谈问题库','',common+'fsg-recruiting-03。','','围绕最近一单展开，先听当事人描述，再向其他角色交叉核实。','']
    stakeholders=['# 利益相关者资料与分工','',common+'fsg-recruiting-04。','','以下为六角色公开资料；审批权、预算和最终验收权需进一步访谈确认。','']
    for r in rs:
        questions.extend([f'## {r["name"]} · {r["role"]}','','本角色切入点：'+(r.get('problem') or r.get('task') or r['intro']),'',
                          f'- 在“{c["title"]}”中，请以最近处理的一次事件说明：{r.get("request") or r.get("focus") or r["intro"]}'])
        questions.extend(f'- 结合你作为{r["role"]}的实际操作：{q}' for q in r['questions'])
        questions.extend(['- 哪份原始资料能核对上述说法？与哪个角色的记录可能不一致？',''])
        stakeholders.extend([f'## {r["name"]} · {r["role"]}','','角色介绍：'+r['intro'],'',
                             '现场问题：'+(r.get('problem') or '具体事件待访谈核实'),'',
                             '本角色任务：'+(r.get('task') or r.get('request') or r['intro']),'',
                             '核对重点：'+(r.get('focus') or r.get('request') or c['title']),'',
                             '协作要求：说明自己接收谁的输入、向谁交接，提供对应记录；与其他角色交叉核实，不能替其他角色确认权限或业务事实。',''])
    documents=[('01-客户简报.md',brief),('02-现状信息请求表.md',request),('03-业务发现访谈问题库.md',questions),('04-利益相关者资料与分工.md',stakeholders)]
    manifest=dict(sourceURL='https://fde-discovery-lab-67046.app.workbuddy.host/group-training?project=fsg-recruiting',
                  templateURL='https://fde-discovery-lab-67046.app.workbuddy.host/fde-flow.js',
                  templateFunction='renderCaseInformation',exportMode='平台公开字段与原有四份文档模板的等价Markdown导出',
                  sourceSnapshot='../evidence/original-materials-source.json',
                  sourceSHA256=hashlib.sha256(source_path.read_bytes()).hexdigest(),documents=[])
    for name,content in documents:
        write(output/name,'\n'.join(content))
        manifest['documents'].append(dict(file=name,sha256=hashlib.sha256((output/name).read_bytes()).hexdigest()))
    write(output/'manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    write(output/'README.md','# 项目原有资料（四份）\n\n这四份对应实验室页面“本案例可核对资料 · 4份”，而不是四篇官网背景文章。根据平台公开字段和页面原有文档模板，等价导出为Markdown；来源与SHA256见 [manifest.json](manifest.json)。未补造正式Brief、真实客户附件、原始业务日志或授权文件。\n\n'+ '\n'.join(f'- [{name[3:-3]}]({name})' for name,_ in documents)+'\n\n资料性质：公开业务方向 · 合成演练。实际业务附件仍需向客户索取。')
    print('Exported 45 interview records in MD / JSON / CSV and four platform materials')


if __name__=='__main__':main()
