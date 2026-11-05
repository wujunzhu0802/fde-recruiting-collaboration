"""Draw editable SVG and PNG process diagrams, including explicit decisions."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'diagrams'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    nodes = [
        ('开始：客户提出岗位需求', '客户 / 招聘顾问', False),
        ('访谈并整理岗位需求简报', '林亦舟 · 招聘与用工服务顾问', False),
        ('信息完整，且必备 / 偏好明确？', '判断 1 · 招聘顾问', True),
        ('客户确认需求、用途和版本', '叶书 · 客户岗位负责人', False),
        ('客户已正式确认？', '判断 2 · 客户岗位负责人', True),
        ('按确认版本整理候选材料', '招聘顾问 · 人工处理', False),
        ('需求是否发生变更？', '判断 3 · 招聘顾问 / 客户', True),
        ('收集时间并拟定面试安排', '唐映秋 · 排期与培训协调员', False),
        ('排期是否有冲突？', '判断 4 · 协调员', True),
        ('人工确认安排并组织面试', '协调员 / 面试官', False),
        ('填写面试反馈与证据位置', '面试官', False),
        ('反馈完整且版本正确？', '判断 5 · 质量复核', True),
        ('质量与客户复核', '傅景 / 叶书', False),
        ('复核通过？', '判断 6 · 质量与客户', True),
        ('归档：版本、反馈与交接责任', '协调员 / 资料负责人', False),
        ('结束：资料交接完成', '录用由人工另行决策', False),
    ]
    w,h=1480,2600
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
         '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#426d60"/></marker></defs>',
         '<rect width="100%" height="100%" fill="#f4f7f3"/>',
         '<g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif">',
         '<text x="60" y="64" font-size="29" fill="#193e32" font-weight="bold">招聘需求澄清与面试协同</text>',
         '<text x="60" y="100" font-size="17" fill="#5c7468">现状业务流程 · 不引入 AI · 含判断、退回与变更分支</text>',
         '<text x="60" y="130" font-size="13" fill="#718278">依据：FDE 实验室六角色合成访谈；非企业真实制度。矩形＝人工处理，菱形＝判断。</text>']

    def text(x,y,s,size=17,color='#244d3d',weight='normal'):
        svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(s)}</text>')

    def line(points,label=None,lx=None,ly=None):
        svg.append(f'<polyline points="{points}" fill="none" stroke="#426d60" stroke-width="2" marker-end="url(#arrow)"/>')
        if label: text(lx,ly,label,14)

    centers=[]
    for i,(label,owner,decision) in enumerate(nodes):
        y=220+i*145;centers.append(y)
        if decision:
            svg.append(f'<polygon points="640,{y-53} 862,{y} 640,{y+53} 418,{y}" fill="#fff5da" stroke="#b59c57" stroke-width="1.5"/>')
        else:
            svg.append(f'<rect x="420" y="{y-40}" width="440" height="80" rx="{25 if i in (0,15) else 8}" fill="#ffffff" stroke="#afc5b5" stroke-width="1.5"/>')
        text(640,y-4,label,17,weight='bold');text(640,y+22,owner,12,'#728477')
        if i:
            prev=centers[i-1]; prev_d=nodes[i-1][2]
            label_path = {2:'是',4:'是',6:'否',8:'否',11:'是',13:'是'}.get(i-1)
            line(f'640,{prev+(53 if prev_d else 40)} 640,{y-(53 if decision else 40)}',label_path,663,(prev+y)//2+5)
    # Right-hand return loops at different x positions to avoid node overlap.
    branches=[(2,1,'否','追问缺项，明确条件',1010),
              (4,1,'否','返回客户澄清',1130),
              (6,1,'是','登记变更并保留旧版',1210),
              (8,7,'是','人工协调并重新约定',1020),
              (11,10,'否','退回补充并核对版本',1020),
              (13,10,'否','记录问题，退回反馈',1150)]
    for source,target,answer,label,x in branches:
        y=centers[source];ty=centers[target]
        line(f'862,{y} {x},{y} {x},{ty} 860,{ty}',answer,900,y-9)
        # Branch label placed along its vertical outer edge, two lines.
        mid=(y+ty)//2
        svg.append(f'<rect x="{x-145}" y="{mid-18}" width="290" height="27" fill="#f4f7f3"/>')
        text(x-3,mid,label,12,'#84682c')
    text(640,2530,'交接必须保留：最新版本 / 来源位置 / 未结事项 / 接收人 / 截止时间',16)
    text(640,2564,'数据为合成演练材料；本图不包含自动候选人筛选、排名或录用。',13,'#728477')
    svg.append('</g></svg>')
    (OUT/'as-is-no-ai.svg').write_text('\n'.join(svg),encoding='utf8')
    try:
        import cairosvg
        cairosvg.svg2png(url=str(OUT/'as-is-no-ai.svg'),write_to=str(OUT/'as-is-no-ai.png'))
        print('SVG + PNG generated')
    except (ImportError,OSError) as e:
        print('SVG generated; PNG renderer unavailable:',str(e)[:160])


if __name__=='__main__':main()
