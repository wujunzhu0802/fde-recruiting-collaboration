"""Reproducible unit, HTTP and local recovery evidence. No external writes."""
import hashlib
import http.client
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.server import build_handler
from src.store import Store


def main():
    results = []
    for repeat in range(3):
        p = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                           cwd=ROOT, capture_output=True, text=True, encoding='utf8', errors='replace')
        results.append(dict(repeat=repeat + 1, exit_code=p.returncode, log=p.stderr))
    assert all(r['exit_code'] == 0 for r in results), 'Unit regression failed'
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / 'demo.sqlite'
        store = Store(db_path)
        server = ThreadingHTTPServer(('127.0.0.1', 0), build_handler(store, 'test-session'))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
        checks = []

        def request(method, path, body=None, auth=True, role='consultant'):
            headers = {'Content-Type': 'application/json', 'X-Demo-Role': role, 'Idempotency-Key':'http-K'}
            if auth: headers['Authorization'] = 'Bearer test-session'
            conn.request(method, path, json.dumps(body) if body is not None else None, headers)
            r = conn.getresponse(); data = r.read()
            return r.status, data

        try:
            for path, expected in [('/api/health',200),('/',200),('/app.js',200),('/style.css',200),('/does-not-exist',404)]:
                status, _ = request('GET',path); assert status==expected
                checks.append(dict(path=path,status=status))
            status,_ = request('POST','/api/check',{},auth=False); assert status==401
            checks.append(dict(case='unauthenticated',status=status))
            status,_ = request('POST','/api/check',{'brief':{}},role='engineer'); assert status==403
            checks.append(dict(case='unauthorized role',status=status))
            payload = json.loads((ROOT/'examples'/'normal.json').read_text(encoding='utf8'))
            status,data = request('POST','/api/check',payload); assert status==200
            row = json.loads(data)
            status,data = request('POST','/api/review',dict(id=row['id'],revision=1,decision='confirmed',note='HTTP演练'),role='quality')
            assert status==200 and json.loads(data)['state']=='confirmed'
            checks.append(dict(case='HTTP end-to-end human review',status=status))
        finally:
            conn.close();server.shutdown();server.server_close();thread.join()
        # SQLite connections have closed. Back up a known-good data file, then restore it.
        backup = Path(tmp)/'known-good.sqlite';shutil.copy2(db_path, backup)
        store.create(dict(payload,adapter_mode='timeout'),'failure-K','A','consultant')
        before = len(store.listing())
        shutil.copy2(backup,db_path)
        restored = Store(db_path).listing()
        assert before == 2 and len(restored)==1 and restored[0]['state']=='confirmed'
        recovery = dict(mode='local synthetic database recovery',before_count=before,restored_count=len(restored),
                        restored_state=restored[0]['state'],result='passed',production_release=False)
    hashes = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in ('src','tests') for p in (ROOT/folder).rglob('*')
              if p.is_file() and '__pycache__' not in str(p)}
    out = ROOT/'docs'/'evidence';out.mkdir(parents=True,exist_ok=True)
    report = dict(at=datetime.now(timezone.utc).isoformat(),mode='local deterministic + synthetic interface stub',
                  repetitions=results,http_checks=checks,recovery=recovery,source_sha256=hashes,
                  skipped=['真实模型调用','真实企业系统集成','真实用户UAT','真实上线与真实收益核验'])
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS: 18 unit tests x 3; HTTP workflow; local rollback. Evidence: docs/evidence/verification.json')


if __name__ == '__main__': main()
