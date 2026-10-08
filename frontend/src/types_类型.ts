export type Lang = 'ko' | 'zh';
export type Localized = string | {ko:string;zh:string};
export type MatchStatus = 'conditions_met' | 'conditions_not_met' | 'missing_information' | 'needs_staff_review';
export type Scope = 'none' | 'case_only' | 'tasks_and_cases';
export interface Account {id:string;role:string;school_id:string;label:Localized;is_demo?:boolean;username?:string}
export interface Rule {op:string;field?:string;value?:unknown;children?:Rule[];evidence?:string}
export interface Reason {field?:string;op:string;result:boolean|null;actual?:unknown;expected?:unknown;evidence?:string;message?:Localized}
export interface Match {status:MatchStatus;reasons:Reason[];missing_fields:string[];needs_staff_review:boolean}
export interface Task {id:string;student_id:string;notice_id:string;notice_version:number;title:Localized;description:Localized;task_type:string;required_or_suggested:string;source_evidence:string;official_due_at:string|null;suggested_start_at:string|null;depends_on:string[];status:string}
export interface Document {id:string;title:Localized;evidence:string}
export interface Notice {id:string;school_id:string;title:Localized;category:string;version:number;publication_status:string;source_text:string;source_url:string;source_hash:string;reviewed_by:string|null;reviewed_at:string|null;eligibility_rules:Rule;required_documents:Document[];official_deadline:string|null;application_window:unknown;application_url:string|null;application_link_type:'official'|'demo'|'unknown';office_contact:{name:Localized;email:string|null;phone:string|null;evidence:string;is_demo:boolean}|null;task_templates:unknown[];evidence:Record<string,string>;ambiguities:unknown[];change_summary:Localized;extraction_mode?:string;match?:Match;application_state?:ApplicationState;changes?:{field:string;before:unknown;after:unknown}[]}
export type ApplicationState = string | {status:string;opens_at?:string;closes_at?:string;date_precision?:string;timezone?:string;now?:string};
export interface Detail {notice:Notice;match?:Match;tasks:Task[];versions:Notice[];application_state:ApplicationState;submission_status:string|{status:string}|null;sharing_scope:Scope}
export interface Profile {school_id:string;program_type:string;enrollment_status:string;year:number|null;semester:number|null;department_id:string;international_student:boolean|null;gpa_value:number|null;gpa_scale:number|null;gpa_period:string|null;current_dorm_resident:boolean|null;language_qualification:string|null;[key:string]:unknown}
export interface HelpCase {id:string;student_id:string;notice_id:string;school_id:string;message:string;sharing_scope:Scope;current_sharing_scope?:Scope;status:string;response:string|null;created_at:string;updated_at:string}
export interface Source {id:string;title:Localized;source_text:string}
