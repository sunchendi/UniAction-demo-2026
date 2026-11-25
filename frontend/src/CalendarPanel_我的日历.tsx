import { useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight, CalendarDays, ChevronLeft, ChevronRight, Download, Loader2 } from 'lucide-react';
import { api } from './api_接口';
import { calendarEventKind, downloadCalendar } from './calendarExport_日历导出';
import { dateLabel, formatMessage, languages, localize, tr } from './i18n_多语言';
import type { CalendarEvent, Lang, StudentCalendar } from './types_类型';

export interface CalendarSelection { month?: string; day?: string }

function utcDate(day: string) {
  return new Date(day + 'T00:00:00Z');
}

function adjacentMonth(month: string, change: number): string {
  const date = utcDate(month + '-01');
  date.setUTCMonth(date.getUTCMonth() + change);
  return date.toISOString().slice(0, 7);
}

function weeksFor(month: string) {
  const first = utcDate(month + '-01');
  const last = utcDate(month + '-01');
  last.setUTCMonth(last.getUTCMonth() + 1, 0);
  const leading = (first.getUTCDay() + 6) % 7;
  const weekCount = Math.ceil((leading + last.getUTCDate()) / 7);
  return Array.from({ length: weekCount }, (_, week) => Array.from({ length: 7 }, (_, weekday) => {
    const day = week * 7 + weekday - leading + 1;
    return day > 0 && day <= last.getUTCDate() ? day : null;
  }));
}

function groupEvents(events: CalendarEvent[]) {
  const byDay = new Map<string, CalendarEvent[]>();
  for (const event of events) {
    const day = event.starts_at.slice(0, 10);
    const group = byDay.get(day);
    if (group) group.push(event);
    else byDay.set(day, [event]);
  }
  return byDay;
}

export default function CalendarPanel({ account, lang, selection, setSelection, openNotice, back }: {
  account: string; lang: Lang; selection: CalendarSelection;
  setSelection: (selection: CalendarSelection) => void;
  openNotice: (id: string, tab?: string, taskId?: string) => void; back: () => void;
}) {
  const t = (ko: string, zh: string) => tr(lang, ko, zh);
  const [response, setResponse] = useState<{ key: string; data?: StudentCalendar; error?: string }>();
  const [retry, setRetry] = useState(0);
  const month = selection.month;
  const key = `${account}:${month ?? ''}:${retry}`;
  const calendar = response?.key === key ? response.data : undefined;
  const error = response?.key === key ? response.error : undefined;

  useEffect(() => {
    let active = true;
    const path = month ? '/calendar?month=' + encodeURIComponent(month) : '/calendar';
    api<StudentCalendar>(account, path).then(
      data => { if (active) setResponse({ key, data }); },
      (failure: Error) => { if (active) setResponse({ key, error: failure.message }); },
    );
    return () => { active = false; };
  }, [account, key, month]);

  const locale = languages[lang].locale;
  const monthFormat = new Intl.DateTimeFormat(locale, { month: 'long', year: 'numeric', timeZone: 'UTC' });
  const dayFormat = new Intl.DateTimeFormat(locale, { weekday: 'long', month: 'long', day: 'numeric', timeZone: 'UTC' });
  const weekdayFormat = new Intl.DateTimeFormat(locale, { weekday: 'short', timeZone: 'UTC' });
  const weekdays = Array.from({ length: 7 }, (_, offset) => {
    const date = String(5 + offset).padStart(2, '0');
    return weekdayFormat.format(utcDate(`2026-01-${date}`));
  });
  const days = groupEvents(calendar?.events ?? []);
  const agenda = selection.day
    ? [[selection.day, days.get(selection.day) ?? []] as const]
    : [...days.entries()];

  return (
    <div className="student-calendar" data-testid="calendar-page">
      <button className="back-button" onClick={back}>
        <ArrowLeft size={16} aria-hidden="true"/>{t('오늘의 할 일로 돌아가기', '返回今日行动')}
      </button>
      <div className="today-heading">
        <div>
          <h1>{t('내 일정', '我的日历')}</h1>
          <p>{t('학교 시간(KST) 기준으로 마감일과 준비 일정을 확인하세요.', '按学校时间（KST）查看截止日和建议准备日。')}</p>
        </div>
        <button className="secondary" data-testid="calendar-export" disabled={!calendar?.events.length}
          onClick={() => { if (calendar) downloadCalendar(calendar, lang); }}>
          <Download size={16} aria-hidden="true"/>{t('이달 일정 내보내기', '导出当月日历')} <span>.ics</span>
        </button>
      </div>

      {error && <div className="alert error" role="alert">
        <p>{error}</p><button className="secondary" onClick={() => setRetry(retry + 1)}>{t('새로고침', '刷新')}</button>
      </div>}
      {!calendar && !error && <div className="loading" role="status">
        <Loader2 className="spin" size={24} aria-hidden="true"/>{t('불러오는 중…', '正在加载…')}
      </div>}

      {calendar && <div className="calendar-layout">
        <section className="panel calendar-grid">
          <div className="calendar-toolbar">
            <h2 data-testid="calendar-month">{monthFormat.format(utcDate(calendar.month + '-01'))}</h2>
            <div>
              <button className="icon-button" type="button" data-testid="calendar-prev" disabled={calendar.month === '0001-01'}
                aria-label={t('지난달', '上个月')} onClick={() => setSelection({ month: adjacentMonth(calendar.month, -1) })}>
                <ChevronLeft size={19} aria-hidden="true"/>
              </button>
              <button className="secondary" type="button" onClick={() => setSelection({ month: calendar.today.slice(0, 7), day: calendar.today })}>
                {t('오늘', '今天')}
              </button>
              <button className="icon-button" type="button" data-testid="calendar-next" disabled={calendar.month === '9999-12'}
                aria-label={t('다음 달', '下个月')} onClick={() => setSelection({ month: adjacentMonth(calendar.month, 1) })}>
                <ChevronRight size={19} aria-hidden="true"/>
              </button>
            </div>
          </div>
          <table className="calendar-table" aria-label={monthFormat.format(utcDate(calendar.month + '-01'))}>
            <thead><tr>{weekdays.map((weekday, index) => <th key={index} scope="col">{weekday}</th>)}</tr></thead>
            <tbody>{weeksFor(calendar.month).map((week, index) => <tr key={index}>
              {week.map((number, column) => {
                if (number === null) return <td key={column}/>;
                const date = `${calendar.month}-${String(number).padStart(2, '0')}`;
                const entries = days.get(date) ?? [];
                const kinds = new Set(entries.map(event => event.kind));
                const count = formatMessage(t('일정 {count}개', '{count} 项安排'), { count: entries.length });
                return <td key={column}>
                  <button className="calendar-day" type="button" data-testid={`calendar-day-${date}`}
                    aria-pressed={selection.day === date} aria-current={calendar.today === date ? 'date' : undefined}
                    aria-label={dayFormat.format(utcDate(date)) + ' · ' + count}
                    onClick={() => setSelection({ month, day: date })}>
                    <span>{number}</span>
                    {!!kinds.size && <span className="calendar-markers" aria-hidden="true">
                      {[...kinds].map(kind => <span className={`calendar-marker ${kind}`} key={kind}/>)}
                    </span>}
                  </button>
                </td>;
              })}
            </tr>)}</tbody>
          </table>
          <div className="calendar-legend">
            <span><i className="calendar-marker deadline"/>{calendarEventKind('deadline', lang)}</span>
            <span><i className="calendar-marker preparation"/>{calendarEventKind('preparation', lang)}</span>
          </div>
        </section>

        <section className="panel calendar-agenda" aria-labelledby="calendar-agenda-title">
          <div className="calendar-toolbar">
            <h2 id="calendar-agenda-title"><CalendarDays size={18} aria-hidden="true"/>
              {selection.day ? dayFormat.format(utcDate(selection.day)) : t('이달 일정', '本月安排')}
            </h2>
            {selection.day && <button type="button" className="secondary" onClick={() => setSelection({ month })}>
              {t('이달 전체', '整月')}
            </button>}
          </div>
          {agenda.some(([, events]) => events.length) ? agenda.map(([date, events]) => <div className="calendar-agenda-day" key={date}>
            {!selection.day && <h3>{dayFormat.format(utcDate(date))}</h3>}
            <ul>{events.map(event => <li key={event.id}>
              <button className="calendar-agenda-item" data-testid={`calendar-event-${event.id}`}
                onClick={() => openNotice(event.notice_id, 'tasks', event.task_id ?? undefined)}>
                <span>
                  <span className="calendar-entry-kind">
                    <i className={`calendar-marker ${event.kind}`}/>{calendarEventKind(event.kind, lang)}
                  </span>
                  <strong>{localize(event.title, lang)}</strong>
                  {event.kind === 'preparation'
                    ? <span>{localize(event.notice_title, lang)}</span>
                    : <time dateTime={event.starts_at}>{dateLabel(event.starts_at, lang)}</time>}
                </span>
                <ArrowRight size={16} aria-hidden="true"/>
              </button>
            </li>)}</ul>
          </div>) : <p className="today-empty">{t('선택한 기간에 일정이 없습니다.', '所选日期范围暂无安排。')}</p>}
        </section>
      </div>}
    </div>
  );
}
