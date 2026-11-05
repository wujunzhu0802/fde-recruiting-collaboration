"""Local-only synthetic workbench. Run: python -m src.server"""
import argparse
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .engine import Invalid, VERSION
from .store import Conflict, Store

ROOT = Path(__file__).resolve().parents[1]


def build_handler(store, token):
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, body, content_type='application/json; charset=utf-8'):
            raw = json.dumps(body, ensure_ascii=False).encode() if isinstance(body, (dict, list)) else body
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/api/health':
                return self.send(200, dict(ok=True, version=VERSION, mode='synthetic-local'))
            if path == '/api/session':
                # Reject cross-origin script access. Token is local demo-only.
                return self.send(200, dict(token=token))
            if path in ('/api/reviews', '/api/audit'):
                if self.headers.get('Authorization') != 'Bearer ' + token:
                    return self.send(401, dict(error='请打开本地工作台'))
                return self.send(200, store.listing() if path.endswith('reviews') else store.audits())
            assets = {'/': ('index.html', 'text/html; charset=utf-8'),
                      '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                      '/style.css': ('style.css', 'text/css; charset=utf-8')}
            if path not in assets:
                return self.send(404, dict(error='不存在'))
            name, kind = assets[path]
            return self.send(200, (ROOT / 'src' / 'web' / name).read_bytes(), kind)

        def do_POST(self):
            # Local synthetic identity switch is not enterprise authentication.
            if self.headers.get('Authorization') != 'Bearer ' + token:
                return self.send(401, dict(error='会话无效'))
            if self.headers.get('Origin') not in (None, f'http://{self.headers.get("Host")}'):
                return self.send(403, dict(error='不允许跨源请求'))
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 65536:
                    raise Invalid('请求大小必须为 1–65536 字节')
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict):
                    raise Invalid('请求必须为对象')
                role = self.headers.get('X-Demo-Role', 'consultant')
                actor = 'demo-' + role
                path = urlsplit(self.path).path
                if path == '/api/check':
                    result = store.create(body, self.headers.get('Idempotency-Key'), actor, role)
                elif path == '/api/review':
                    result = store.review(body.get('id'), body.get('revision'), body.get('decision'), body.get('note'), actor, role)
                else:
                    return self.send(404, dict(error='不存在'))
                self.send(200, result)
            except PermissionError as exc:
                self.send(403, dict(error=str(exc)))
            except Conflict as exc:
                self.send(409, dict(error=str(exc)))
            except KeyError:
                self.send(404, dict(error='核对单不存在'))
            except (Invalid, ValueError, TypeError) as exc:
                self.send(400, dict(error=str(exc)))

        def log_message(self, fmt, *args):
            pass  # No request bodies or local session tokens in console logs.
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--db', default=str(ROOT / 'runtime' / 'demo.sqlite'))
    args = parser.parse_args()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), build_handler(Store(args.db), secrets.token_urlsafe(32)))
    print(f'招聘需求协同演练：http://127.0.0.1:{args.port} （仅本机、仅合成数据）', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
