"""Public HTTPS smoke test with disposable synthetic org and no recorded secrets."""
import json
import secrets
import sys
from datetime import datetime,timezone
from pathlib import Path
import httpx

url=sys.argv[1].rstrip('/')
root=Path(__file__).resolve().parents[1]
checks=[]
with httpx.Client(base_url=url,timeout=25,follow_redirects=True) as c:
    for path in ('/','/assets/app.js','/assets/style.css','/api/health','/docs','/openapi.json'):
        r=c.get(path);assert r.status_code==200,(path,r.status_code)
        checks.append(dict(path=path,status=r.status_code))
    r=c.get('/api/wiki');assert r.status_code==401
    checks.append(dict(path='unauthenticated wiki',status=r.status_code))
    password=secrets.token_urlsafe(22);email='smoke-'+secrets.token_hex(5)+'@example.test'
    r=c.post('/api/signup',json=dict(email=email,password=password,organization='MVP公网验证（合成）'),headers={'Origin':url})
    assert r.status_code==201,r.text
    token=r.json()['token'];h={'Authorization':'Bearer '+token}
    checks.append(dict(path='signup isolated organization',status=r.status_code))
    r=c.get('/api/wiki',headers=h);assert r.status_code==200 and len(r.json())==4
    checks.append(dict(path='authorized basic wiki',status=r.status_code,pages=len(r.json())))
    r=c.post('/api/ask',json={'question':'证书偏好取消后如何处理旧版面试反馈？'},headers=h)
    assert r.status_code==200 and r.json()['sources'],r.text
    checks.append(dict(path='RAG with citations',status=r.status_code,mode=r.json()['mode'],sources=len(r.json()['sources'])))
    r=c.get('/api/graph',headers=h);assert r.status_code==200 and r.json()['nodes']
    checks.append(dict(path='authorized knowledge graph',status=r.status_code,nodes=len(r.json()['nodes'])))
    r=c.get('/api/admin/tenants',headers=h);assert r.status_code==403
    checks.append(dict(path='tenant owner cannot access SaaS admin',status=r.status_code))
    c.post('/api/logout',json={},headers=h)
    r=c.get('/api/wiki',headers=h);assert r.status_code==401
    checks.append(dict(path='logout revocation',status=r.status_code))
report=dict(url=url,api_docs=url+'/docs',health=url+'/api/health',verified_at=datetime.now(timezone.utc).isoformat(),
            temporary=True,depends_on_local_process=True,llm_configured=False,
            deployment='Real FastAPI/Uvicorn backend, Cloudflare Quick Tunnel HTTPS, synthetic-data demonstration',
            checks=checks,long_term_cloud_deployment=False,credentials_included=False)
(root/'docs/mvp-deployment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('Public HTTPS smoke checks passed:',len(checks))
