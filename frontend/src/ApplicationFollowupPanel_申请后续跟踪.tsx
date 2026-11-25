import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { ArrowLeft, ArrowRight, Check, ClipboardList, Loader2 } from 'lucide-react';
import { api } from './api_接口';
import { dateLabel, formatMessage, localize, tr } from './i18n_多语言';
import type { ApplicationFollowup, Lang, StudentApplications, TrackedApplication } from './types_类型';

const statuses: Record<ApplicationFollowup['status'], readonly [string, string]> = {
  waiting_result: ['결과 기다리는 중', '等待结果'],
  needs_documents: ['보완 서류 필요', '需补材料'],
  result_checked: ['결과 확인함', '已查看结果'],
};

function FollowupCard({ item, today, lang, onOpen, onSave }: {
  item: TrackedApplication; today: string; lang: Lang; onOpen: () => void;
  onSave: (followup: ApplicationFollowup) => Promise<void>;
}) {
  const t = (ko: string, zh: string) => tr(lang, ko, zh);
  const { followup } = item;
  const [draft, setDraft] = useState<ApplicationFollowup | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');
  const due = followup.status !== 'result_checked' && followup.next_check_on && followup.next_check_on <= today;

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft || saving) return;
    setSaving(true);
    setError('');
    try {
      await onSave(draft);
      setDraft(null);
      setSaved(true);
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return <article className="panel followup-card" data-testid={`app-followup-${item.notice_id}`}>
    <div className="followup-card-heading">
      <h2>{localize(item.title, lang)}</h2>
      <span className={`badge ${due ? 'missing_information' : ''}`} data-testid="followup-status">
        {t(...statuses[followup.status])}
      </span>
    </div>
    <p className="followup-meta">
      {t('내 제출 기록', '自报提交记录')}
      <time dateTime={item.reported_at}>{dateLabel(item.reported_at, lang)}</time>
      <span>v{item.submitted_version}</span>
    </p>
    {item.latest_version > item.submitted_version && <p className="followup-version">
      {formatMessage(t('제출을 기록한 뒤 공지가 v{version}(으)로 변경되었습니다.', '记录提交后，公告已更新至 v{version}。'), { version: item.latest_version })}
    </p>}
    {draft ? <form className="followup-form" onSubmit={save}>
      <fieldset disabled={saving}>
        <div className="followup-fields">
          <label className="field"><span>{t('나의 진행 상태', '我的跟踪状态')}</span>
            <select data-testid="followup-edit-status" value={draft.status}
              onChange={event => setDraft({ ...draft, status: event.currentTarget.value as ApplicationFollowup['status'] })}>
              {(Object.keys(statuses) as ApplicationFollowup['status'][]).map(status =>
                <option key={status} value={status}>{t(...statuses[status])}</option>)}
            </select>
          </label>
          <label className="field"><span>{t('다음 확인 날짜 (학교 시간)', '下次查看日期（学校时间）')}</span>
            <input type="date" min="0001-01-01" max="9999-12-31" data-testid="followup-edit-date" value={draft.next_check_on ?? ''}
              onChange={event => setDraft({ ...draft, next_check_on: event.currentTarget.value || null })}/>
          </label>
        </div>
        <label className="field"><span>{t('비공개 메모', '私人备注')}</span>
          <textarea rows={3} maxLength={1000} data-testid="followup-edit-note" value={draft.note}
            onChange={event => setDraft({ ...draft, note: event.currentTarget.value })}/>
        </label>
        {error && <p className="alert error" role="alert">{error}</p>}
        <div className="button-row">
          <button className="primary" type="submit" data-testid="followup-save"><Check size={16} aria-hidden="true"/>
            {saving ? t('저장 중…', '正在保存…') : t('후속 기록 저장', '保存跟踪记录')}
          </button>
          <button className="secondary" type="button" onClick={() => { setDraft(null); setError(''); }}>{t('취소', '取消')}</button>
        </div>
      </fieldset>
    </form> : <>
      {followup.next_check_on && <p className="followup-meta">
        {t('다음 확인 날짜 (학교 시간)', '下次查看日期（学校时间）')}
        <time dateTime={followup.next_check_on}>{followup.next_check_on}</time>
        {due && <strong className="followup-due" data-testid="followup-due">{t('확인할 날짜가 지났거나 오늘입니다.', '已到查看日期')}</strong>}
      </p>}
      {followup.note && <div className="followup-note"><strong>{t('비공개 메모', '私人备注')}</strong><p>{followup.note}</p></div>}
      <div className="button-row">
        <button className="secondary" data-testid="followup-edit" onClick={() => { setSaved(false); setDraft(followup); }}>
          {t('후속 기록 수정', '编辑跟踪记录')}
        </button>
        <button className="secondary" data-testid="followup-notice" onClick={onOpen}>
          {t('공지 상세 보기', '查看通知详情')}<ArrowRight size={16} aria-hidden="true"/>
        </button>
        {saved && <span className="muted" role="status">{t('후속 기록을 저장했습니다.', '已保存跟踪记录')}</span>}
      </div>
    </>}
  </article>;
}

export default function ApplicationFollowupPanel({ account, lang, openNotice, openNotices, back }: {
  account: string; lang: Lang; openNotice: (id: string) => void; openNotices: () => void; back: () => void;
}) {
  const t = (ko: string, zh: string) => tr(lang, ko, zh);
  const [data, setData] = useState<StudentApplications>();
  const [error, setError] = useState('');
  const [request, setRequest] = useState(0);

  useEffect(() => {
    let active = true;
    api<StudentApplications>(account, '/applications').then(
      result => { if (active) setData(result); },
      (failure: Error) => { if (active) setError(failure.message); },
    );
    return () => { active = false; };
  }, [account, request]);

  async function save(noticeId: string, draft: ApplicationFollowup) {
    const followup = await api<ApplicationFollowup>(account, `/applications/${encodeURIComponent(noticeId)}/follow-up`, 'PUT', draft);
    setData(previous => previous && {
      ...previous,
      items: previous.items.map(item => item.notice_id === noticeId ? { ...item, followup } : item),
    });
  }

  return <div data-testid="applications-page">
    <button className="back-button" onClick={back}>
      <ArrowLeft size={16} aria-hidden="true"/>{t('오늘의 할 일로 돌아가기', '返回今日行动')}
    </button>
    <div className="today-heading"><div>
      <h1>{t('신청 후속 관리', '申请后续跟踪')}</h1>
      <p>{t('제출한 신청의 다음 확인 날짜와 메모를 나만 볼 수 있게 기록하세요.', '为自报已提交的申请记录下次查看日期和私人备注，内容仅本人可见。')}</p>
    </div></div>
    {error && <div className="alert error" role="alert">
      <p>{error}</p><button className="secondary" onClick={() => { setError(''); setRequest(request + 1); }}>{t('새로고침', '刷新')}</button>
    </div>}
    {!data && !error && <div className="loading" role="status">
      <Loader2 className="spin" size={24} aria-hidden="true"/>{t('불러오는 중…', '正在加载…')}
    </div>}
    {data && (data.items.length ? <div className="followup-list">
      {data.items.map(item => <FollowupCard key={item.notice_id} item={item} today={data.today} lang={lang}
        onOpen={() => openNotice(item.notice_id)} onSave={draft => save(item.notice_id, draft)}/>)}
    </div> : <section className="panel followup-empty" data-testid="applications-empty">
      <ClipboardList size={24} aria-hidden="true"/>
      <p>{t('공지에서 제출했다고 기록하면 여기에 신청이 표시됩니다.', '在通知详情记录「我已提交」后，申请会出现在这里。')}</p>
      <button className="secondary" onClick={openNotices}>{t('나의 할 일', '我的事项')}<ArrowRight size={16} aria-hidden="true"/></button>
    </section>)}
  </div>;
}
