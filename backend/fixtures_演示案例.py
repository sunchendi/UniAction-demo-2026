"""Fictional notices and preset students; school name is a presentation label."""
from copy import deepcopy
from hashlib import sha256

SCHOOL = "hanyang_demo"
SCHOOL_NAME = "Hanyang University / 한양대학교 / 汉阳大学"
DEMO_TIME = "2026-10-07T10:00:00+09:00"


def bi(ko, zh):
    return {"ko": ko, "zh": zh}


ACCOUNTS = [
    {"id": "A", "role": "student", "school_id": SCHOOL, "label": bi("학생 A · 공학부 2학년", "学生 A · 工科二年级")},
    {"id": "B", "role": "student", "school_id": SCHOOL, "label": bi("학생 B · 경영 석사", "学生 B · 商科硕士")},
    {"id": "C", "role": "student", "school_id": SCHOOL, "label": bi("학생 C · 정보 미입력", "学生 C · 信息待补充")},
    {"id": "staff", "role": "staff", "school_id": SCHOOL, "label": bi("국제교류처 담당자", "国际交流处工作人员")},
    {"id": "other_staff", "role": "staff", "school_id": "other_demo", "label": bi("타교 담당자 · 접근 검증", "其他学校工作人员 · 访问验证")},
]

PROFILES = {
    "A": {"school_id": SCHOOL, "program_type": "undergraduate", "enrollment_status": "enrolled", "year": 2, "semester": 3, "department_id": "engineering", "international_student": True, "gpa_value": 3.8, "gpa_scale": 4.5, "gpa_period": "previous_semester", "current_dorm_resident": True, "language_qualification": None},
    "B": {"school_id": SCHOOL, "program_type": "master", "enrollment_status": "enrolled", "year": None, "semester": 1, "department_id": "business", "international_student": True, "gpa_value": None, "gpa_scale": None, "gpa_period": None, "current_dorm_resident": False, "language_qualification": None},
    "C": {"school_id": SCHOOL, "program_type": "undergraduate", "enrollment_status": "enrolled", "year": 2, "semester": 3, "department_id": "engineering", "international_student": True, "gpa_value": None, "gpa_scale": None, "gpa_period": None, "current_dorm_resident": None, "language_qualification": None},
}


def leaf(op, field, value, evidence):
    return {"op": op, "field": field, "value": value, "children": [], "evidence": evidence}


def make_notice(id, title, category, conditions, docs, deadline, rules, version=1):
    url = f"https://demo.invalid/hanyang/{id.lower()}/apply"
    contact = "문의: 국제교류처 데모 담당자, demo-office@hanyang.invalid (실제 연락처 아님)."
    document_line = "필수 제출 자료: " + (", ".join(doc[1] for doc in docs) if docs else "별도 제출 자료 없음") + "."
    deadline_line = f"신청 마감: {deadline[:10]} {deadline[11:16]}, 한국시간 Asia/Seoul (UTC+09:00)."
    window_line = f"신청 기간: 2026-10-01 09:00부터 {deadline[:10]} {deadline[11:16]}까지, 한국시간."
    application_line = f"신청 방법: {url} 에서 신청서를 제출하세요. 이 주소는 데모용 자리표시자이며 실제 신청은 진행되지 않습니다."
    source = "\n".join([
        "[가상 데모 공지 · 한양대학교 공식 공지가 아닙니다]", SCHOOL_NAME,
        f"공고 번호: {id}, 버전: {version}", f"제목: {title[0]}", "공고일: 2026-10-01, 한국시간.",
        "지원 대상: " + conditions, document_line, window_line, deadline_line,
        application_line, contact, "조건 충족 여부와 최종 접수·선발 결과는 다릅니다. 최종 확인은 학교 담당자가 수행합니다.",
    ])
    tasks = []
    documents = []
    for key, ko, zh in docs:
        documents.append({"id": key, "title": bi(ko, zh), "evidence": document_line})
        tasks.append({"id": key, "title": bi(ko + " 준비", "准备" + zh), "description": bi("공지에 명시된 필수 자료를 준비하세요.", "准备通知明确要求的必需材料。"), "task_type": "document", "required_or_suggested": "required", "source_evidence": document_line, "depends_on": [], "uses_deadline": False, "suggested_lead_days": 3})
    tasks.append({"id": "prepare", "title": bi("준비 일정 확인", "确认准备安排"), "description": bi("시스템 제안: 마감 3일 전 준비 시작. 공지에 처리 기간이 없으므로 조정할 수 있습니다.", "系统建议：截止前 3 天开始准备。原文未说明办理时间，可调整。"), "task_type": "prepare", "required_or_suggested": "suggested", "source_evidence": "", "depends_on": [], "uses_deadline": False, "suggested_lead_days": 3})
    tasks.append({"id": "apply", "title": bi("신청서 제출 확인", "确认申请表提交"), "description": bi("데모 링크를 확인한 뒤 제출 상태를 직접 기록하세요. 학교 접수 확인이 아닙니다.", "确认演示入口后自行记录提交状态；这不代表学校确认收到。"), "task_type": "apply", "required_or_suggested": "required", "source_evidence": application_line, "depends_on": [d[0] for d in docs], "uses_deadline": True, "suggested_lead_days": None})
    return {
        "id": id, "school_id": SCHOOL, "title": bi(*title), "category": category,
        "source_url": f"https://demo.invalid/hanyang/{id.lower()}/v{version}", "source_text": source,
        "source_hash": sha256(source.encode("utf-8")).hexdigest(), "version": version,
        "publication_status": "approved", "reviewed_by": "staff", "reviewed_at": DEMO_TIME,
        "eligibility_rules": {"op": "all", "field": None, "value": None, "children": rules, "evidence": conditions},
        "required_documents": documents, "official_deadline": deadline,
        "application_window": {"opens_at": "2026-10-01T09:00:00+09:00", "closes_at": deadline},
        "application_url": url, "application_link_type": "demo",
        "office_contact": {"name": bi("국제교류처 데모 담당자", "国际交流处演示工作人员"), "email": "demo-office@hanyang.invalid", "phone": None, "evidence": contact, "is_demo": True},
        "task_templates": tasks,
        "evidence": {"official_deadline": deadline_line, "application_window": window_line, "application_url": application_line},
        "ambiguities": [], "change_summary": bi("최초 승인 버전 (고정 데모 데이터)", "首次审核版本（固定演示数据）"),
        "extraction_mode": "fixed_demo",
    }


def fixtures():
    n1_condition = "외국인 학부 재학생, 2학년 이상. 직전 학기 GPA 4.5 만점 기준 3.5 이상."
    n1_rules = [leaf("is_true", "international_student", None, "외국인 학부 재학생"), leaf("eq", "program_type", "undergraduate", "외국인 학부 재학생"), leaf("eq", "enrollment_status", "enrolled", "외국인 학부 재학생"), leaf("gte", "year", 2, "2학년 이상"), leaf("eq", "gpa_period", "previous_semester", "직전 학기 GPA"), leaf("eq", "gpa_scale", 4.5, "4.5 만점 기준"), leaf("gte", "gpa_value", 3.5, "3.5 이상")]
    n1 = make_notice("N1", ("외국인 학부생 장학금", "外国人本科生奖学金"), "scholarship", n1_condition, [("transcript", "직전 학기 성적증명서", "上一学期成绩证明"), ("application_form", "신청서", "申请表")], "2026-10-16T18:00:00+09:00", n1_rules)
    n2_condition = "외국인 재학생, 입학 후 첫 번째 학기. 학위 과정 유형 제한 없음."
    n2 = make_notice("N2", ("외국인 신입생 환영 활동", "外国新入学学生活动"), "activity", n2_condition, [], "2026-10-09T18:00:00+09:00", [leaf("is_true", "international_student", None, "외국인 재학생"), leaf("eq", "enrollment_status", "enrolled", "외국인 재학생"), leaf("eq", "semester", 1, "첫 번째 학기")])
    n3_condition = "외국인 재학생이며 현재 학교 기숙사 거주자."
    n3 = make_notice("N3", ("외국인 학생 기숙사 연장", "外国学生宿舍续住"), "dormitory", n3_condition, [("renewal_form", "기숙사 연장 신청서", "续住申请表")], "2026-10-20T18:00:00+09:00", [leaf("is_true", "international_student", None, "외국인 재학생"), leaf("eq", "enrollment_status", "enrolled", "외국인 재학생"), leaf("is_true", "current_dorm_resident", None, "현재 학교 기숙사 거주자")])
    n4_condition = "경영학 계열 재학생. 학위 과정 유형 제한 없음."
    n4 = make_notice("N4", ("경영학 학생 교류 활동", "商科学生交流活动"), "activity", n4_condition, [], "2026-10-15T18:00:00+09:00", [leaf("eq", "enrollment_status", "enrolled", "경영학 계열 재학생"), leaf("eq", "department_id", "business", "경영학 계열")])
    n5_condition = "외국인 재학생이며 한국어로 원활하게 의사소통할 수 있는 학생. TOPIK 점수 또는 등급 기준은 명시하지 않습니다."
    n5 = make_notice("N5", ("외국인 학생 자원봉사 활동", "外国学生志愿活动"), "activity", n5_condition, [], "2026-10-14T18:00:00+09:00", [leaf("is_true", "international_student", None, "외국인 재학생"), leaf("eq", "enrollment_status", "enrolled", "외국인 재학생"), leaf("needs_staff_review", "language_qualification", None, "한국어로 원활하게 의사소통할 수 있는 학생")])
    n5["ambiguities"] = [bi("한국어 의사소통 기준은 담당자 확인 필요. TOPIK 기준을 추정하지 않습니다.", "韩语顺畅沟通的标准需要工作人员确认；不推定 TOPIK 门槛。")]
    n1v2 = make_notice("N1", ("외국인 학부생 장학금", "外国人本科生奖学金"), "scholarship", n1_condition, [("transcript", "직전 학기 성적증명서", "上一学期成绩证明"), ("application_form", "신청서", "申请表"), ("enrollment_certificate", "재학증명서", "在学证明")], "2026-10-14T18:00:00+09:00", deepcopy(n1_rules), version=2)
    n1v2["publication_status"] = "draft"
    n1v2["reviewed_by"] = n1v2["reviewed_at"] = None
    n1v2["change_summary"] = bi("마감이 10월 14일 18:00로 앞당겨짐. 재학증명서 추가. 지원 조건은 동일.", "截止提前至 10 月 14 日 18:00；新增在学证明；申请条件不变。")
    return [n1, n2, n3, n4, n5], n1v2


BASE_NOTICES, N1_V2 = fixtures()
EXPECTED_RESULTS = {
    "A": ["conditions_met", "conditions_not_met", "conditions_met", "conditions_not_met", "needs_staff_review"],
    "B": ["conditions_not_met", "conditions_met", "conditions_not_met", "conditions_met", "needs_staff_review"],
    "C": ["missing_information", "conditions_not_met", "missing_information", "conditions_not_met", "needs_staff_review"],
}


def all_sources():
    return [{"id": n["id"] if n["version"] == 1 else n["id"] + "-v2", "title": n["title"], "source_text": n["source_text"]} for n in [*BASE_NOTICES, N1_V2]]
