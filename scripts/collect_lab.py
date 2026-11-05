"""Collect virtual-role interviews via the lab's documented frontend API.

Cookie jar remains in TEMP, outside the public repository. No real patient data.
Run only for an explicitly authorized virtual training interview.
"""
import json
import os
import sys
from datetime import datetime, timezone
from http.cookiejar import MozillaCookieJar
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://fde-discovery-lab-67046.app.workbuddy.host'
PROJECT = 'fsg-recruiting'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    jar = MozillaCookieJar(str(Path(os.environ['TEMP']) / 'recruiting-cookies.txt'))
    jar.load(ignore_discard=True, ignore_expires=True)
    session = requests.Session()
    session.cookies.update(jar)
    active = json.loads((Path(os.environ['TEMP']) / 'recruiting-active.json').read_text(encoding='utf8'))
    attempt = active['attempt']['id']
    params = dict(projectId=PROJECT, moduleId=PROJECT, attemptId=attempt, stage='discovery')
    out = ROOT / 'docs' / 'evidence'
    out.mkdir(parents=True, exist_ok=True)

    def call(action, payload=None, scope='group-lab'):
        url = f'{BASE}/api/{scope}/{action}'
        response = session.get(url, params=params, timeout=120) if payload is None else session.post(url, params=params, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        if result.get('error'):
            raise RuntimeError(result['error'])
        for cookie in session.cookies:
            jar.set_cookie(cookie)
        jar.save(ignore_discard=True, ignore_expires=True)
        return result

    state = call('state')
    # Nurse first, then buyer, process, engineering, quality, downstream.
    roles = state['scenario']['characters']
    order = [roles[i] for i in [1, 0, 2, 3, 4, 5]]
    for role in order:
        for item in role['investigation']:
            question = item['question']
            # Exact topic prompt plus context; one focus per turn.
            question += ' 请结合岗位必备与偏好条件混写、面试反馈无法对照需求说明；没有记录支持的数字或授权请明确标为待核实。'
            if any(h['speaker'] == 'user' and h.get('characterId') == role['id'] and h['text'] == question for h in state['history']):
                continue
            try:
                state = call('ask', dict(scenarioId=PROJECT, characterId=role['id'], question=question))
            except Exception as exc:
                print('STOP', role['name'], item['topic'], str(exc), flush=True)
                raise
            (out / 'interviews.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf8')
            print(role['name'], item['topic'], 'facts', len(state['found']), flush=True)
    # Import only actual collected facts; imported evidence remains unverified.
    imported = call('import', {})
    (out / 'import-result.json').write_text(json.dumps(imported, ensure_ascii=False, indent=2), encoding='utf8')
    report = call('report')
    (out / 'lab-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    (out / 'provenance.json').write_text(json.dumps(dict(
        projectId=PROJECT, attemptId=attempt, collectedAt=datetime.now(timezone.utc).isoformat(),
        trainingUrl=BASE + '/group-training?project=' + PROJECT + '&attemptId=' + attempt,
        originalAttemptAccessible=False,
        source='原创合成案例；实际调用实验室在线虚拟角色，不代表真实企业访谈',
    ), ensure_ascii=False, indent=2), encoding='utf8')
    print('DONE', len(state['found']), '/', state['scenario']['total'], flush=True)


if __name__ == '__main__':
    main()
