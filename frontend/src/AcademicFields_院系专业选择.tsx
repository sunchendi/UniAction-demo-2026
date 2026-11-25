import { tr } from './i18n_多语言';
import type { CatalogName, CollegeOption, Lang, SchoolOption } from './types_类型';

export function catalogName(name: CatalogName, lang: Lang) {
  return name[lang === 'ko' || lang === 'zh' ? lang : 'en'];
}

export default function AcademicFields({ school, collegeId, majorId, lang, prefix, disabled, required, onChange }: {
  school?: SchoolOption; collegeId: string; majorId: string; lang: Lang; prefix: 'auth' | 'profile';
  disabled?: boolean; required?: boolean; onChange: (college: CollegeOption | undefined, majorId: string) => void;
}) {
  const college = school?.colleges.find(item => item.id === collegeId);
  return <>
    <label className="field">
      <span>{tr(lang, '단과대학', '所属院系')}</span>
      <select data-testid={prefix + '-department'} value={collegeId} disabled={disabled || !school} required={required}
        onChange={event => onChange(school?.colleges.find(item => item.id === event.currentTarget.value), '')}>
        <option value="" disabled>{tr(lang, '단과대학을 선택하세요', '请选择院系')}</option>
        {school?.colleges.map(item => <option key={item.id} value={item.id}>{catalogName(item.name, lang)}</option>)}
      </select>
    </label>
    <label className="field">
      <span>{tr(lang, '전공', '专业')}</span>
      <select data-testid={prefix + '-major'} value={majorId} disabled={disabled || !college} required={required}
        onChange={event => onChange(college, event.currentTarget.value)}>
        <option value="" disabled>{tr(lang, '전공을 선택하세요', '请选择专业')}</option>
        {college?.majors.map(item => <option key={item.id} value={item.id}>{catalogName(item.name, lang)}</option>)}
      </select>
    </label>
  </>;
}
