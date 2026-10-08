import { fieldLabel, tr } from './i18n_双语';
import type { Lang } from './types_类型';
export class ApiError extends Error {status:number;constructor(message:string,status:number){super(message);this.status=status;}}
function errorMessage(detail:unknown,status:number):string{
  const lang:Lang=localStorage.getItem('campus-lang')==='zh'?'zh':'ko';const t=(ko:string,zh:string)=>tr(lang,ko,zh);
  const messages:Record<string,[string,string]>={
    login_error:['아이디 또는 비밀번호가 맞지 않습니다. 입력을 확인하고 다시 시도해 주세요.','用户名或密码错误，请检查输入后重试。'],
    session_invalid:['로그인이 만료되었습니다. 다시 로그인하거나 데모 계정을 선택해 주세요.','登录已失效，请重新登录或选择演示账号。'],
    username_taken:['이미 사용 중인 아이디입니다. 다른 아이디를 선택해 주세요.','此用户名已被使用，请选择其他用户名。'],
    rate_limited:['로그인 또는 등록 실패가 반복되었습니다. 15분 후 다시 시도해 주세요.','登录或注册失败次数过多，请 15 分钟后重试。'],
    csrf_origin_rejected:['허용된 로컬 주소에서 다시 열어 주세요: http://127.0.0.1:8000','请通过允许的本地地址重新打开：http://127.0.0.1:8000'],
    demo_source_unknown:['고정 데모 모드는 6개 완전한 원문만 인식합니다. 데모 원문을 선택하거나 수동 초안을 작성해 주세요.','固定演示模式只识别六份完整预设原文。请选择演示原文，或手动补充草稿。'],
    ai_not_configured:['실제 AI가 설정되지 않았습니다. 서버 API 설정을 확인하거나 고정 데모 / 수동 초안을 사용하세요.','真实 AI 尚未配置。请检查服务端 API 设置，或继续固定演示 / 手工草稿。'],
    ai_timeout:['AI 요청 시간이 초과되었습니다. 다시 시도하거나 수동 초안을 작성하세요. 결과는 게시되지 않았습니다.','AI 请求超时。请重试或手工补充草稿，结果尚未发布。'],
    ai_invalid_return:['AI가 완전한 구조화 초안을 반환하지 않았습니다. 원문을 줄여 다시 시도하거나 수동으로 보완하세요.','AI 未返回完整结构化草稿。请缩短原文重试，或手工补充。'],
    ai_quota_unavailable:['AI 할당량 또는 요청 제한에 도달했습니다. 서비스 설정을 확인하거나 수동 초안을 사용하세요.','AI 额度或速率限制。请检查服务账户额度，或使用人工草稿。'],
    ai_connection_failed:['AI 서비스에 연결할 수 없습니다. 네트워크를 확인하거나 수동 초안을 사용하세요.','无法连接 AI 服务。请检查网络，或使用人工草稿。'],
    ai_service_unavailable:['AI 서비스가 오류를 반환했습니다. 모델 설정을 확인하거나 수동 초안을 사용하세요.','AI 服务返回错误。请核对模型配置，或使用人工草稿。'],
    ai_semantic_invalid:['AI 초안의 필드·규칙·원문 근거·과제 의존성이 유효하지 않습니다. 수동으로 보완하세요. 초안은 저장/승인되지 않았습니다.','AI 草稿字段、规则、原文依据或任务依赖无效。请手工修正，草稿未保存或批准。']
  };
  if(detail&&typeof detail==='object'&&!Array.isArray(detail)){
    const structured=detail as {code?:string;message?:string};
    if(structured.code&&messages[structured.code])return messages[structured.code][lang==='ko'?0:1];
    if(structured.message)return structured.message;
  }
  if(Array.isArray(detail)){
    const fields=[...new Set(detail.map(item=>(item as {loc?:string[]}).loc?.filter(x=>x!=='body').map(x=>fieldLabel(String(x),lang)).join(' › ')).filter(Boolean))].slice(0,8);
    return t('입력값을 확인해 주세요. 필수 필드, 허용 규칙, 원문 근거와 날짜 형식을 검토하세요.','请检查输入内容，核对必填字段、支持的规则、原文依据和日期格式。')+(fields.length?' '+fields.join(' · '):'');
  }
  if(typeof detail==='string'){
    if(lang==='zh')return detail;
    if(detail.includes('依赖的材料'))return '먼저 의존하는 필수 자료 과제를 완료해 주세요. 학교 신청 확인과는 별개입니다.';
    if(detail.includes('跨学校')||detail.includes('不属于当前学校'))return '현재 학교의 허용 범위를 벗어난 접근입니다. 소속 학교와 계정을 확인하세요.';
    if(detail.includes('未授权')||detail.includes('撤销')||detail.includes('共享授权'))return '이 정보에 대한 공유 권한이 없거나 철회되었습니다. 학생이 선택한 공유 범위를 확인하세요.';
    if(detail.includes('开始人工审核'))return '중요 조건, 자료, 날짜와 원문을 확인한 뒤 검토를 시작하고 버전을 승인하세요.';
    if(detail.includes('不可覆盖')||detail.includes('不可修改')||detail.includes('不可批准'))return '기존 승인 내용이나 원문을 덮어쓸 수 없습니다. 새 버전으로 가져와 검토해 주세요.';
    if(detail.includes('明确不满足'))return '현재 정보로 명확한 조건을 충족하지 않습니다. 관련 정보를 먼저 확인해 주세요.';
    if(detail.includes('已经审核'))return '이미 승인된 버전입니다. 새 버전을 가져와 검토할 수 있습니다.';
    if(detail.includes('工作人员角色'))return '담당자 데모 계정으로 전환해 주세요.';
    if(detail.includes('任务不存在'))return '과제가 없거나 본인에게 접근 권한이 없습니다.';
    if(detail.includes('通知不存在'))return '공지가 없거나 아직 승인되지 않았습니다. 공지 목록을 새로 불러오세요.';
  }
  if(status===403)return t('현재 계정에 접근 권한이 없습니다. 계정과 공유 범위를 확인해 주세요.','当前账号无访问权限，请检查角色、所属学校及共享范围。');
  if(status===401)return t('로그인이 만료되었습니다. 개인 계정으로 다시 로그인하거나 데모 계정을 선택해 주세요.','登录已失效，请重新登录个人账号或选择演示账号。');
  if(status===422)return t('입력 내용을 확인해 주세요. 중요한 필드가 유효해야 저장할 수 있습니다.','请检查输入内容，重要字段通过校验后才能保存。');
  return t('요청을 처리하지 못했습니다. 입력 내용을 확인하고 다시 시도해 주세요.','请求未完成，请检查输入并重试。');
}
export async function api<T>(account:string,path:string,method='GET',body?:unknown):Promise<T>{
  const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),65000);
  try{
    const response=await fetch(`/api${path}`,{method,credentials:'same-origin',headers:{'Content-Type':'application/json',...(account?{'X-Demo-Account':account}:{})},...(body!==undefined?{body:JSON.stringify(body)}:{}),signal:controller.signal});
    const data=await response.json().catch(()=>({detail:'Invalid response'}));
    if(!response.ok){if(response.status===401&&!path.startsWith('/auth/'))window.dispatchEvent(new Event('uniaction-session-expired'));throw new ApiError(errorMessage(data.detail??data,response.status),response.status);}
    return data as T;
  }catch(error){if(error instanceof ApiError)throw error;if(error instanceof Error&&error.name==='AbortError')throw new ApiError('요청 시간이 초과되었습니다. / 请求超时，请重试。',408);throw new ApiError('서버에 연결할 수 없습니다. 실행 상태를 확인해 주세요. / 无法连接服务，请检查后端是否启动。',0);}finally{clearTimeout(timer);}
}
