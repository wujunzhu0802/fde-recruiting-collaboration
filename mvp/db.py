import hashlib
import json
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return salt + ':' + digest


def verify(password, saved):
    return secrets.compare_digest(password_hash(password, saved.split(':')[0]), saved)


class Database:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        with self.connection() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS tenants(id TEXT PRIMARY KEY,name TEXT NOT NULL,plan TEXT NOT NULL DEFAULT 'basic');
            CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,
                tenant_id TEXT,role TEXT NOT NULL,tier TEXT NOT NULL DEFAULT 'basic',active INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS sessions(hash TEXT PRIMARY KEY,user_id TEXT NOT NULL,expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS wiki(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,title TEXT NOT NULL,
                body TEXT NOT NULL,tier TEXT NOT NULL,version INTEGER NOT NULL,tags TEXT NOT NULL,links TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,user_id TEXT NOT NULL,
                created REAL NOT NULL,question TEXT NOT NULL,result TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,created REAL NOT NULL,user_id TEXT,
                tenant_id TEXT,action TEXT NOT NULL,detail TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS login_attempts(key TEXT PRIMARY KEY,count INTEGER NOT NULL,reset REAL NOT NULL);
            ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def log(self, user, action, detail):
        with self.connection() as db:
            db.execute('INSERT INTO audit(created,user_id,tenant_id,action,detail) VALUES(?,?,?,?,?)',
                       (time.time(), user.get('id'), user.get('tenant_id'), action, json.dumps(detail, ensure_ascii=False)))

    def seed(self, tenant_id):
        pages = [
            ('brief', '岗位需求澄清与条件分类', '岗位简报必须分别列出必备条件、偏好条件和待澄清事项。证书偏好不能自动转成硬性要求。每项条件保留原文来源、版本和客户确认人。未确认时退回招聘顾问，不能自动排除或录用候选人。', 'basic', ['岗位需求','条件分类','人工确认'], []),
            ('version', '需求版本与面试反馈', '客户取消证书偏好后，应登记变更，保留原版本及原因。面试反馈必须关联当时生效的需求版本与条件编号。旧反馈不可覆盖已确认的新版本，版本不一致时暂停交接并由客户岗位负责人核对。', 'basic', ['版本管理','面试反馈'], ['brief']),
            ('schedule', '面试安排与冲突处理', '协调员收集面试官和候选人的时间。同一面试官时间重叠时须人工协调，首尾相接允许。交接清单必须有最新版本、未结项、接收人和截止时间。资料不全时不得只回复已处理。', 'basic', ['排期','交接'], ['brief','version']),
            ('quality', '质量复核与正式上线条件', '质量负责人核对来源完整性、资料授权用途和人工复核记录。真实上线必须经过业务、技术与质量三方批准。工程测试与虚拟访谈不能代替真实用户UAT；任何自动录用或自动筛除行为都不在本项目范围。', 'basic', ['质量','验收','人工确认'], ['version']),
            ('roi', '试点成本与ROI方法（进阶）', '试点应按相同样本口径比较首次处理、返工和等待时长。运行费用、人工复核新增成本、采用率和节省工时兑现率都应计入ROI。实验室40份简报、120条安排和9小时返工仅为合成教学基线，不代表企业真实经营指标。', 'pro', ['ROI','试点','验收'], ['quality'])
        ]
        with self.connection() as db:
            for slug, title, body, tier, tags, links in pages:
                db.execute('INSERT INTO wiki VALUES(?,?,?,?,?,?,?,?)', (tenant_id+'-'+slug,tenant_id,title,body,tier,1,
                    json.dumps(tags,ensure_ascii=False),json.dumps([tenant_id+'-'+x for x in links])))

    def bootstrap(self):
        email = os.getenv('MVP_ADMIN_EMAIL', 'admin@recruiting.local')
        password = os.getenv('MVP_ADMIN_PASSWORD')
        with self.connection() as db:
            if db.execute("SELECT 1 FROM users WHERE role='saas_admin'").fetchone():
                return
            password = password or secrets.token_urlsafe(24)
            db.execute('INSERT INTO users VALUES(?,?,?,?,?,?,1)',
                       (secrets.token_hex(12),email,password_hash(password),None,'saas_admin','pro'))
        # Local-only initial credential, excluded from Git and never served over HTTP.
        destination = Path(self.path).parent/'admin-credentials.txt'
        destination.write_text('email='+email+'\npassword='+password+'\n',encoding='utf8')
