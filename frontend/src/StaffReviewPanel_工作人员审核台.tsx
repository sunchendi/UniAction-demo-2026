import { useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { ArrowRight, FileCheck2, FileText, Search } from 'lucide-react';
import { dateLabel, fieldLabel, label, localize, tr, valueLabel } from './i18n_多语言';
import type { Lang, ReviewChecks, ReviewDuplicate } from './types_类型';

const evidenceLabel = ['원문 근거 확인 필요', '原文依据待核对'] as const;
const matches: Record<ReviewDuplicate['reasons'][number], readonly [string, string]> = {
  same_source: ['원문 일치', '原文相同'],
  same_link: ['원문 링크 일치', '来源链接相同'],
  same_title: ['제목 일치', '标题相同'],
};

export function ReviewFlags({ checks, lang }: { checks?: ReviewChecks; lang: Lang }) {
  return <>
    {checks?.missing_deadline && <span className="badge missing_information" data-testid="review-no-date">
      {tr(lang, '마감일 없음', '缺截止日期')}
    </span>}
    {checks?.missing_evidence && <span className="badge missing_information" data-testid="review-no-evidence">
      {tr(lang, ...evidenceLabel)}
    </span>}
    {!!checks?.duplicates.length && <span className="badge needs_staff_review" data-testid="review-duplicates">
      {tr(lang, '중복 의심', '疑似重复')}
    </span>}
  </>;
}

function record(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function text(value: unknown) { return typeof value === 'string' ? value : ''; }
function items(value: unknown): unknown[] { return Array.isArray(value) ? value : []; }
function draftLabel(value: unknown, lang: Lang) {
  const localized = record(value);
  if (typeof localized.ko === 'string' && typeof localized.zh === 'string') {
    return localize({ ko: localized.ko, zh: localized.zh }, lang);
  }
  return text(value) || '—';
}

function draftFrom(editor: string) {
  try {
    const data = record(JSON.parse(editor));
    return Object.keys(data).length ? data : null;
  } catch {
    return null;
  }
}

interface ReviewRow {
  name: string;
  value: string;
  quote: string;
  tokens?: string[];
  pending?: boolean;
  depth?: number;
}

function reviewRows(draft: Record<string, unknown>, lang: Lang): ReviewRow[] {
  const t = (ko: string, zh: string) => tr(lang, ko, zh);
  const evidence = record(draft.evidence);
  const window = record(draft.application_window);
  const rows: ReviewRow[] = [];
  function dateRow(name: string, date: string, quote: string, requireTime = false) {
    if (!date) return;
    const tokens = [date.slice(0, 10)];
    if (requireTime && date.length > 10) tokens.push(date.slice(11, 16));
    rows.push({ name, value: dateLabel(date, lang), quote, tokens });
  }

  dateRow(t('학교 공식 마감', '学校正式截止'), text(draft.official_deadline), text(evidence.official_deadline), true);
  dateRow(t('신청 시작일', '申请开放日期'), text(window.opens_at), text(evidence.application_window));
  dateRow(t('신청 종료일', '申请结束日期'), text(window.closes_at), text(evidence.application_window));

  const ruleRows: ReviewRow[] = [];
  function visitRule(value: unknown, depth = 0) {
    if (depth > 12 || ruleRows.length >= 100) return;
    const rule = record(value);
    const op = text(rule.op);
    if (!op) return;
    const field = text(rule.field);
    const values = (Array.isArray(rule.value) ? rule.value : [rule.value]).filter(item =>
      typeof item === 'string' || typeof item === 'number' || typeof item === 'boolean');
    const operator = ({ eq: '=', gte: '≥', lte: '≤', in: '∈' } as Record<string, string>)[op];
    const ruleValue = op === 'all' ? t('모든 하위 조건 충족', '满足全部子条件')
      : op === 'any' ? t('하위 조건 중 하나 충족', '满足任一子条件')
        : op === 'needs_staff_review' ? label(op, lang)
          : op === 'is_true' || op === 'is_false' ? valueLabel(op === 'is_true', lang)
            : [operator, ...values.map(item => valueLabel(item, lang))].filter(Boolean).join(' ');
    ruleRows.push({ name: field ? fieldLabel(field, lang) : t('신청 조건', '申请条件'), value: ruleValue, quote: text(rule.evidence), pending: op === 'needs_staff_review', depth });
    for (const child of items(rule.children).slice(0, 100)) visitRule(child, depth + 1);
  }
  visitRule(draft.eligibility_rules);
  rows.push(...ruleRows);

  for (const value of items(draft.required_documents)) {
    const document = record(value);
    rows.push({ name: t('필수 서류', '必需材料'), value: draftLabel(document.title, lang), quote: text(document.evidence), tokens: [text(record(document.title).ko)] });
  }
  for (const value of items(draft.task_templates)) {
    const task = record(value);
    if (task.required_or_suggested !== 'required' || task.task_type === 'document') continue;
    rows.push({ name: t('필수 과제', '必需任务'), value: draftLabel(task.title, lang), quote: text(task.source_evidence) });
  }
  const link = text(draft.application_url);
  if (link) rows.push({ name: t('신청 링크', '办理链接'), value: link, quote: text(evidence.application_url), tokens: [link] });
  if (draft.office_contact) {
    const contact = record(draft.office_contact);
    const tokens = [text(contact.email), text(contact.phone)].filter(Boolean);
    rows.push({ name: t('담당 부서', '办理咨询部门'), value: [draftLabel(contact.name, lang), ...tokens].join(' · '), quote: text(contact.evidence), tokens });
  }
  return rows;
}

export default function StaffReviewPanel({ lang, editor, setEditor, preservedSource, duplicates, openNotice, badge, metadata, actions }: {
  lang: Lang; editor: string; setEditor: (value: string) => void; preservedSource?: string;
  duplicates: ReviewDuplicate[]; openNotice: (id: string) => void;
  badge: ReactNode; metadata: ReactNode; actions: ReactNode;
}) {
  const t = (ko: string, zh: string) => tr(lang, ko, zh);
  const draft = useMemo(() => draftFrom(editor), [editor]);
  const source = preservedSource ?? text(draft?.source_text);
  const [quote, setQuote] = useState('');
  const focusedExcerpt = useRef<HTMLElement>(null);
  const start = quote ? source.indexOf(quote) : -1;
  const rows = useMemo(() => draft ? reviewRows(draft, lang) : [], [draft, lang]);
  const validity = (row: ReviewRow) => !!row.quote.trim() && source.includes(row.quote)
    && (row.tokens ?? []).every(token => row.quote.includes(token));
  const checks = draft && {
    missing_deadline: !(text(draft.official_deadline) || text(record(draft.application_window).closes_at)),
    missing_evidence: !text(record(draft.eligibility_rules).op) || rows.some(row => row.pending || !validity(row))
      || Object.values(record(draft.evidence)).some(value => !text(value).trim() || !source.includes(text(value))),
    duplicates,
  };

  useEffect(() => {
    if (start >= 0) focusedExcerpt.current?.scrollIntoView({ block: 'nearest' });
  }, [quote, start]);

  return <>
    <div className="review-layout staff-review-layout">
      <section className="panel review-source-panel" aria-labelledby="review-source-heading">
        <div className="section-heading"><FileText size={20} aria-hidden="true"/>
          <h2 id="review-source-heading">{t('원문 보존', '保留原文')}</h2>{badge}
        </div>
        <pre className="source-text" tabIndex={0} data-testid="review-source">{start >= 0 ? <>
          {source.slice(0, start)}<mark ref={focusedExcerpt}>{quote}</mark>{source.slice(start + quote.length)}
        </> : source || t('편집기에 원문을 입력하세요.', '请在编辑器中填写原文。')}</pre>
        {metadata}
      </section>
      <section className="panel" aria-labelledby="review-fields-heading">
        <div className="section-heading"><FileCheck2 size={20} aria-hidden="true"/>
          <h2 id="review-fields-heading">{t('추출 결과', '提取结果')}</h2>
        </div>
        {draft && checks ? <>
          <div className="review-flags"><ReviewFlags checks={checks} lang={lang}/></div>
          <h3>{draftLabel(draft.title, lang)}</h3>
          <dl className="review-fields">
            {rows.map((row, index) => {
              const valid = validity(row);
              return <div key={index} style={row.depth ? { paddingInlineStart: Math.min(row.depth, 4) * 10 } : undefined}>
                <dt>{row.name}</dt>
                <dd><span>{row.value || '—'}</span>
                  {valid ? <button className="review-evidence" type="button" aria-pressed={row.quote === quote}
                    onClick={() => setQuote(row.quote === quote ? '' : row.quote)}>
                    <Search size={14} aria-hidden="true"/>{t('원문 근거 찾기', '定位原文依据')}
                  </button> : <small>{t(...evidenceLabel)}</small>}
                </dd>
              </div>;
            })}
          </dl>
        </> : <p className="muted" role="status">{t('올바른 JSON을 입력하면 추출 결과가 표시됩니다.', 'JSON 格式有效后会显示提取结果。')}</p>}
        {!!duplicates.length && <div className="review-related">
          <h3>{t('중복 의심 공지', '疑似重复公告')}</h3>
          <ul>{duplicates.map(other => <li key={other.id}>
            <button className="today-link" onClick={() => openNotice(other.id)}>
              <span>{localize(other.title, lang)} <small>{other.id}</small></span><ArrowRight size={15} aria-hidden="true"/>
            </button>
            <small>{other.reasons.map(reason => t(...matches[reason])).join(' · ')}</small>
          </li>)}</ul>
        </div>}
      </section>
    </div>
    <section className="panel review-editor-panel" aria-labelledby="review-editor-heading">
      <h2 id="review-editor-heading">{t('구조화 필드 편집', '编辑结构化字段')}</h2>
      <p className="editor-hint">{t('조건·서류·마감·연락처·근거를 수정할 수 있습니다. 규칙과 필드는 서버에서 허용 목록으로 검증합니다.','可修改条件、材料、截止、联系人和依据。规则与字段由服务端按白名单校验。')}</p>
      <textarea aria-label={t('구조화 초안 JSON 편집', '编辑结构化草稿 JSON')} className="json-editor" spellCheck={false}
        value={editor} onChange={event => setEditor(event.currentTarget.value)} rows={16}/>
      {actions}
    </section>
  </>;
}
