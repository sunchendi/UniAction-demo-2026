import { useEffect, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { ArrowRight, LockKeyhole, UserRound } from 'lucide-react';
import type { Lang, SchoolOption } from './types_类型';
import { tr, valueLabel } from './i18n_多语言';
import AcademicFields, { catalogName } from './AcademicFields_院系专业选择';

export type AuthMode = 'demo' | 'login' | 'register';
export interface AuthForm {username:string;password:string;display_name?:string;program_type?:string;enrollment_status?:string;school_id?:string;college_id?:string;major_id?:string}
interface Props {mode:AuthMode;setMode:(mode:AuthMode)=>void;lang:Lang;busy:boolean;error:string;submit:(data:AuthForm)=>Promise<void>;children:ReactNode;schools:SchoolOption[]}

export default function AuthPanel({mode,setMode,lang,busy,error,submit,children,schools}:Props){
  const t=(ko:string,zh:string)=>tr(lang,ko,zh);
  const [username,setUsername]=useState('');const [password,setPassword]=useState('');
  const [displayName,setDisplayName]=useState('');const [program,setProgram]=useState('');const [enrollment,setEnrollment]=useState('');const [validation,setValidation]=useState('');
  const [schoolId, setSchoolId] = useState('');
  const [collegeId, setCollegeId] = useState('');
  const [majorId, setMajorId] = useState('');
  const school = schools.find(item => item.id === schoolId);
  useEffect(()=>{setValidation('');},[lang]);
  const register=mode==='register';
  function changeMode(next:AuthMode){setValidation('');setPassword('');setMode(next);}
  async function handleSubmit(event:FormEvent){
    event.preventDefault();setValidation('');
    if(!/^[A-Za-z0-9_.-]{3,32}$/.test(username.trim())){setValidation(t('아이디는 3–32자의 영문·숫자·밑줄·점·하이픈으로 입력해 주세요.','用户名需为 3–32 位英文字母、数字、下划线、点或连字符。'));return;}
    const passwordLength = Array.from(password).length;
    if (register && (passwordLength < 10 || passwordLength > 32)) {
      setValidation(t('비밀번호를 10–32자로 입력해 주세요.', '密码需为 10–32 个字符。'));
      return;
    }
    if (!passwordLength) { setValidation(t('비밀번호를 입력해 주세요.', '请输入密码。')); return; }
    if(register&&(!displayName.trim()||displayName.trim().length>50)){setValidation(t('표시 이름을 1–50자로 입력해 주세요.','显示名称需为 1–50 个字符。'));return;}
    if(register&&(!program||!enrollment)){setValidation(t('과정과 학적 상태를 선택해 주세요.','请选择学位类型和学籍状态。'));return;}
    if(register&&(!school||!collegeId||!majorId)){setValidation(t('학교, 단과대학과 전공을 선택해 주세요.','请选择学校、院系和专业。'));return;}
    await submit({username:username.trim(),password,...(register?{
      display_name:displayName.trim(),program_type:program,enrollment_status:enrollment,
      school_id:schoolId,college_id:collegeId,major_id:majorId,
    }:{})});
  }
  return <section className="login-card auth-card">
    <div className="auth-tabs" role="tablist" aria-label={t('계정 접근 방식','账号使用方式')}>
      <button type="button" data-testid="auth-login-tab" role="tab" aria-selected={mode==='login'} onClick={()=>changeMode('login')}>{t('개인 로그인','个人登录')}</button>
      <button type="button" data-testid="auth-register-tab" role="tab" aria-selected={register} onClick={()=>changeMode('register')}>{t('계정 만들기','创建账号')}</button>
      <button type="button" data-testid="auth-demo-tab" role="tab" aria-selected={mode==='demo'} onClick={()=>changeMode('demo')}>{t('데모 체험','演示体验')}</button>
    </div>
    <span className="eyebrow">{mode==='demo'?t('DEMO WORKSPACE','演示工作区'):t('MY LOCAL ACCOUNT','我的本地账号')}</span>
    <h2>{mode==='demo'?t('데모 계정 선택','选择演示账号'):register?t('내 계정 만들기','创建个人账号'):t('내 계정으로 로그인','登录个人账号')}</h2>
    <p>{mode==='demo'?t('같은 공지가 학생마다 어떻게 달라지는지 살펴보세요.','看看同一则通知如何对应不同学生。'):register?t('학점·학년 등 추가 정보는 필요한 공지에서 나중에 입력합니다.','GPA、年级等补充信息，可在相关通知需要时再填写。'):t('저장한 학생 정보와 준비 진행을 이어서 확인하세요.','继续查看已保存的学生资料和准备进度。')}</p>
    {(error||validation)&&<div className="auth-error" role="alert">{validation||error}</div>}
    {mode==='demo'?children:<form noValidate onSubmit={handleSubmit} className="auth-form">
      <label className="field"><span>{t('아이디','用户名')}</span><input data-testid="auth-username" aria-label={t('아이디','用户名')} value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username" autoCapitalize="none" spellCheck={false} minLength={3} maxLength={32} required/><small>{t('3–32자 · 영문, 숫자, _, ., -','3–32 位 · 英文、数字、_、.、-')}</small></label>
      <label className="field"><span>{t('비밀번호','密码')}</span><input data-testid="auth-password" aria-label={t('비밀번호','密码')} type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete={register?'new-password':'current-password'} required/>{register && <small>{t('10–32자', '10–32 个字符')}</small>}</label>
      {register&&<>
        <label className="field"><span>{t('표시 이름','显示名称')}</span><input data-testid="auth-display-name" aria-label={t('표시 이름','显示名称')} value={displayName} onChange={e=>setDisplayName(e.target.value)} autoComplete="nickname" minLength={1} maxLength={50} required/><small>{t('1–50자 · 화면에서 사용할 이름','1–50 个字符 · 用于页面展示')}</small></label>
        <div className="auth-registration-fields">
          <label className="field"><span>{t('과정','学位类型')}</span><select data-testid="auth-program" aria-label={t('과정','学位类型')} value={program} onChange={e=>setProgram(e.target.value)} required><option value="">{t('직접 선택해 주세요','请明确选择')}</option>{['language','undergraduate','master','doctor'].map(value=><option key={value} value={value}>{valueLabel(value,lang)}</option>)}</select></label>
          <label className="field"><span>{t('학적 상태','学籍状态')}</span><select data-testid="auth-enrollment" aria-label={t('학적 상태','学籍状态')} value={enrollment} onChange={e=>setEnrollment(e.target.value)} required><option value="">{t('직접 선택해 주세요','请明确选择')}</option>{['enrolled','leave','graduated'].map(value=><option key={value} value={value}>{valueLabel(value,lang)}</option>)}</select></label>
        </div>
        <label className="field"><span>{t('소속 학교','所属学校')}</span>
          <select data-testid="auth-school" value={schoolId} disabled={busy || !schools.length} required
            onChange={event => { setSchoolId(event.currentTarget.value); setCollegeId(''); setMajorId(''); setValidation(''); }}>
            <option value="" disabled>{t('학교를 선택하세요','请选择学校')}</option>
            {schools.map(item => <option key={item.id} value={item.id}>{catalogName(item.name, lang)}</option>)}
          </select>
        </label>
        {school && <p className="academic-catalog-link"><a href={school.source_url} target="_blank" rel="noreferrer">{t('공식 학과 안내','查看官方院系目录')}</a></p>}
        <div className="auth-registration-fields academic-registration-fields">
          <AcademicFields school={school} collegeId={collegeId} majorId={majorId} prefix="auth" lang={lang} required disabled={busy}
            onChange={(college, major) => { setCollegeId(college?.id ?? ''); setMajorId(major); setValidation(''); }}/>
        </div>
      </>}
      <button type="submit" data-testid="auth-submit" className="primary full-width" disabled={busy}>{register?<UserRound size={17}/>:<LockKeyhole size={17}/>}{busy?t('처리 중…','处理中…'):register?t('계정 만들고 정보 입력','创建账号并填写资料'):t('로그인','登录')}<ArrowRight size={17}/></button>
      <p className="microcopy"><LockKeyhole size={15}/>{t('개인 정보는 이 컴퓨터의 로컬 서비스에 저장됩니다. 학교 SSO나 정식 학교 계정이 아닙니다.','个人资料保存在此电脑的本地服务中。这不是学校 SSO 或正式学校账号。')}</p>
    </form>}
  </section>;
}
