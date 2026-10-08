import type { Lang, Localized } from './types_类型';
export const tr = (lang:Lang, ko:string, zh:string) => lang==='ko'?ko:zh;
export const localize = (value:Localized | unknown, lang:Lang):string => {
  if(value==null)return '—';
  if(typeof value==='string')return value;
  if(typeof value==='object' && 'ko' in value)return String((value as {ko:unknown;zh:unknown})[lang] ?? (value as {ko:unknown}).ko);
  return typeof value==='object'?JSON.stringify(value):String(value);
};
export const statusLabels:Record<string,[string,string]>={conditions_met:['조건 충족','条件满足'],conditions_not_met:['조건 불충족','条件不满足'],missing_information:['정보 부족','信息不足'],needs_staff_review:['담당자 확인 필요','需要工作人员确认'],todo:['준비 전','待办'],in_progress:['진행 중','进行中'],done:['완료','完成'],needs_help:['도움 필요','需要帮助'],requires_reconfirmation:['다시 확인 필요','需要重新确认'],draft:['초안','草稿'],under_review:['검토 중','审核中'],approved:['승인됨','已审核'],archived:['보관됨','已归档'],open:['신청 가능','申请开放'],not_open:['신청 시작 전','尚未开放'],upcoming:['신청 시작 전','尚未开放'],closed:['신청 마감','申请截止'],expired:['신청 마감','申请截止'],unknown:['기간 확인 필요','需确认申请期间'],resolved:['처리됨','已处理'],in_review:['처리 중','处理中']};
export const label=(key:string,lang:Lang)=>statusLabels[key]?.[lang==='ko'?0:1]??key;
Object.assign(statusLabels,{case_open:['접수된 문의','待处理案例'],needs_confirmation:['신청 기간 확인 필요','需要确认申请期间'],deadline_time_unknown:['마감 시각 확인 필요','需要确认截止时刻']});
export const fields:Record<string,[string,string]>={program_type:['과정','学位类型'],enrollment_status:['학적 상태','学籍状态'],year:['학년','年级'],semester:['입학 후 학기','入学后学期'],department_id:['전공 분류','院系分类'],international_student:['외국인 학생 여부','是否为外国学生'],gpa_value:['학점','GPA 数值'],gpa_scale:['학점 만점','GPA 满分制'],gpa_period:['학점 기간','GPA 对应期间'],current_dorm_resident:['현재 기숙사 거주','当前是否住宿舍'],language_qualification:['언어 사용 정보','语言资格信息'],school_id:['소속 학교','所属学校']};
export const fieldLabel=(key:string,lang:Lang)=>fields[key]?.[lang==='ko'?0:1]??key;
Object.assign(fields,{username:['아이디','用户名'],password:['비밀번호','密码'],display_name:['표시 이름','显示名称']});
export const valueLabels:Record<string,[string,string]>={language:['어학 과정','语言课程'],undergraduate:['학부','本科'],master:['석사','硕士'],doctor:['박사','博士'],enrolled:['재학','在读'],leave:['휴학','休学'],graduated:['졸업','已毕业'],engineering:['공학','工科'],business:['경영·상경','商科'],humanities:['인문','人文'],previous_semester:['직전 학기','上一学期'],cumulative:['전체 누적','累计'],current_semester:['현재 학기','本学期'],true:['예','是'],false:['아니요','否']};
export const valueLabel=(value:unknown,lang:Lang)=>value==null?tr(lang,'미입력 / 모름','未填写 / 不确定'):valueLabels[String(value)]?.[lang==='ko'?0:1]??String(value);
export const dateLabel=(date:string|null|undefined,lang:Lang)=>{
  if(!date)return tr(lang,'미지정','未指定');
  if(/^\d{4}-\d{2}-\d{2}$/.test(date))return `${date} · ${tr(lang,'시각 미지정','时刻未指定')} (Asia/Seoul)`;
  try{return new Intl.DateTimeFormat(lang==='ko'?'ko-KR':'zh-CN',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(date))+' (KST · UTC+09:00)';}catch{return date;}
};
