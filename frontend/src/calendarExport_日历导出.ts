import { localize, tr } from './i18n_多语言';
import type { CalendarEvent, Lang, StudentCalendar } from './types_类型';

export function calendarEventKind(kind: CalendarEvent['kind'], lang: Lang) {
  return kind === 'deadline'
    ? tr(lang, '학교 공식 마감', '学校正式截止')
    : tr(lang, '준비 시작 제안', '建议开始日');
}

function escapeText(value: string): string {
  return value.replace(/\\/g, '\\\\').replace(/\r\n|\r|\n/g, '\\n').replace(/([,;])/g, '\\$1');
}

function utcStamp(date: Date): string {
  return date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
}

function foldLine(line: string): string {
  const encoder = new TextEncoder();
  let width = 0;
  let folded = '';
  for (const character of line) {
    const byteLength = encoder.encode(character).length;
    if (width + byteLength > 75) {
      folded += '\r\n ';
      width = 1;
    }
    folded += character;
    width += byteLength;
  }
  return folded;
}

export function downloadCalendar(calendar: StudentCalendar, lang: Lang) {
  const stamp = utcStamp(new Date());
  const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//UniAction//Student Calendar//EN', 'CALSCALE:GREGORIAN'];
  for (const event of calendar.events) {
    // Preserve date-only notices and suggestions as all-day markers, including on export.
    const start = event.starts_at.length === 10
      ? 'DTSTART;VALUE=DATE:' + event.starts_at.replaceAll('-', '')
      : 'DTSTART:' + utcStamp(new Date(event.starts_at));
    const summary = calendarEventKind(event.kind, lang) + ' · ' + localize(event.title, lang);
    lines.push(
      'BEGIN:VEVENT',
      'UID:' + encodeURIComponent(event.id) + '@uniaction.local',
      'SEQUENCE:' + event.version,
      'DTSTAMP:' + stamp,
      start,
      'TRANSP:TRANSPARENT',
      'SUMMARY:' + escapeText(summary),
    );
    if (event.kind === 'preparation') lines.push('DESCRIPTION:' + escapeText(localize(event.notice_title, lang)));
    lines.push('END:VEVENT');
  }
  lines.push('END:VCALENDAR');
  const url = URL.createObjectURL(new Blob([lines.map(foldLine).join('\r\n') + '\r\n'], { type: 'text/calendar;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'UniAction-' + calendar.month + '.ics';
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
