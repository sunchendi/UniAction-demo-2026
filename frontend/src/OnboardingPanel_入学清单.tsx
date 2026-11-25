import { useEffect, useState } from 'react';
import { ArrowUpRight, Backpack, BookOpen, CalendarDays, Loader2 } from 'lucide-react';
import { api } from './api_接口';
import CampusPlaceCard from './CampusPlaceCard_办事地点卡';
import { formatMessage, localize, tr, valueLabel } from './i18n_多语言';
import type { Lang, OnboardingChecklist, OnboardingItem, OnboardingStage } from './types_类型';

const stages = [
  { id: 'before_arrival', names: ['도착 전', '到校前'], Icon: Backpack },
  { id: 'first_week', names: ['도착 첫 주', '到校第一周'], Icon: CalendarDays },
  { id: 'term_start', names: ['학기 초', '学期初'], Icon: BookOpen },
] as const satisfies readonly { id: OnboardingStage; names: readonly [string, string]; Icon: typeof BookOpen }[];

export default function OnboardingPanel({ account, lang, openProfile }: {
  account: string; lang: Lang; openProfile: () => void;
}) {
  const [checklist, setChecklist] = useState<OnboardingChecklist | null>(null);
  const [error, setError] = useState('');
  const [request, setRequest] = useState(0);
  const [saving, setSaving] = useState<string | null>(null);
  const t = (ko: string, zh: string) => tr(lang, ko, zh);

  useEffect(() => {
    let active = true;
    api<OnboardingChecklist>(account, '/onboarding').then(
      data => { if (active) setChecklist(data); },
      (failure: Error) => { if (active) setError(failure.message); },
    );
    return () => { active = false; };
  }, [account, request]);

  async function save(itemId: string, completed: boolean) {
    setSaving(itemId);
    setError('');
    try {
      const updated = await api<Pick<OnboardingItem, 'id' | 'completed'>>(
        account, `/onboarding/${encodeURIComponent(itemId)}`, 'PUT', { completed },
      );
      setChecklist(current => current && {
        ...current,
        items: current.items.map(item => item.id === updated.id ? { ...item, completed: updated.completed } : item),
      });
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setSaving(null);
    }
  }

  const items = checklist?.items ?? [];
  const done = items.filter(item => item.completed).length;
  const progress = formatMessage(t('{done} / {total} 완료', '已完成 {done} / {total} 项'), { done, total: items.length });

  return (
    <div data-testid="onboarding-page">
      <div className="page-title">
        <div>
          <h1>{t('유학생 입학 체크리스트', '留学生入学清单')}</h1>
          <p>{t('내 과정에 맞춰 준비하세요. 실제 일정과 절차는 학교 안내에서 확인할 수 있습니다.', '按自己的课程类型准备。具体日期和流程请查看学校公告。')}</p>
        </div>
      </div>

      {error && <div className="alert error" role="alert">
        <span>{error}</span>
        <button className="secondary" onClick={() => {
          setChecklist(null);
          setError('');
          setRequest(previous => previous + 1);
        }}>{t('새로고침', '刷新')}</button>
      </div>}
      {!checklist && !error && <div className="loading" role="status">
        <Loader2 className="spin" size={24} aria-hidden="true"/>{t('불러오는 중…', '正在加载…')}
      </div>}

      {checklist && (items.length ? <div className="onboarding-content">
        <section className="panel onboarding-progress">
          <div className="onboarding-progress-head">
            <span><strong data-testid="onboarding-progress" aria-live="polite">{progress}</strong>
              <span>{valueLabel(checklist.program_type, lang)}</span>
            </span>
            <button className="secondary" onClick={openProfile}>{t('학생 정보', '学生资料')}</button>
          </div>
          <progress value={done} max={items.length} aria-label={progress}/>
        </section>
        {stages.map(({ id, names, Icon }) => {
          const stageItems = items.filter(item => item.stage === id);
          if (!stageItems.length) return null;
          return <section className="panel onboarding-stage" key={id} aria-labelledby={`onboarding-${id}`}>
            <h2 id={`onboarding-${id}`}><Icon size={19} aria-hidden="true"/>{t(names[0], names[1])}</h2>
            <ul className="onboarding-items">
              {stageItems.map(item => {
                const title = localize(item.title, lang);
                const officialGuide = t('학교 안내 보기', '查看校方说明');
                return <li key={item.id} data-testid={`onboarding-item-${item.id}`}>
                  <label className="onboarding-task">
                    <input type="checkbox" data-testid={`onboarding-check-${item.id}`}
                      checked={item.completed} disabled={saving !== null}
                      onChange={event => void save(item.id, event.currentTarget.checked)}/>
                    <span>{title}</span>
                  </label>
                  <details className="onboarding-details">
                    <summary>{t('진행 방법 보기', '查看办理步骤')}</summary>
                    <ol>{item.steps.map((step, index) => <li key={index}>{localize(step, lang)}</li>)}</ol>
                    <a href={item.source_url} target="_blank" rel="noopener noreferrer" aria-label={`${title} · ${officialGuide}`}>
                      {officialGuide}<ArrowUpRight size={15} aria-hidden="true"/>
                    </a>
                  </details>
                  {item.place && <CampusPlaceCard place={item.place} lang={lang}/>}
                </li>;
              })}
            </ul>
          </section>;
        })}
      </div> : <p>{t('현재 과정에 표시할 입학 항목이 없습니다.', '当前课程类型暂无入学事项。')}</p>)}
    </div>
  );
}
