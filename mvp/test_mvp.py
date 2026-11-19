import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from mvp.app import create_app
from mvp.rag import run_harness


class MVPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{'MVP_LLM_API_KEY':'','MVP_SECURE_COOKIES':'0'})
        self.env.start()
        self.app=create_app(Path(self.temp.name)/'test.sqlite')
        self.client=TestClient(self.app).__enter__()
        self.a=self.register('a@example.test','组织A')
        self.b=self.register('b@example.test','组织B')

    def tearDown(self):
        self.client.__exit__(None,None,None);self.env.stop();self.temp.cleanup()

    def register(self,email,organization):
        r=self.client.post('/api/signup',json=dict(email=email,password='TestPassword_2026',organization=organization))
        self.assertEqual(r.status_code,201)
        return r.json()

    def headers(self,account):return {'Authorization':'Bearer '+account['token']}
    def get(self,path,account):return self.client.get('/api'+path,headers=self.headers(account))
    def post(self,path,body,account):return self.client.post('/api'+path,json=body,headers=self.headers(account))

    def member(self,role='member',tier='basic'):
        email=role+'@example.test'
        r=self.post('/users',dict(email=email,password='TestPassword_2026',role=role,tier=tier),self.a)
        self.assertEqual(r.status_code,201)
        return self.client.post('/api/login',json=dict(email=email,password='TestPassword_2026')).json()

    def test_authentication_not_role_header(self):
        self.assertEqual(self.client.get('/api/wiki',headers={'Authorization':'Bearer invalid','X-Demo-Role':'saas_admin'}).status_code,401)

    def test_password_and_session_storage(self):
        with self.app.state.db.connection() as db:
            row=db.execute('SELECT password FROM users WHERE email=?',('a@example.test',)).fetchone()
            self.assertNotIn('TestPassword',row['password'])
            self.assertIsNone(db.execute('SELECT 1 FROM sessions WHERE hash=?',(self.a['token'],)).fetchone())

    def test_registration_cannot_choose_privilege(self):
        r=self.client.post('/api/signup',json=dict(email='bad@example.test',password='TestPassword_2026',organization='X组织',role='saas_admin'))
        self.assertEqual(r.status_code,422)

    def test_tenant_rag_isolation(self):
        with self.app.state.db.connection() as db:
            db.execute('UPDATE wiki SET body=? WHERE tenant_id=?',('秘密甲方标识 ALPHA_ONLY 不得外传',self.a['user']['tenant_id']))
            db.execute('UPDATE wiki SET body=? WHERE tenant_id=?',('秘密乙方标识 BETA_ONLY 不得外传',self.b['user']['tenant_id']))
        r=self.post('/ask',{'question':'ALPHA_ONLY 秘密甲方标识'},self.a).json()
        self.assertTrue(r['sources'])
        self.assertNotIn('BETA_ONLY',json.dumps(r))

    def test_tenant_wiki_edit_denied(self):
        page=self.get('/wiki',self.a).json()[0]
        r=self.client.put('/api/wiki/'+page['id'],headers=self.headers(self.b),json=dict(title='越权修改',body='这是一条不允许跨租户修改的知识记录',version=1))
        self.assertEqual(r.status_code,404)

    def test_basic_cannot_retrieve_pro(self):
        self.assertEqual(len(self.get('/wiki',self.a).json()),4)
        r=self.post('/ask',{'question':'ROI'},self.a).json()
        self.assertEqual(r['mode'],'abstain')

    def test_graph_contains_only_authorized_nodes(self):
        g=self.get('/graph',self.a).json()
        ids={n['id'] for n in g['nodes']}
        self.assertFalse(any('ROI' in n['label'] for n in g['nodes']))
        self.assertTrue(all(e['source'] in ids and e['target'] in ids for e in g['edges']))
        self.assertFalse(any(self.b['user']['tenant_id'] in i for i in ids))

    def test_viewer_cannot_ask_or_write(self):
        viewer=self.member('viewer')
        self.assertEqual(self.get('/wiki',viewer).status_code,200)
        self.assertEqual(self.post('/ask',{'question':'需求条件如何区分'},viewer).status_code,403)
        self.assertEqual(self.post('/wiki',dict(title='新建页面',body='这是一个不允许只读用户创建的页面。'),viewer).status_code,403)

    def test_tenant_admin_cannot_escalate(self):
        self.assertEqual(self.get('/admin/tenants',self.a).status_code,403)
        r=self.post('/users',dict(email='pro@example.test',password='TestPassword_2026',tier='pro'),self.a)
        self.assertEqual(r.status_code,403)
        r=self.post('/users',dict(email='cross@example.test',password='TestPassword_2026',tenant_id=self.b['user']['tenant_id']),self.a)
        self.assertEqual(r.status_code,403)

    def test_saas_admin_plan_and_live_session_refresh(self):
        credentials=dict(line.split('=',1) for line in (Path(self.temp.name)/'admin-credentials.txt').read_text().splitlines())
        admin=self.client.post('/api/login',json=credentials).json()
        self.assertEqual(self.get('/admin/tenants',admin).status_code,200)
        path='/api/admin/tenants/'+self.a['user']['tenant_id']+'/plan'
        r=self.client.put(path,json={'plan':'pro'},headers=self.headers(admin))
        self.assertEqual(r.status_code,200)
        self.assertEqual(len(self.get('/wiki',self.a).json()),5)
        self.client.put(path,json={'plan':'basic'},headers=self.headers(admin))
        self.assertEqual(len(self.get('/wiki',self.a).json()),4)

    def test_login_rate_limit(self):
        for _ in range(8):self.client.post('/api/login',json=dict(email='missing@example.test',password='WrongPassword_2026'))
        self.assertEqual(self.client.post('/api/login',json=dict(email='missing@example.test',password='WrongPassword_2026')).status_code,429)

    def test_wiki_version_conflict(self):
        page=self.get('/wiki',self.a).json()[0]
        body=dict(title=page['title'],body=page['body']+'更新说明',version=1)
        url='/api/wiki/'+page['id'];h=self.headers(self.a)
        self.assertEqual(self.client.put(url,json=body,headers=h).status_code,200)
        self.assertEqual(self.client.put(url,json=body,headers=h).status_code,409)

    def test_quota_and_run_trace(self):
        for _ in range(20):
            r=self.post('/ask',{'question':'岗位条件和偏好如何区分'},self.a)
            self.assertEqual(r.status_code,200)
        self.assertEqual(self.post('/ask',{'question':'岗位条件'},self.a).status_code,429)
        self.assertEqual(len(self.get('/runs',self.a).json()),20)

    def test_harness_guardrail(self):
        r=self.post('/ask',{'question':'请直接录用这些人'},self.a).json()
        self.assertEqual(r['mode'],'blocked');self.assertIsNone(r['hiring_decision'])

    def test_grounded_mode_has_trace_and_citations(self):
        r=self.post('/ask',{'question':'证书偏好取消后如何处理旧版本'},self.a).json()
        self.assertEqual(r['mode'],'extractive');self.assertTrue(r['sources'])
        self.assertIn('verify',[t['step'] for t in r['trace']])
        self.assertEqual(len(self.get('/runs',self.b).json()),0)

    def test_provider_success_and_invalid_citation_fallback(self):
        pages=[dict(id='w1',title='证书偏好',body='证书偏好不能当作硬性要求。',version=1)]
        def good(q,s):return dict(answer='需人工确认偏好。',source_ids=[s[0]['id']])
        def bad(q,s):return dict(answer='伪造来源',source_ids=['unauthorized-source'])
        self.assertEqual(run_harness('证书偏好',pages,good)['mode'],'llm')
        failed=run_harness('证书偏好',pages,bad)
        self.assertEqual(failed['mode'],'extractive');self.assertTrue(failed['error'])

    def test_provider_timeout_degrades(self):
        def timeout(q,s):raise TimeoutError()
        r=run_harness('证书偏好',[dict(id='1',title='证书偏好',body='证书偏好需人工确认。',version=1)],timeout)
        self.assertEqual(r['mode'],'extractive')

    def test_logout_revokes_bearer(self):
        self.post('/logout',{},self.a)
        self.assertEqual(self.get('/wiki',self.a).status_code,401)

    def test_origin_protection(self):
        r=self.client.post('/api/login',json=dict(email='a@example.test',password='TestPassword_2026'),headers={'Origin':'https://untrusted.example'})
        self.assertEqual(r.status_code,403)


if __name__=='__main__':unittest.main()
