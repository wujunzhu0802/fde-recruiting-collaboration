"""Deterministic checks. No candidate ranking or hiring decisions."""
from datetime import datetime, timezone
import hashlib
import json

VERSION = '1.0.0'
RULE_VERSION = 'recruiting-rules-1'
REQUIRED = ('job_id', 'version', 'owner', 'location', 'headcount', 'conditions', 'source_id')
ROLES = {'consultant', 'coordinator', 'quality', 'client', 'engineer'}


class Invalid(ValueError):
    pass


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def check(payload, role='consultant'):
    if role not in ROLES:
        raise PermissionError('未知角色')
    if not isinstance(payload, dict):
        raise Invalid('请求必须是 JSON 对象')
    # No raw resume or candidate personal information is accepted by this demo.
    if set(payload) - {'brief', 'feedback', 'schedule', 'adapter_mode', 'model_mode'}:
        raise Invalid('存在契约外字段；请勿提交候选人个人信息')
    brief = payload.get('brief')
    if not isinstance(brief, dict):
        raise Invalid('brief 必须为对象')
    issues = []

    def issue(code, field, message, severity='blocker', source=None):
        issues.append(dict(code=code, field=field, message=message, severity=severity,
                           source=source or brief.get('source_id', 'missing-source')))

    for key in REQUIRED:
        if key not in brief or brief[key] in (None, '', []):
            issue('MISSING', 'brief.' + key, '缺少必填字段 ' + key)
    if not isinstance(brief.get('version'), int) or isinstance(brief.get('version'), bool) or brief['version'] < 1:
        issue('INVALID_VERSION', 'brief.version', '版本必须是正整数')
    if not isinstance(brief.get('headcount'), int) or isinstance(brief.get('headcount'), bool) or brief['headcount'] < 1:
        issue('INVALID_HEADCOUNT', 'brief.headcount', '人数必须为正整数')
    conditions = brief.get('conditions', [])
    if not isinstance(conditions, list):
        raise Invalid('conditions 必须为数组')
    ids = set()
    for i, condition in enumerate(conditions):
        if not isinstance(condition, dict):
            raise Invalid('每项条件必须为对象')
        field = f'brief.conditions[{i}]'
        if not condition.get('id') or not isinstance(condition.get('id'), str) or condition['id'] in ids:
            issue('CONDITION_ID', field + '.id', '条件 ID 缺失或重复')
        ids.add(condition.get('id'))
        if condition.get('kind') not in ('must', 'preferred', 'clarify'):
            issue('AMBIGUOUS', field + '.kind', '必须由岗位负责人明确必备、偏好或待澄清')
        if condition.get('kind') == 'clarify':
            issue('NEEDS_CLARIFICATION', field + '.kind', '条件分类待客户确认')
        if not condition.get('text') or not isinstance(condition.get('text'), str):
            issue('MISSING', field + '.text', '缺少条件原文')
        if not condition.get('source'):
            issue('NO_SOURCE', field + '.source', '缺少页码或原文位置')
    feedback = payload.get('feedback', [])
    if not isinstance(feedback, list):
        raise Invalid('feedback 必须为数组')
    for i, item in enumerate(feedback):
        if not isinstance(item, dict):
            raise Invalid('反馈项必须为对象')
        field = f'feedback[{i}]'
        if item.get('brief_version') != brief.get('version'):
            issue('STALE_VERSION', field, '反馈引用旧岗位版本，转人工核对')
        if item.get('condition_id') not in ids:
            issue('UNKNOWN_CONDITION', field, '反馈未对齐当前岗位条件')
        if not item.get('evidence_ref'):
            issue('NO_SOURCE', field, '反馈缺少访谈记录位置')
    # Schedule checks are read-only; no invitations are sent.
    schedule = payload.get('schedule', [])
    if not isinstance(schedule, list):
        raise Invalid('schedule 必须为数组')
    intervals = []
    for i, item in enumerate(schedule):
        if not isinstance(item, dict):
            raise Invalid('排期项必须为对象')
        try:
            start, end = (datetime.fromisoformat(item[key]) for key in ('start', 'end'))
            if start.tzinfo is None or end.tzinfo is None or end <= start or not item.get('interviewer_id'):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            issue('INVALID_TIME', f'schedule[{i}]', '排期需具备时区、面试官代号且结束晚于开始')
            continue
        for other, other_start, other_end in intervals:
            if other['interviewer_id'] == item['interviewer_id'] and start < other_end and other_start < end:
                issue('SCHEDULE_CONFLICT', f'schedule[{i}]', '同一面试官排期重叠，需协调员处理')
        intervals.append((item, start, end))
    mode = payload.get('adapter_mode', 'stub')
    if mode not in ('stub', 'timeout', 'unavailable'):
        raise Invalid('不支持的接口模式')
    if mode != 'stub':
        issue('UPSTREAM_' + mode.upper(), 'adapter', '停止读取，转系统工程师与协调员')
    if payload.get('model_mode', 'disabled') not in ('disabled', 'stub'):
        raise Invalid('本版本未接真实模型，仅支持 disabled/stub')
    return dict(version=VERSION, rule_version=RULE_VERSION, mode='synthetic-stub',
                model_mode=payload.get('model_mode', 'disabled'), issues=issues,
                status='needs_review' if issues else 'ready_for_review',
                summary=f'发现 {len(issues)} 项需核对内容；必须由人工确认。',
                source_id=brief.get('source_id'), source_hash=fingerprint(payload),
                generated_at=datetime.now(timezone.utc).isoformat(), hiring_decision=None)
