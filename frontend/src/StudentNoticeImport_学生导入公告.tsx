import { useState } from 'react';
import type { FormEvent } from 'react';
import { ArrowLeft, ArrowUpRight, CalendarDays, CheckCircle2, FileText, ListChecks, Loader2, Send } from 'lucide-react';
import { api } from './api_接口';
import { label, tr } from './i18n_多语言';
import type { Lang, StudentNoticePreview, StudentNoticeReceipt } from './types_类型';

const maxEmailBytes = 2 * 1024 * 1024;

export default function StudentNoticeImport({ account, lang, back }: {
  account: string; lang: Lang; back: () => void;
}) {
  const [sourceText, setSourceText] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [preview, setPreview] = useState<StudentNoticePreview | null>(null);
  const [receipt, setReceipt] = useState<StudentNoticeReceipt | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const t = (ko: string, zh: string) => tr(lang, ko, zh);

  function clearPreview() {
    setPreview(null);
    setReceipt(null);
    setError('');
  }

  async function loadPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearPreview();
    setBusy(true);
    try {
      setPreview(await api<StudentNoticePreview>(account, '/student-notices/preview', 'POST', {
        source_text: sourceText,
        source_url: sourceUrl.trim(),
      }));
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function submitPreview() {
    if (!preview) return;
    setError('');
    setBusy(true);
    try {
      setReceipt(await api<StudentNoticeReceipt>(account, '/student-notices', 'POST', {
        source_text: preview.source_text,
        source_url: preview.source_url,
      }));
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function loadEmail(file: File) {
    clearPreview();
    if (!file.name.toLowerCase().endsWith('.eml')) {
      setError(t('.eml 파일을 선택해 주세요.', '请选择 .eml 文件。'));
      return;
    }
    if (file.size > maxEmailBytes) {
      setError(t('2MB 이하의 .eml 파일을 선택해 주세요.', '请选择 2 MB 以内的 .eml 文件。'));
      return;
    }
    setBusy(true);
    try {
      const result = await api<StudentNoticePreview>(account, '/student-notices/preview-email', 'POST', file);
      setSourceText(result.source_text);
      setSourceUrl('');
      setPreview(result);
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div data-testid="student-import-page">
      <button className="back-button" onClick={back}><ArrowLeft size={16}/>{t('공지 목록', '返回通知列表')}</button>
      <div className="page-title">
        <div>
          <h1>{t('내 공지 가져오기', '导入公告')}</h1>
          <p>{t('메일 파일, 공지 원문 또는 한양대학교 공개 링크로 미리 본 뒤 검토를 요청하세요.', '可选取邮件文件、粘贴公告原文或填入汉阳大学公开公告链接，预览后送审。')}</p>
        </div>
      </div>

      {error && <p className="alert error" role="alert">{error}</p>}
      <div className={preview ? 'student-intake student-intake-with-preview' : 'student-intake'}>
        <form className="panel student-intake-editor" onSubmit={loadPreview}>
          <label className="field student-email-field">
            <span>{t('메일 파일 (.eml)', '邮件文件（.eml）')}</span>
            <input data-testid="student-import-email" type="file" accept=".eml,message/rfc822" disabled={busy}
              onChange={event => {
                const file = event.currentTarget.files?.[0];
                if (file) void loadEmail(file);
              }}/>
            <small>{t('2MB 이하의 파일에서 제목과 본문만 가져옵니다. 검토 요청 전에 본문을 수정할 수 있습니다.', '从 2 MB 以内的文件提取主题和正文，送审前可编辑正文。')}</small>
          </label>
          <label className="field">
            <span>{t('원문 링크', '原文链接')}</span>
            <input data-testid="student-import-url" type="url" maxLength={2000} placeholder="https://" value={sourceUrl} disabled={busy}
              onChange={event => { setSourceUrl(event.currentTarget.value); clearPreview(); }}/>
          </label>
          <label className="field">
            <span>{t('공지 원문', '公告原文')}</span>
            <textarea data-testid="student-import-text" rows={10} maxLength={100000} value={sourceText} disabled={busy}
              onChange={event => { setSourceText(event.currentTarget.value); clearPreview(); }}/>
            <small>{t('이미지나 첨부 파일의 내용은 텍스트로 붙여 넣으세요.', '图片或附件中的内容可复制为文字后粘贴。')}</small>
          </label>
          <button className="primary" data-testid="student-import-preview" type="submit" disabled={busy || !(sourceText.trim() || sourceUrl.trim())}>
            {busy && !preview ? <Loader2 size={16} className="spin"/> : <FileText size={16}/>}
            {t('공지 미리보기', '预览公告')}
          </button>
        </form>

        {preview && <section className="panel student-intake-preview" aria-labelledby="student-preview-title">
          <h2 id="student-preview-title">{preview.title}</h2>
          <p>{t('아래 원문에서 찾은 후보입니다. 담당자가 날짜와 자료를 확인합니다.', '以下是从原文找到的候选片段，日期和材料由工作人员核对。')}</p>
          <div className="student-intake-candidates">
            <section>
              <h3><CalendarDays size={17}/>{t('날짜 후보', '日期候选')}</h3>
              {preview.dates.length ? <ul>{preview.dates.map(item => <li key={item}>{item}</li>)}</ul>
                : <p>{t('찾은 날짜가 없습니다.', '暂未识别到日期。')}</p>}
            </section>
            <section>
              <h3><ListChecks size={17}/>{t('제출 자료 후보', '材料候选')}</h3>
              {preview.materials.length ? <ul>{preview.materials.map(item => <li key={item}>{item}</li>)}</ul>
                : <p>{t('찾은 제출 자료가 없습니다.', '暂未识别到材料。')}</p>}
            </section>
          </div>
          <details>
            <summary>{t('원문 보기', '查看原文')}</summary>
            {preview.source_url && <a className="student-intake-source" href={preview.source_url} target="_blank" rel="noopener noreferrer">
              {preview.source_url}<ArrowUpRight size={14}/>
            </a>}
            <blockquote>{preview.source_text}</blockquote>
          </details>
          {receipt ? <div className="alert success" data-testid="student-import-receipt" role="status">
            <CheckCircle2 size={18}/>
            <div>
              <strong>{receipt.publication_status === 'approved'
                ? label('approved', lang)
                : t('담당자에게 검토를 요청했습니다.', '已提交工作人员审核。')}</strong>
              <div>{t('접수 번호', '送审编号')} <code>{receipt.notice_id}</code></div>
            </div>
          </div> : <button className="primary" data-testid="student-import-send" disabled={busy} onClick={() => void submitPreview()}>
            {busy ? <Loader2 size={16} className="spin"/> : <Send size={16}/>}
            {t('검토 요청 보내기', '提交工作人员审核')}
          </button>}
        </section>}
      </div>
    </div>
  );
}
