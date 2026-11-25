"""ERICA service locations from the university's public guides."""

from .fixtures_演示案例 import BASE_NOTICES, N1_V2, SCHOOL, bi


ERICA_MAP_URL = "https://www.hanyang.ac.kr/map_erica"
WELFARE_BUILDING = bi("학생복지관", "学生福利馆")
OFFICE_HOURS = (
    {"label": bi("학기 중", "学期内"), "time": "08:30–17:30"},
    {"label": bi("방학 중", "假期内"), "time": "10:00–17:00"},
    {"label": bi("점심시간", "午休"), "time": "12:00–13:00"},
)

CERTIFICATE_KIOSK = {
    "id": "certificate-kiosk",
    "name": bi("무인증명발급기", "自助证明机"),
    "building": WELFARE_BUILDING,
    "building_number": "102",
    "floor": 2,
    "hours": [{"label": bi("이용 가능", "可使用"), "time": bi("24시간", "24 小时")}],
    "note": bi("오른쪽 출입구로 들어가 계단실을 확인하세요.", "从右侧入口进入，在楼梯间找自助证明机。"),
    "map_url": ERICA_MAP_URL,
    "sources": [
        {"label": bi("증명 발급 안내", "证明开具指南"), "url": "https://ehaksa.hanyang.ac.kr/ko/certificate"},
    ],
}

INTERNATIONAL_OFFICE = {
    "id": "international-office",
    "name": bi("ERICA 국제처", "ERICA 国际处"),
    "building": WELFARE_BUILDING,
    "building_number": "102",
    "floor": 3,
    "hours": OFFICE_HOURS,
    "note": bi("평일에 상담할 수 있으며 공휴일은 쉽니다. 오리엔테이션 장소는 해당 안내에서 확인하세요.",
               "周一至周五可咨询，公休日休息。迎新活动地点请查看当期通知。"),
    "map_url": ERICA_MAP_URL,
    "sources": [
        {"label": bi("국제처 방문 안내", "国际处来访指南"), "url": "https://global.hanyang.ac.kr/s1/s1_4.php"},
    ],
}

DORMITORY_OFFICE = {
    "id": "dormitory-office",
    "name": bi("창의인재원 행정팀", "创意人才院宿舍行政办公室"),
    "building": bi("창의관", "创意馆"),
    "building_number": "501",
    "floor": 2,
    "hours": OFFICE_HOURS,
    "note": bi("기숙사 문의처입니다. 접수와 입주 절차는 본인 생활관의 안내를 확인하세요.",
               "可在此咨询宿舍事项。提交和入住流程请查看本人宿舍楼的通知。"),
    "map_url": ERICA_MAP_URL,
    "sources": [
        {"label": bi("기숙사 연락처와 업무시간", "宿舍联系方式与办公时间"),
         "url": "https://hydorm.hanyang.ac.kr/service/content/intro_02/index.do"},
        {"label": bi("기숙사 생활안내", "宿舍生活指南"),
         "url": "https://hydorm.hanyang.ac.kr/service/content/info_03/index.do?tab=cont03"},
    ],
}

TASK_PLACES = {
    ("N1", "transcript"): CERTIFICATE_KIOSK,
    ("N1", "enrollment_certificate"): CERTIFICATE_KIOSK,
    ("N3", "renewal_form"): DORMITORY_OFFICE,
}
DEMO_TASK_TITLES = {
    (notice["id"], notice["source_hash"], task["id"]): task["title"]["ko"]
    for notice in (*BASE_NOTICES, N1_V2)
    for task in notice["task_templates"]
    if (notice["id"], task["id"]) in TASK_PLACES
}


def task_place_details(notice, tasks):
    if notice.school_id != SCHOOL or notice.extraction_mode != "fixed_demo" or notice.publication_status != "approved":
        return tasks, {}

    # The approved templates provide locations even before a student creates tasks.
    places = {
        template.id: TASK_PLACES[(notice.id, template.id)]
        for template in notice.task_templates
        if template.task_type == "document"
        and template.title.ko == DEMO_TASK_TITLES.get((notice.id, notice.source_hash, template.id))
    }
    result = []
    for task in tasks:
        template = task["template_id"]
        expected = DEMO_TASK_TITLES.get((notice.id, notice.source_hash, template))
        if template in places and task["task_type"] == "document" and task["title"]["ko"] == expected:
            result.append({**task, "place": places[template]})
        else:
            result.append(task)
    return result, places
