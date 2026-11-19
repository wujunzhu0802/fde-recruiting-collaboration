"""Harness regression runner; reports actual results, not fabricated model metrics."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path

root=Path(__file__).resolve().parents[1]
p=subprocess.run([sys.executable,'-m','unittest','mvp.test_mvp','-v'],cwd=root,capture_output=True,text=True,encoding='utf8',errors='replace')
report=dict(at=datetime.now(timezone.utc).isoformat(),exit_code=p.returncode,
            mode='FastAPI ASGI integration + SQLite + local TF-IDF RAG; provider success/failure use mocks',
            log=p.stdout+p.stderr,real_llm_executed=False,
            source_sha256={x.relative_to(root).as_posix():hashlib.sha256(x.read_bytes()).hexdigest()
                for x in (root/'mvp').rglob('*') if x.is_file() and x.suffix in ('.py','.html','.css','.js') and '__pycache__' not in x.parts})
(root/'docs/mvp-evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(report['log']);sys.exit(p.returncode)
