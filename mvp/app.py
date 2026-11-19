import hashlib
import json
import os
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .db import Database, password_hash, verify
from .rag import run_harness

ROOT=Path(__file__).resolve().parent


class Input(BaseModel):
    model_config=ConfigDict(extra='forbid')


class Login(Input):
    email:str=Field(min_length=3,max_length=160)
    password:str=Field(min_length=10,max_length=128)


class Signup(Login):
    organization:str=Field(min_length=2,max_length=80)


class Wiki(Input):
    title:str=Field(min_length=2,max_length=150)
    body:str=Field(min_length=10,max_length=20000)
    tier:str='basic'
    tags:list[str]=Field(default_factory=list,max_length=12)
    links:list[str]=Field(default_factory=list,max_length=20)


class UpdateWiki(Wiki):
    version:int=Field(ge=1)


class Question(Input):
    question:str=Field(min_length=2,max_length=1500)


class CreateUser(Login):
    role:str='member'
    tier:str='basic'
    tenant_id:str|None=None


class TenantPlan(Input):
    plan:str


def create_app(db_path=None):
    database=Database(db_path or os.getenv('MVP_DB','runtime/mvp/data.sqlite'))
    @asynccontextmanager
    async def lifespan(app):
        database.bootstrap()
        yield
    app=FastAPI(title='需求有据 · 招聘知识 SaaS',version='2.0.0',lifespan=lifespan)
    app.state.db=database

    @app.middleware('http')
    async def origin_check(request,call_next):
        origin=request.headers.get('origin')
        if request.method not in ('GET','HEAD','OPTIONS') and origin and urlsplit(origin).netloc!=request.headers.get('host'):
            return Response(status_code=403,content='Cross-origin request denied')
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Cache-Control']='no-store'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'"
        if request.url.path in ('/docs','/redoc'):
            response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com; frame-ancestors 'none'"
        return response

    def current(request:Request):
        header=request.headers.get('authorization','')
        token=header[7:] if header.startswith('Bearer ') else request.cookies.get('mvp_session','')
        with database.connection() as db:
            row=db.execute('SELECT u.* FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.hash=? AND s.expires>? AND u.active=1',
                           (hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone()
        if not row:raise HTTPException(401,'请先登录')
        return {k:row[k] for k in row.keys() if k!='password'}

    def require(user,roles):
        if user['role'] not in roles:raise HTTPException(403,'当前角色没有此操作权限')

    def visible(user):
        with database.connection() as db:
            rows=db.execute('SELECT * FROM wiki WHERE tenant_id=? ORDER BY title',(user['tenant_id'],)).fetchall()
        return [dict(r) for r in rows if r['tier']=='basic' or user['tier']=='pro']

    def authenticated(user,response):
        token=secrets.token_urlsafe(40)
        with database.connection() as db:
            db.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user['id'],time.time()+28800))
        response.set_cookie('mvp_session',token,httponly=True,samesite='lax',secure=os.getenv('MVP_SECURE_COOKIES')=='1',max_age=28800)
        return dict(token=token,user={k:user[k] for k in ('id','email','tenant_id','role','tier')})

    @app.get('/api/health')
    def health():return dict(ok=True,version='2.0.0',framework='FastAPI',llm_configured=bool(os.getenv('MVP_LLM_API_KEY')))

    @app.post('/api/signup',status_code=201)
    def signup(body:Signup,response:Response):
        tenant=secrets.token_hex(10);uid=secrets.token_hex(12);email=body.email.lower().strip()
        with database.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM users WHERE email=?',(email,)).fetchone():raise HTTPException(409,'账号已存在')
            db.execute('INSERT INTO tenants VALUES(?,?,?)',(tenant,body.organization,'basic'))
            db.execute('INSERT INTO users VALUES(?,?,?,?,?,?,1)',(uid,email,password_hash(body.password),tenant,'tenant_admin','basic'))
        database.seed(tenant)
        user=dict(id=uid,email=email,tenant_id=tenant,role='tenant_admin',tier='basic')
        database.log(user,'signup',{})
        return authenticated(user,response)

    @app.post('/api/login')
    def login(body:Login,response:Response,request:Request):
        email=body.email.lower().strip();key=hashlib.sha256((email+'|'+request.client.host).encode()).hexdigest()
        with database.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            entry=db.execute('SELECT * FROM login_attempts WHERE key=?',(key,)).fetchone()
            if entry and entry['reset']>time.time() and entry['count']>=8:raise HTTPException(429,'尝试次数过多，请15分钟后重试')
            count=entry['count']+1 if entry and entry['reset']>time.time() else 1
            db.execute('INSERT OR REPLACE INTO login_attempts VALUES(?,?,?)',(key,count,time.time()+900))
            row=db.execute('SELECT * FROM users WHERE email=? AND active=1',(email,)).fetchone()
        if not row or not verify(body.password,row['password']):raise HTTPException(401,'账号或密码错误')
        with database.connection() as db:db.execute('DELETE FROM login_attempts WHERE key=?',(key,))
        return authenticated(dict(row),response)

    @app.post('/api/logout')
    def logout(request:Request,response:Response,user=Depends(current)):
        header=request.headers.get('authorization','');token=header[7:] if header.startswith('Bearer ') else request.cookies.get('mvp_session','')
        with database.connection() as db:db.execute('DELETE FROM sessions WHERE hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
        response.delete_cookie('mvp_session');return {'ok':True}

    @app.get('/api/me')
    def me(user=Depends(current)):return user

    @app.get('/api/wiki')
    def pages(user=Depends(current)):
        result=visible(user);database.log(user,'wiki.list',{'count':len(result)})
        return [dict(p,tags=json.loads(p['tags']),links=json.loads(p['links'])) for p in result]

    @app.post('/api/wiki',status_code=201)
    def add_page(body:Wiki,user=Depends(current)):
        require(user,['tenant_admin'])
        if body.tier not in ('basic','pro') or (body.tier=='pro' and user['tier']!='pro'):raise HTTPException(403,'无权创建此层级知识')
        if not set(body.links)<={p['id'] for p in visible(user)}:raise HTTPException(400,'关联页面不可访问')
        page_id=secrets.token_hex(12)
        with database.connection() as db:db.execute('INSERT INTO wiki VALUES(?,?,?,?,?,?,?,?)',(page_id,user['tenant_id'],body.title,body.body,body.tier,1,json.dumps(body.tags),json.dumps(body.links)))
        database.log(user,'wiki.create',{'id':page_id});return dict(id=page_id,version=1)

    @app.put('/api/wiki/{page_id}')
    def update_page(page_id:str,body:UpdateWiki,user=Depends(current)):
        require(user,['tenant_admin'])
        allowed={p['id']:p for p in visible(user)}
        if page_id not in allowed:raise HTTPException(404,'页面不存在')
        if body.tier not in ('basic','pro') or (body.tier=='pro' and user['tier']!='pro'):raise HTTPException(403,'层级不允许')
        if not set(body.links)<=set(allowed):raise HTTPException(400,'关联页面不可访问')
        with database.connection() as db:
            changed=db.execute('UPDATE wiki SET title=?,body=?,tier=?,version=version+1,tags=?,links=? WHERE id=? AND tenant_id=? AND version=?',
                (body.title,body.body,body.tier,json.dumps(body.tags),json.dumps(body.links),page_id,user['tenant_id'],body.version)).rowcount
            if not changed:raise HTTPException(409,'版本已变化，请重新读取')
        database.log(user,'wiki.update',{'id':page_id,'version':body.version+1});return dict(id=page_id,version=body.version+1)

    @app.get('/api/graph')
    def graph(user=Depends(current)):
        result=visible(user);ids={p['id'] for p in result};nodes=[];edges=[];tags=set()
        for p in result:
            nodes.append(dict(id=p['id'],label=p['title'],kind='wiki'))
            for tag in json.loads(p['tags']):
                tagid='tag:'+tag;tags.add(tag)
                edges.append(dict(source=p['id'],target=tagid,relation='主题'))
            for link in json.loads(p['links']):
                if link in ids:edges.append(dict(source=p['id'],target=link,relation='引用'))
        nodes.extend(dict(id='tag:'+t,label=t,kind='tag') for t in sorted(tags))
        database.log(user,'graph.read',{'pages':len(result)})
        return dict(nodes=nodes,edges=edges)

    @app.post('/api/ask')
    def ask(body:Question,user=Depends(current)):
        require(user,['tenant_admin','member'])
        limit=200 if user['tier']=='pro' else 20
        # Reserve quota transactionally before model execution, including concurrent requests.
        run_id=secrets.token_hex(16)
        with database.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            count=db.execute('SELECT count(*) FROM runs WHERE user_id=? AND created>?',(user['id'],time.time()-86400)).fetchone()[0]
            if count>=limit:raise HTTPException(429,'已达到24小时问答额度')
            db.execute('INSERT INTO runs VALUES(?,?,?,?,?,?)',(run_id,user['tenant_id'],user['id'],time.time(),body.question,'{}'))
        result=run_harness(body.question,visible(user));result['id']=run_id
        with database.connection() as db:db.execute('UPDATE runs SET result=? WHERE id=?',(json.dumps(result,ensure_ascii=False),run_id))
        database.log(user,'harness.run',dict(run_id=run_id,mode=result['mode']))
        return result

    @app.get('/api/runs')
    def runs(user=Depends(current)):
        with database.connection() as db:
            if user['role']=='tenant_admin':rows=db.execute('SELECT * FROM runs WHERE tenant_id=? ORDER BY created DESC LIMIT 30',(user['tenant_id'],)).fetchall()
            else:rows=db.execute('SELECT * FROM runs WHERE user_id=? ORDER BY created DESC LIMIT 30',(user['id'],)).fetchall()
        return [dict(id=r['id'],created=r['created'],question=r['question'],result=json.loads(r['result'])) for r in rows]

    @app.get('/api/users')
    def users(user=Depends(current)):
        require(user,['saas_admin','tenant_admin'])
        with database.connection() as db:
            rows=db.execute('SELECT id,email,tenant_id,role,tier,active FROM users WHERE tenant_id=?',(user['tenant_id'],)).fetchall() if user['role']=='tenant_admin' else db.execute('SELECT id,email,tenant_id,role,tier,active FROM users').fetchall()
        return [dict(r) for r in rows]

    @app.post('/api/users',status_code=201)
    def add_user(body:CreateUser,user=Depends(current)):
        require(user,['saas_admin','tenant_admin'])
        tenant=body.tenant_id if user['role']=='saas_admin' else user['tenant_id']
        if body.role not in ('tenant_admin','member','viewer') or body.tier not in ('basic','pro'):raise HTTPException(400,'角色或层级无效')
        with database.connection() as db:
            t=db.execute('SELECT * FROM tenants WHERE id=?',(tenant,)).fetchone()
            if not t:raise HTTPException(400,'租户不存在')
            if user['role']=='tenant_admin' and (body.tenant_id not in (None,user['tenant_id']) or (body.tier=='pro' and t['plan']!='pro')):raise HTTPException(403,'不能越租户或升级订阅')
            if db.execute('SELECT 1 FROM users WHERE email=?',(body.email.lower(),)).fetchone():raise HTTPException(409,'账号已存在')
            uid=secrets.token_hex(12)
            db.execute('INSERT INTO users VALUES(?,?,?,?,?,?,1)',(uid,body.email.lower(),password_hash(body.password),tenant,body.role,body.tier))
        database.log(user,'user.create',{'id':uid,'role':body.role,'tier':body.tier});return dict(id=uid)

    @app.get('/api/admin/tenants')
    def tenants(user=Depends(current)):
        require(user,['saas_admin'])
        with database.connection() as db:return [dict(r) for r in db.execute('SELECT * FROM tenants')]

    @app.put('/api/admin/tenants/{tenant_id}/plan')
    def plan(tenant_id:str,body:TenantPlan,user=Depends(current)):
        require(user,['saas_admin'])
        if body.plan not in ('basic','pro'):raise HTTPException(400,'订阅无效')
        with database.connection() as db:
            if not db.execute('UPDATE tenants SET plan=? WHERE id=?',(body.plan,tenant_id)).rowcount:raise HTTPException(404,'租户不存在')
            db.execute('UPDATE users SET tier=? WHERE tenant_id=? AND role=?',(body.plan,tenant_id,'tenant_admin'))
            if body.plan=='basic':db.execute('UPDATE users SET tier=? WHERE tenant_id=?',('basic',tenant_id))
        database.log(user,'tenant.plan',{'tenant_id':tenant_id,'plan':body.plan});return {'ok':True}

    @app.get('/api/audit')
    def audit(user=Depends(current)):
        require(user,['tenant_admin','saas_admin'])
        with database.connection() as db:
            rows=db.execute('SELECT * FROM audit WHERE tenant_id=? ORDER BY id DESC LIMIT 100',(user['tenant_id'],)).fetchall() if user['role']=='tenant_admin' else db.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 100').fetchall()
        return [dict(r) for r in rows]

    app.mount('/assets',StaticFiles(directory=ROOT/'web'),name='assets')
    @app.get('/')
    def index():return FileResponse(ROOT/'web/index.html')
    return app


app=create_app()
