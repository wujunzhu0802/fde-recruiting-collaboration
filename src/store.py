"""SQLite transactions for review, optimistic concurrency, idempotency and audit."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from .engine import Invalid, check, fingerprint


class Conflict(Exception):
    pass


class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY, body TEXT NOT NULL,
              result TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1, state TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS requests(key TEXT PRIMARY KEY, hash TEXT NOT NULL, review_id INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, at TEXT NOT NULL, actor TEXT NOT NULL,
              role TEXT NOT NULL, action TEXT NOT NULL, review_id INTEGER, detail TEXT NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def audit(self, db, actor, role, action, review_id, detail):
        db.execute('INSERT INTO audit(at,actor,role,action,review_id,detail) VALUES(?,?,?,?,?,?)',
                   (datetime.now(timezone.utc).isoformat(), actor, role, action, review_id,
                    json.dumps(detail, ensure_ascii=False)))

    def create(self, payload, key, actor, role):
        if role not in ('consultant', 'coordinator', 'quality'):
            raise PermissionError('此角色不能创建核对单')
        if not isinstance(key, str) or not key.strip() or len(key) > 128:
            raise Invalid('需要 1–128 字符的 Idempotency-Key')
        result = check(payload, role)
        digest = fingerprint(dict(payload=payload, actor=actor, role=role))
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT * FROM requests WHERE key=?', (key,)).fetchone()
            if existing:
                if existing['hash'] != digest:
                    raise Conflict('重复请求键对应不同内容或身份')
                return self._read(db, existing['review_id'])
            row = db.execute('INSERT INTO reviews(body,result,state) VALUES(?,?,?)',
                             (json.dumps(payload, ensure_ascii=False), json.dumps(result, ensure_ascii=False), result['status']))
            review_id = row.lastrowid
            db.execute('INSERT INTO requests VALUES(?,?,?)', (key, digest, review_id))
            self.audit(db, actor, role, 'create', review_id,
                       dict(source_hash=result['source_hash'], rule_version=result['rule_version']))
            return self._read(db, review_id)

    def _read(self, db, review_id):
        row = db.execute('SELECT * FROM reviews WHERE id=?', (review_id,)).fetchone()
        if not row:
            raise KeyError('核对单不存在')
        return dict(id=row['id'], revision=row['revision'], state=row['state'],
                    input=json.loads(row['body']), result=json.loads(row['result']))

    def review(self, review_id, revision, decision, note, actor, role):
        if role not in ('quality', 'client'):
            raise PermissionError('仅质量复核或客户岗位负责人可确认')
        if decision not in ('confirmed', 'returned') or not isinstance(note, str) or not note.strip():
            raise Invalid('需填写 confirmed/returned 及确认意见')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current = self._read(db, review_id)
            if current['revision'] != revision:
                raise Conflict('版本冲突，请重新读取核对单')
            if current['state'] in ('confirmed', 'returned'):
                raise Conflict('已处理；修改后应新建核对单')
            if decision == 'confirmed' and any(i['severity'] == 'blocker' for i in current['result']['issues']):
                raise Conflict('存在阻断问题，请修正后新建核对单')
            db.execute('UPDATE reviews SET state=?,revision=revision+1 WHERE id=?', (decision, review_id))
            self.audit(db, actor, role, decision, review_id, dict(note=note, previous_revision=revision))
            return self._read(db, review_id)

    def listing(self):
        with self.connect() as db:
            return [self._read(db, row['id']) for row in db.execute('SELECT id FROM reviews ORDER BY id DESC LIMIT 100')]

    def audits(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 200')]
