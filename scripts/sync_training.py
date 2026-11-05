"""Save authored task conclusions; never invent gate approvals or client signoff."""
import json
import os
from pathlib import Path
from http.cookiejar import MozillaCookieJar
import requests

ROOT=Path(__file__).resolve().parents[1]
BASE='https://fde-discovery-lab-67046.app.workbuddy.host'


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf8')
    jar=MozillaCookieJar(str(Path(os.environ['TEMP'])/'recruiting-cookies.txt'));jar.load(ignore_discard=True,ignore_expires=True)
    s=requests.Session();s.cookies.update(jar)
    provenance=json.loads((ROOT/'docs/evidence/provenance.json').read_text(encoding='utf8'))
    p=dict(projectId='fsg-recruiting',attemptId=provenance['attemptId'])
    records=json.loads((ROOT/'docs/task-records.json').read_text(encoding='utf8'))
    r=s.get(BASE+'/api/projects/state',params=p,timeout=60);r.raise_for_status()
    current=r.json()['attempt']['flow'].get('steps',{})
    saved=[]
    for record in records:
        actual=current.get(record['stepId'],{})
        if not all(actual.get(k)==record[k] for k in ('notes','status','owner','evidence')):
            for retry in range(3):
                try:
                    r=s.post(BASE+'/api/projects/flow-step',json={**p,**record},timeout=60)
                    r.raise_for_status();d=r.json()
                    actual=d['attempt']['flow']['steps'][record['stepId']]
                    break
                except requests.RequestException:
                    if retry==2:raise
        assert actual['notes']==record['notes']
        saved.append(dict(stepId=record['stepId'],status=actual['status']))
        print('saved',record['stepId'],actual['status'],flush=True)
    r=s.get(BASE+'/api/projects/state',params=p,timeout=40);r.raise_for_status();d=r.json()
    assert len(d['attempt']['flow']['steps'])==27
    out=dict(projectId=p['projectId'],attemptId=p['attemptId'],saved=saved,
             flow=d['attempt']['flow'],gate_approvals_invented=False,
             note='未执行真实客户验收与签收的四项任务保持进行中；未将任何阶段关卡伪造为通过。')
    (ROOT/'docs/evidence/training-sync.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print('DONE',len(saved),'task conclusions verified',flush=True)


if __name__=='__main__':main()
