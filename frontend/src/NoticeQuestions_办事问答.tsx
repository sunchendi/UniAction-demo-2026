import { useState } from 'react';
import { ArrowRight, ArrowUpRight, ClipboardList, MapPin, ShieldCheck } from 'lucide-react';
import CampusPlaceCard from './CampusPlaceCard_办事地点卡';
import { fieldLabel, formatMessage, label, localize, tr } from './i18n_多语言';
import type { CampusPlace, Detail, Document, Lang } from './types_类型';

type OpenTask = (id?: string) => void;

const questions = [
  { id: 'eligibility', ko: '신청 조건을 충족하나요?', zh: '我符合条件吗？', Icon: ShieldCheck },
  { id: 'materials', ko: '어떤 자료가 더 필요한가요?', zh: '还缺哪些材料？', Icon: ClipboardList },
  { id: 'location', ko: '어디에서 처리하나요?', zh: '去哪里办？', Icon: MapPin },
] as const;

function EvidenceQuotes({ quotes, lang }: { quotes: string[]; lang: Lang }) {
  const excerpts = [...new Set(quotes.filter(Boolean))];
  if (!excerpts.length) return null;
  return (
    <section className="question-evidence">
      <h3>{tr(lang, '원문 근거', '原文依据')}</h3>
      {excerpts.map(excerpt => <blockquote key={excerpt}>{excerpt}</blockquote>)}
    </section>
  );
}

function MaterialAnswer({ detail, lang, openTask }: { detail: Detail; lang: Lang; openTask: OpenTask }) {
  const t = (ko: string, zh: string) => tr(lang, ko, zh);
  const documents = detail.notice.required_documents;
  const tasksByTemplate = new Map(
    detail.tasks.filter(task => task.task_type === 'document' && task.notice_version === detail.notice.version)
      .map(task => [task.template_id, task]),
  );
  const outstanding = documents.filter(document => tasksByTemplate.get(document.id)?.status !== 'done');
  if (!documents.length) return <p>{t('확인된 제출 자료 항목이 없습니다.', '当前暂无已核对的必备材料条目。')}</p>;
  return (
    <>
      <p className="question-result">{outstanding.length
        ? formatMessage(t('준비할 자료 {count}개가 남았습니다.', '还有 {count} 项材料待准备。'), { count: outstanding.length })
        : t('필수 자료 과제를 모두 완료했습니다.', '必备材料任务均已完成。')}</p>
      {!!outstanding.length && <ul className="question-task-list">
        {outstanding.map(document => {
          const task = tasksByTemplate.get(document.id);
          return <li key={document.id}>
            <button className="question-task" onClick={() => openTask(task?.id)}>
              <span>{localize(document.title, lang)}</span>
              <span>{task ? label(task.status, lang) : t('진행 기록 없음', '暂无进度记录')}<ArrowRight size={15} aria-hidden="true"/></span>
            </button>
          </li>;
        })}
      </ul>}
      <EvidenceQuotes quotes={(outstanding.length ? outstanding : documents).map(document => document.evidence)} lang={lang}/>
    </>
  );
}

function LocationAnswer({ detail, lang, openTask, openHelp }: {
  detail: Detail; lang: Lang; openTask: OpenTask; openHelp: () => void;
}) {
  const { notice, tasks, task_places: places = {} } = detail;
  const t = (ko: string, zh: string) => tr(lang, ko, zh);
  const groups = new Map<string, { place: CampusPlace; documents: Document[] }>();
  for (const document of notice.required_documents) {
    const place = places[document.id];
    if (!place) continue;
    const group = groups.get(place.id);
    if (group) group.documents.push(document);
    else groups.set(place.id, { place, documents: [document] });
  }
  const office = notice.office_contact?.is_demo === false ? notice.office_contact : null;
  const applicationUrl = notice.application_link_type === 'official' ? notice.application_url : null;
  const evidence = [...groups.values()].flatMap(group => group.documents.map(document => document.evidence));
  if (applicationUrl && notice.evidence.application_url) evidence.push(notice.evidence.application_url);
  if (office?.evidence) evidence.push(office.evidence);

  return (
    <>
      {[...groups.values()].map(({ place, documents }) => (
        <div className="question-location" key={place.id}>
          <CampusPlaceCard place={place} lang={lang}/>
          <ul className="question-task-list">
            {documents.map(document => {
              const task = tasks.find(item => item.template_id === document.id && item.notice_version === notice.version);
              return <li key={document.id}><button className="question-task" onClick={() => openTask(task?.id)}>
                <span>{localize(document.title, lang)}</span><ArrowRight size={15} aria-hidden="true"/>
              </button></li>;
            })}
          </ul>
        </div>
      ))}
      {applicationUrl && <a className="secondary question-application" href={applicationUrl} target="_blank" rel="noopener noreferrer">
        {t('공식 신청 링크', '官方办理链接')}<ArrowUpRight size={16} aria-hidden="true"/>
      </a>}
      {office && <p className="question-office">
        <strong>{localize(office.name, lang)}</strong>
        {office.email && <span>{office.email}</span>}
        {office.phone && <span>{office.phone}</span>}
      </p>}
      {!groups.size && !applicationUrl && !office && <>
        <p>{t('확인된 방문 장소나 공식 신청 링크가 없습니다.', '暂无已核实的办理地点或官方入口。')}</p>
        <button className="secondary" onClick={openHelp}>{t('도움 요청','请求协助')}<ArrowRight size={15} aria-hidden="true"/></button>
      </>}
      <EvidenceQuotes quotes={evidence} lang={lang}/>
    </>
  );
}

export default function NoticeQuestions({ detail, lang, openTask, openEvidence, openProfile, openHelp }: {
  detail: Detail; lang: Lang; openTask: OpenTask; openEvidence: () => void;
  openProfile: () => void; openHelp: () => void;
}) {
  const [question, setQuestion] = useState<(typeof questions)[number]['id']>('eligibility');
  const { notice, match } = detail;
  const t = (ko: string, zh: string) => tr(lang, ko, zh);
  if (notice.publication_status !== 'approved' || !match) return null;

  return (
    <section className="panel notice-questions" data-testid="notice-questions">
      <div className="question-choices">
        {questions.map(({ id, ko, zh, Icon }) => <button className="secondary" type="button"
          key={id} aria-pressed={question === id} aria-controls="notice-question-answer"
          data-testid={`question-${id}`} onClick={() => setQuestion(id)}>
          <Icon size={17} aria-hidden="true"/>{t(ko, zh)}
        </button>)}
      </div>
      <div id="notice-question-answer" className="question-answer" aria-live="polite">
        {question === 'eligibility' && <>
          <p className="question-result">{label(match.status, lang)}</p>
          {match.status === 'conditions_met' && <p>
            {t('최종 접수, 자격 확인 및 선발 결과는 학교가 확인합니다.', '最终受理、资格核验及选拔结果由学校确认。')}
          </p>}
          {!!match.missing_fields.length && <p>{match.missing_fields.map(field => fieldLabel(field, lang)).join(' · ')}</p>}
          <EvidenceQuotes quotes={[notice.eligibility_rules.evidence ?? '']} lang={lang}/>
          <div className="question-actions">
            <button className="secondary" onClick={openEvidence}>{t('조건과 원문','条件与原文')}<ArrowRight size={15} aria-hidden="true"/></button>
            {!!match.missing_fields.length && <button className="secondary" onClick={openProfile}>{t('정보 보완','补充资料')}<ArrowRight size={15} aria-hidden="true"/></button>}
            {match.needs_staff_review && <button className="secondary" onClick={openHelp}>{t('도움 요청','请求协助')}<ArrowRight size={15} aria-hidden="true"/></button>}
          </div>
        </>}
        {question === 'materials' && <MaterialAnswer detail={detail} lang={lang} openTask={openTask}/>}
        {question === 'location' && <LocationAnswer detail={detail} lang={lang} openTask={openTask} openHelp={openHelp}/>}
      </div>
    </section>
  );
}
