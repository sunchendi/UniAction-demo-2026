export type Lang = 'ko' | 'zh' | 'en' | 'fr' | 'ru' | 'es' | 'de' | 'pt';
export type Localized = string | ({ko:string;zh:string} & Partial<Record<Lang,string>>);
export type MatchStatus = 'conditions_met' | 'conditions_not_met' | 'missing_information' | 'needs_staff_review';
export type Scope = 'none' | 'case_only' | 'tasks_and_cases';
export interface Account {id:string;role:string;school_id:string;label:Localized;is_demo?:boolean;username?:string}
export interface Rule {op:string;field?:string;value?:unknown;children?:Rule[];evidence?:string}
export interface Reason {field?:string;op:string;result:boolean|null;actual?:unknown;expected?:unknown;evidence?:string;message?:Localized}
export interface Match {status:MatchStatus;reasons:Reason[];missing_fields:string[];needs_staff_review:boolean}
export interface Task {id:string;template_id:string;student_id:string;notice_id:string;notice_version:number;title:Localized;description:Localized;task_type:string;required_or_suggested:string;source_evidence:string;official_due_at:string|null;suggested_start_at:string|null;depends_on:string[];status:string;place?:CampusPlace}
export interface Document {id:string;title:Localized;evidence:string}
export interface Notice {id:string;school_id:string;title:Localized;category:string;version:number;publication_status:string;source_text:string;source_url:string;source_hash:string;reviewed_by:string|null;reviewed_at:string|null;eligibility_rules:Rule;required_documents:Document[];official_deadline:string|null;application_window:unknown;application_url:string|null;application_link_type:'official'|'demo'|'unknown';office_contact:{name:Localized;email:string|null;phone:string|null;evidence:string;is_demo:boolean}|null;task_templates:unknown[];evidence:Record<string,string>;ambiguities:unknown[];change_summary:Localized;extraction_mode?:string;review_checks?:ReviewChecks;match?:Match;application_state?:ApplicationState;changes?:{field:string;before:unknown;after:unknown}[]}
export type ApplicationState = string | {status:string;opens_at?:string;closes_at?:string;date_precision?:string;timezone?:string;now?:string};
export interface Detail {notice:Notice;match?:Match;tasks:Task[];task_places?:Record<string,CampusPlace>;versions:Notice[];application_state:ApplicationState;submission_status:string|{status:string}|null;sharing_scope:Scope}
export interface Profile {school_id:string;program_type:string;enrollment_status:string;year:number|null;semester:number|null;department_id:string;college_id:string|null;major_id:string|null;international_student:boolean|null;gpa_value:number|null;gpa_scale:number|null;gpa_period:string|null;current_dorm_resident:boolean|null;language_qualification:string|null;[key:string]:unknown}
export interface CatalogName { ko: string; zh: string; en: string }
export interface CollegeOption { id: string; name: CatalogName; department_id: string; majors: { id: string; name: CatalogName }[] }
export interface SchoolOption { id: string; name: CatalogName; source_url: string; colleges: CollegeOption[] }
export interface HelpCase {id:string;student_id:string;notice_id:string;school_id:string;message:string;sharing_scope:Scope;current_sharing_scope?:Scope;status:string;response:string|null;created_at:string;updated_at:string}
export interface Source {id:string;title:Localized;source_text:string}

export interface ReviewDuplicate {
  id: string;
  title: Localized;
  reasons: ('same_source' | 'same_link' | 'same_title')[];
}
export interface ReviewChecks {
  missing_deadline: boolean;
  missing_evidence: boolean;
  duplicates: ReviewDuplicate[];
}

export interface StudentNoticePreview {
  source_text: string;
  source_url: string;
  title: string;
  dates: string[];
  materials: string[];
}
export interface StudentNoticeReceipt { notice_id: string; publication_status: string }

export interface CalendarEvent {
  id: string;
  kind: 'deadline' | 'preparation';
  notice_id: string;
  notice_title: Localized;
  title: Localized;
  starts_at: string;
  task_id: string | null;
  version: number;
}
export interface StudentCalendar {
  month: string;
  today: string;
  events: CalendarEvent[];
}

export interface ApplicationFollowup {
  status: 'waiting_result' | 'needs_documents' | 'result_checked';
  next_check_on: string | null;
  note: string;
}
export interface TrackedApplication {
  notice_id: string;
  title: Localized;
  latest_version: number;
  submitted_version: number;
  reported_at: string;
  followup: ApplicationFollowup;
}
export interface StudentApplications { today: string; items: TrackedApplication[] }

interface TodayNotice { notice_id: string; title: Localized }
interface TodayTask { id: string; title: Localized }
export interface TodayActions {
  upcoming: (TodayNotice & {
    deadline: string | null;
    match_status: MatchStatus;
    tasks: (TodayTask & { suggested_start_at: string | null })[];
  })[];
  changes: (TodayNotice & { version: number; summary: Localized; tasks: TodayTask[] })[];
  missing: (TodayNotice & { fields: string[] })[];
}

export type OnboardingStage = 'before_arrival' | 'first_week' | 'term_start';
export interface CampusPlace {
  id: string;
  name: Localized;
  building: Localized;
  building_number: string;
  floor: number;
  hours: { label: Localized; time: Localized }[];
  note: Localized;
  map_url: string;
  sources: { label: Localized; url: string }[];
}
export interface OnboardingItem {
  id: string;
  stage: OnboardingStage;
  title: Localized;
  steps: Localized[];
  source_url: string;
  completed: boolean;
  place?: CampusPlace | null;
}
export interface OnboardingChecklist {
  program_type: Profile['program_type'];
  items: OnboardingItem[];
}
