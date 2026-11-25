import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { ArrowRight, ArrowUpRight, Bell, BusFront, CalendarDays, ClipboardList, Clock3, Loader2, MapPin, RefreshCw, UserRound, Utensils } from 'lucide-react';
import { api } from './api_接口';
import { dateLabel, fieldLabel, label, localize, tr } from './i18n_多语言';
import type { Lang, TodayActions } from './types_类型';

type OpenNotice = (id: string, tab?: string, taskId?: string) => void;

const ericaLinks = [
  { id: 'dining', ko: '오늘의 학식', zh: '今日食堂', Icon: Utensils, url: 'https://life.hanyang.ac.kr/theme/pages/home.php' },
  { id: 'shuttle', ko: '셔틀버스 시간표', zh: '校车时刻表', Icon: BusFront, url: 'https://hybus.app/' },
  { id: 'map', ko: '캠퍼스 지도', zh: '校园地图', Icon: MapPin, url: 'https://www.hanyang.ac.kr/map_erica' },
] as const;
const seoulLinks = [
  { id: 'dining', ko: '오늘의 학식', zh: '今日食堂', Icon: Utensils, url: 'https://fnb.hanyang.ac.kr/front/fnbmMdMenu' },
  { id: 'map', ko: '캠퍼스 지도', zh: '校园地图', Icon: MapPin, url: 'https://www.hanyang.ac.kr/web/www/map_seoul' },
] as const;

function TodayGroup({ id, heading, icon, children }: {
  id: string; heading: string; icon: ReactNode; children: ReactNode;
}) {
  return (
    <section className="panel today-group" aria-labelledby={id}>
      <h2 id={id}>{icon}{heading}</h2>
      {children}
    </section>
  );
}

export default function TodayPanel({ account, lang, schoolId, openNotice, openProfile, openCalendar, openApplications }: {
  account: string; lang: Lang; schoolId?: string; openNotice: OpenNotice; openProfile: () => void;
  openCalendar: () => void; openApplications: () => void;
}) {
  const [result, setResult] = useState<TodayActions | null>(null);
  const [error, setError] = useState('');
  const [request, setRequest] = useState(0);
  const t = (ko: string, zh: string) => tr(lang, ko, zh);
  const campusLinks = schoolId === 'hanyang_demo' ? seoulLinks : schoolId === 'hanyang_erica' ? ericaLinks : null;

  useEffect(() => {
    let active = true;
    api<TodayActions>(account, '/today').then(
      data => { if (active) setResult(data); },
      (failure: Error) => { if (active) setError(failure.message); },
    );
    return () => { active = false; };
  }, [account, request]);

  return (
    <div className="today-page" data-testid="today-page">
      <div className="today-heading">
        <div>
          <h1>{t('오늘의 할 일', '今日行动')}</h1>
          <p>{t('다가오는 마감과 공지 변경을 확인하고, 지금 할 일부터 시작하세요.', '查看临近的截止时间和公告变化，开始处理下一项任务。')}</p>
        </div>
        <div className="today-heading-actions">
          <button className="secondary" data-testid="calendar-open" onClick={openCalendar}>
            <CalendarDays size={16} aria-hidden="true"/>{t('내 일정', '我的日历')}
          </button>
          <button className="secondary" data-testid="applications-open" onClick={openApplications}>
            <ClipboardList size={16} aria-hidden="true"/>{t('신청 후속 관리', '申请后续跟踪')}
          </button>
          <button className="secondary" disabled={!result && !error} onClick={() => {
            setError('');
            setResult(null);
            setRequest(previous => previous + 1);
          }}><RefreshCw size={16} aria-hidden="true"/>{t('새로고침', '刷新')}</button>
        </div>
      </div>

      {error && <p className="alert error" role="alert">{error}</p>}
      {!result && !error && <div className="loading" role="status"><Loader2 className="spin" size={24} aria-hidden="true"/>{t('불러오는 중…', '正在加载…')}</div>}

      {result && <div className="today-grid">
        <TodayGroup id="today-upcoming" icon={<Clock3 size={20} aria-hidden="true"/>} heading={t('마감이 다가오는 일', '即将截止')}>
          {result.upcoming.length ? <ul className="today-list">
            {result.upcoming.map(item => <li key={item.notice_id}>
              <button className="today-link" data-testid={`today-upcoming-${item.notice_id}`} onClick={() => openNotice(item.notice_id)}>
                <span>{localize(item.title, lang)}</span><ArrowRight size={16} aria-hidden="true"/>
              </button>
              <span className={`badge today-match ${item.match_status}`}>{label(item.match_status, lang)}</span>
              {item.deadline && <p className="today-date">
                {t('학교 공식 마감', '学校正式截止')}<time dateTime={item.deadline}>{dateLabel(item.deadline, lang)}</time>
              </p>}
              {!!item.tasks.length && <ul className="today-tasks">
                {item.tasks.map(task => <li key={task.id}>
                  <button className="today-link today-task" data-testid={`today-task-${task.id}`} onClick={() => openNotice(item.notice_id, 'tasks', task.id)}>
                    <span>{localize(task.title, lang)}</span><ArrowRight size={14} aria-hidden="true"/>
                  </button>
                  {task.suggested_start_at && <p className="today-date">
                    {t('준비 시작 제안', '建议开始日')}<time dateTime={task.suggested_start_at}>{task.suggested_start_at}</time>
                  </p>}
                </li>)}
              </ul>}
            </li>)}
          </ul> : <p className="today-empty">{t('7일 안에 마감하거나 준비할 일이 없습니다.', '未来 7 天没有要准备或截止的事项。')}</p>}
        </TodayGroup>

        <div className="today-side">
          <TodayGroup id="today-changes" icon={<Bell size={20} aria-hidden="true"/>} heading={t('공지 변경', '公告有变')}>
            {result.changes.length ? <ul className="today-list">
              {result.changes.map(item => <li key={item.notice_id}>
                <button className="today-link" data-testid={`today-change-${item.notice_id}`} onClick={() => openNotice(item.notice_id, 'versions')}>
                  <span>{localize(item.title, lang)} <small>v{item.version}</small></span><ArrowRight size={16} aria-hidden="true"/>
                </button>
                <p className="today-note">{localize(item.summary, lang)}</p>
                {!!item.tasks.length && <ul className="today-tasks">
                  {item.tasks.map(task => <li key={task.id}>
                    <button className="today-link today-task" onClick={() => openNotice(item.notice_id, 'tasks', task.id)}>
                      <span>{localize(task.title, lang)}<small>{t('다시 확인 필요', '需要重新确认')}</small></span><ArrowRight size={14} aria-hidden="true"/>
                    </button>
                  </li>)}
                </ul>}
              </li>)}
            </ul> : <p className="today-empty">{t('변경된 관련 공지가 없습니다.', '暂无与你相关的公告变更。')}</p>}
          </TodayGroup>

          <TodayGroup id="today-missing" icon={<UserRound size={20} aria-hidden="true"/>} heading={t('추가 정보 필요', '待补资料')}>
            {result.missing.length ? <>
              <ul className="today-list">
                {result.missing.map(item => <li key={item.notice_id}>
                  <button className="today-link" data-testid={`today-missing-${item.notice_id}`} onClick={() => openNotice(item.notice_id, 'evidence')}>
                    <span>{localize(item.title, lang)}</span><ArrowRight size={16} aria-hidden="true"/>
                  </button>
                  <p className="today-note">{item.fields.map(field => fieldLabel(field, lang)).join(' · ')}</p>
                </li>)}
              </ul>
              <button className="secondary today-profile" onClick={openProfile}>{t('정보 보완', '补充资料')}<ArrowRight size={15} aria-hidden="true"/></button>
            </> : <p className="today-empty">{t('지금 보완할 정보가 없습니다.', '目前没有需要补充的资料。')}</p>}
          </TodayGroup>
        </div>
      </div>}

      {campusLinks && <section className="panel today-group campus-shortcuts" aria-labelledby="campus-shortcuts-title">
        <h2 id="campus-shortcuts-title">{t('캠퍼스 바로가기', '校园快捷入口')}</h2>
        <div className="campus-shortcut-list">
          {campusLinks.map(({ id, ko, zh, Icon, url }) => (
            <a className="campus-shortcut" key={id} data-testid={`campus-shortcut-${id}`}
              href={url} target="_blank" rel="noopener noreferrer">
              <Icon size={19} aria-hidden="true"/><span>{t(ko, zh)}</span><ArrowUpRight size={15} aria-hidden="true"/>
            </a>
          ))}
        </div>
      </section>}
    </div>
  );
}
