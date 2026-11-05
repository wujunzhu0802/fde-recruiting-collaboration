"""Editable three-phase AS-IS process board. No AI participates in this flow."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'diagrams'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="2080" height="1580" viewBox="0 0 2080 1580" role="img" aria-labelledby="title desc">',
           '<title id="title">招聘需求澄清与面试协同：不引入AI的现状流程</title>',
           '<desc id="desc">从左至右为需求澄清、面试协同、反馈闭环。六个菱形判断均有是与否分支，未通过时回到人工补充或协调。</desc>',
           '<defs><marker id="mainArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#3c7770"/></marker>',
           '<marker id="returnArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#c87554"/></marker></defs>',
           '<rect width="2080" height="1580" fill="#edf2f5"/>',
           '<g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif">']

    def rect(x,y,w,h,fill,stroke='none',r=12):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')

    def text(x,y,value,size=18,color='#243b4d',weight='normal',anchor='start'):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')

    def path(points,back=False):
        color = '#c87554' if back else '#3c7770'
        dash = 'stroke-dasharray="7 6"' if back else ''
        marker = 'returnArrow' if back else 'mainArrow'
        svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="{2.4 if back else 3}" stroke-linejoin="round" stroke-linecap="round" {dash} marker-end="url(#{marker})"/>')

    def badge(x,y,label,back=False):
        rect(x-18,y-15,36,29,'#fff0e7' if back else '#e0efea',r=7)
        text(x,y+5,label,16,'#aa5d3e' if back else '#296f60','bold','middle')

    def returned(points,label,x,y):
        path(points,True)
        svg.append(f'<text transform="translate({x} {y}) rotate(-90)" font-size="14" fill="#a95f43" text-anchor="middle" paint-order="stroke" stroke="#f8fafc" stroke-width="6" stroke-linejoin="round">{escape(label)}</text>')

    def node(x,y,title,owner,num,terminal=False):
        rect(x-170,y-43,340,86,'#e5f1ec' if terminal else '#ffffff','#c9d6df',r=28 if terminal else 13)
        if not terminal:
            rect(x-156,y-29,32,24,'#e9eff5',r=6)
            text(x-140,y-12,num,12,'#61788c','bold','middle')
        text(x+8,y-5,title,21,'#213d4e','bold','middle')
        text(x,y+23,owner,14,'#708594',anchor='middle')

    def decision(x,y,line1,line2,owner,num):
        svg.append(f'<g class="decision" id="decision-{num}">')
        svg.append(f'<polygon points="{x},{y-64} {x+180},{y} {x},{y+64} {x-180},{y}" fill="#fff5de" stroke="#d2b26c" stroke-width="1.5"/>')
        text(x,y-18,line1,19,'#70572a','bold','middle')
        text(x,y+7,line2,19,'#70572a','bold','middle')
        text(x,y+32,f'{num} / {owner}',12,'#9b865d',anchor='middle')
        svg.append('</g>')

    rect(60,48,142,29,'#173e52',r=6)
    text(78,69,'FDE / AS-IS',14,'#ffffff','bold')
    text(60,134,'招聘需求澄清与面试协同',42,'#173c51','bold')
    text(62,173,'先明确条件，再协同面试；让每一次确认和退回都有依据。',20,'#6a8292')
    rect(1710,58,310,46,'#dfece6',r=23)
    text(1865,88,'人工流程 · 不引入 AI',18,'#356d5d','bold','middle')
    text(1710,140,'版本 2.0  /  2026.11',14,'#788c9b')
    for x,n,label,sub in [(60,'03','业务阶段','从澄清到归档'),(450,'06','判断节点','每项均有回退分支'),(840,'06','协作角色','具名责任与人工确认')]:
        rect(x,208,365,72,'#ffffff',r=12)
        text(x+20,257,n,34,'#2e6c73','bold')
        text(x+92,239,label,18,'#334e61','bold')
        text(x+92,263,sub,13,'#8797a3')
    rect(1230,208,790,72,'#ffffff',r=12)
    svg.append('<rect x="1254" y="231" width="28" height="18" rx="4" fill="#ffffff" stroke="#b2c6d2"/>')
    text(1293,247,'人工处理',15,'#647d8e')
    svg.append('<polygon points="1410,227 1426,239 1410,251 1394,239" fill="#fff5de" stroke="#d2b26c"/>')
    text(1436,247,'业务判断',15,'#647d8e')
    path('1548,239 1588,239');text(1602,247,'主路径',15,'#647d8e')
    path('1715,239 1755,239',True);text(1769,247,'返工 / 变更',15,'#647d8e')
    phases=[(60,590,'01','需求澄清','客户 / 招聘顾问','#dce9f1','#466f92'),
            (710,590,'02','面试协同','招聘顾问 / 排期协调员','#e1e8f5','#697fa9'),
            (1360,660,'03','反馈闭环','面试官 / 质量 / 客户','#dceee8','#4d8c7a')]
    for x,w,num,title,roles,fill,accent in phases:
        rect(x,350,w,1050,'#f8fafc','#dae3ea',18)
        rect(x,350,w,74,fill,r=16)
        text(x+24,399,num,30,accent,'bold')
        text(x+90,385,title,23,'#29475c','bold')
        text(x+90,409,roles,13,'#71889b')
    # Draw edges before nodes to keep boundary intersections clean.
    for x,a,b,kind in [(355,480,610,'rr'),(355,610,765,'rd'),(355,765,920,'dr'),(355,920,1075,'rd'),(355,1075,1240,'dr'),
                       (1005,480,675,'dr'),(1005,675,850,'rd'),(1005,850,1040,'dr'),
                       (1665,480,655,'rd'),(1665,655,835,'dr'),(1665,835,1015,'rd'),(1665,1015,1195,'dr'),(1665,1195,1320,'rr')]:
        path(f'{x},{a+(64 if kind[0]=="d" else 43)} {x},{b-(64 if kind[1]=="d" else 43)}')
    path('525,1240 680,1240 680,480 825,480');badge(680,1158,'续')
    path('1175,1040 1330,1040 1330,480 1495,480');badge(1330,949,'续')
    returned('535,765 590,765 590,610 525,610','追问缺项，区分必备与偏好',603,686);badge(560,765,'否',True)
    returned('535,1075 632,1075 632,610 525,610','返回客户澄清',645,930);badge(560,1075,'否',True)
    path('1185,480 1250,480 1250,313 570,313 570,610 525,610',True)
    rect(743,295,360,34,'#edf2f5',r=9)
    text(923,318,'是 · 登记变更并保留旧版 → 重新澄清',15,'#ae6448',anchor='middle');badge(1210,480,'是',True)
    returned('1185,850 1276,850 1276,675 1175,675','人工协调并重新约定',1289,760);badge(1210,850,'是',True)
    returned('1845,655 1926,655 1926,480 1835,480','补充反馈 / 核对版本',1939,568);badge(1872,655,'否',True)
    returned('1845,1015 1992,1015 1992,480 1835,480','记录问题，退回反馈',2005,870);badge(1872,1015,'否',True)
    node(355,480,'客户提出岗位需求','起点 / 客户与招聘顾问','',True)
    node(355,610,'访谈并整理需求简报','林亦舟 · 招聘与用工服务顾问','01')
    decision(355,765,'岗位信息完整且','必备 / 偏好明确？','招聘顾问','D1')
    node(355,920,'确认需求、用途与版本','叶书 · 客户岗位负责人','02')
    decision(355,1075,'客户是否','正式确认？','客户岗位负责人','D2')
    node(355,1240,'按确认版本整理材料','招聘顾问 · 人工核对','03')
    decision(1005,480,'岗位需求是否','发生变更？','招聘顾问 / 客户','D3')
    node(1005,675,'收集时间，拟定面试安排','唐映秋 · 排期与培训协调员','04')
    decision(1005,850,'面试安排是否','存在时间冲突？','排期协调员','D4')
    node(1005,1040,'人工确认安排并组织面试','协调员 / 面试官','05')
    rect(750,1177,500,150,'#eef2f9',r=12)
    text(774,1209,'本阶段交接物',15,'#7081a2','bold')
    text(774,1245,'已确认版本 + 面试时间 + 参与人',20,'#465d7b','bold')
    text(774,1280,'发生变更或时间冲突时，先回到责任岗位确认。',14,'#8291a7')
    node(1665,480,'按岗位条件填写反馈','面试官 · 保留证据位置','06')
    decision(1665,655,'反馈完整且','关联正确版本？','质量复核','D5')
    node(1665,835,'质量与客户复核','傅景 / 叶书 · 人工确认','07')
    decision(1665,1015,'复核是否','通过？','质量与客户','D6')
    node(1665,1195,'归档版本、反馈与责任','唐映秋 · 资料接收与交接','08')
    node(1665,1320,'资料交接完成','终点 / 录用另由人工决策','',True)
    for x,y,label in [(355,852,'是'),(355,1164,'是'),(1005,578,'否'),(1005,948,'否'),(1665,747,'是'),(1665,1110,'是')]:
        badge(x+30,y,label)
    text(90,1360,'交接物：已确认岗位简报 / 条件分类 / 来源位置',14,'#71899b')
    rect(60,1430,1960,102,'#183e53',r=15)
    text(88,1467,'每次交接都要留下依据',21,'#ffffff','bold')
    text(88,1504,'最新版本   /   原文来源   /   未结事项   /   接收人   /   截止时间',18,'#c3d7e2')
    text(2000,1468,'资料性质：FDE 六角色合成训练',14,'#bdd1dc',anchor='end')
    text(2000,1503,'不自动筛选、排名或录用候选人；非企业正式制度。',14,'#bdd1dc',anchor='end')
    svg += ['</g>','</svg>']
    (OUT/'as-is-no-ai.svg').write_text('\n'.join(svg)+'\n',encoding='utf8')
    # Fully offline viewer: SVG is embedded, no network or file fetch required.
    html = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>招聘协同 · 现状流程图</title>
<style>*{box-sizing:border-box}body{margin:0;background:#eaf0f4;color:#203f52;font-family:Segoe UI,Microsoft YaHei,sans-serif}header{padding:18px 28px;background:#183e53;color:white;display:flex;align-items:center;justify-content:space-between;gap:16px}h1{font-size:18px;margin:0 0 5px}header p{font-size:12px;margin:0;color:#bed1de}.actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}button,a{font:inherit;font-size:13px;cursor:pointer;padding:9px 13px;border:1px solid #d1dce3;background:white;border-radius:7px;color:#315c70;text-decoration:none}button:hover,a:hover{background:#ecf4f4}button:focus-visible,a:focus-visible{outline:3px solid #e4b46b;outline-offset:3px}output{min-width:50px;text-align:center;color:white;font-size:13px}.hint{padding:12px 28px;font-size:12px;color:#6a8392;background:#f8fafb;border-bottom:1px solid #d7e2e9}#viewport{height:calc(100vh - 127px);overflow:auto;padding:24px;overscroll-behavior:contain}#diagram{display:block;max-width:none;height:auto;margin:auto}.emphasis .decision polygon{fill:#ffe2a3;stroke:#c58a32;stroke-width:3}@media(max-width:800px){header{align-items:flex-start;flex-direction:column}#viewport{height:calc(100vh - 185px)}.hint{padding:10px 18px}}</style></head><body>
<header><div><h1>招聘需求澄清与面试协同</h1><p>现状流程 / 不引入 AI / 合成训练材料</p></div><div class="actions"><button id="out" aria-label="缩小流程图">−</button><output id="percent" aria-live="polite"></output><button id="in" aria-label="放大流程图">＋</button><button id="fit">适应窗口</button><button id="focus" aria-pressed="false">突出判断点</button><button id="download">下载 SVG</button><a href="as-is-no-ai.png" download>下载 PNG</a></div></header>
<div class="hint">按 01 → 02 → 03 阅读；绿色实线为主路径，橙色虚线为返工与变更。可缩放后滚动查看。</div><main id="viewport" aria-label="可缩放流程图">__SVG__</main>
<script>const diagram=document.querySelector('svg');diagram.id='diagram';const viewport=document.getElementById('viewport');let scale=1;function zoom(value){scale=Math.max(.25,Math.min(2,value));diagram.style.width=(2080*scale)+'px';document.getElementById('percent').textContent=Math.round(scale*100)+'%';}function fit(){zoom((viewport.clientWidth-48)/2080);}document.getElementById('in').onclick=()=>zoom(scale+.15);document.getElementById('out').onclick=()=>zoom(scale-.15);document.getElementById('fit').onclick=fit;document.getElementById('focus').onclick=function(){const pressed=document.body.classList.toggle('emphasis');this.setAttribute('aria-pressed',String(pressed));};document.getElementById('download').onclick=()=>{const copy=diagram.cloneNode(true);copy.removeAttribute('id');copy.removeAttribute('style');const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(copy)],{type:'image/svg+xml;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='招聘协同-现状流程图.svg';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};fit();</script></body></html>'''
    (OUT/'as-is-no-ai.html').write_text(html.replace('__SVG__','\n'.join(svg)),encoding='utf8')
    print('Generated editable SVG: docs/diagrams/as-is-no-ai.svg')


if __name__ == '__main__':
    main()
