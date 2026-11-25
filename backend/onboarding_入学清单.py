"""Suggested arrival tasks, with public guidance for the student's campus."""

from .campus_places_办事地点 import DORMITORY_OFFICE, INTERNATIONAL_OFFICE
from .fixtures_演示案例 import SCHOOL, bi
from .school_catalog_学校目录 import ERICA


DEGREE_PROGRAMS = {"undergraduate", "master", "doctor"}
LANGUAGE_PROGRAM = {"language"}
ITEMS = (
    {
        "id": "housing",
        "stage": "before_arrival",
        "title": bi("거주지와 입주 일정 확인", "确认住宿与入住安排"),
        "steps": [
            bi("기숙사를 신청했다면 본인 과정의 해당 학기 공지에서 선발 결과와 입주 일정을 확인하세요.",
               "如果申请了宿舍，请在对应学期和项目的通知中确认录取结果与入住日程。"),
            bi("기숙사 또는 교외 숙소의 주소와 입주 시 준비할 사항을 따로 정리하세요.",
               "记下宿舍或校外住处的地址及入住前需要准备的事项。"),
        ],
        "source_url": "https://hydorm.hanyang.ac.kr/service/content/info_04/index.do",
        "place": DORMITORY_OFFICE,
    },
    {
        "id": "campus-route",
        "stage": "before_arrival",
        "title": bi("ERICA 캠퍼스로 가는 길 확인", "确认前往 ERICA 校区的路线"),
        "steps": [
            bi("캠퍼스 지도에서 ERICA 주소와 첫 방문 장소를 확인하세요.",
               "在校园地图上核对 ERICA 校区地址和到校后要去的第一个地点。"),
            bi("도착 예정 시각에 이용할 수 있는 교통편을 확인하세요.",
               "根据预计到达时间确认可用的交通方式。"),
        ],
        "source_url": "https://www.hanyang.ac.kr/map_erica",
    },
    {
        "id": "orientation",
        "stage": "before_arrival",
        "title": bi("신입생 안내와 오리엔테이션 확인", "查看新生指南与迎新安排"),
        "steps": [
            bi("입학 안내 메일과 소속 부서의 공지에서 본인 과정의 안내를 찾으세요.",
               "从入学邮件和所属部门的公告中查找适用于自己项目的新生指南。"),
            bi("오리엔테이션이 안내되면 날짜, 장소와 참가 방법을 확인하세요.",
               "若有迎新安排，确认日期、地点和参加方式。"),
        ],
        "source_url": "https://global.hanyang.ac.kr/bbs/board.php?bo_table=s4_1",
        "place": INTERNATIONAL_OFFICE,
        "language_variant": {"source_url": "https://ericaiie.hanyang.ac.kr/archives/category/notice", "place": None},
    },
    {
        "id": "wifi",
        "stage": "first_week",
        "title": bi("캠퍼스 Wi-Fi 연결", "连接校园 Wi-Fi"),
        "steps": [
            bi("학교 안내에서 HY-WiFi 이용 자격과 본인 기기의 연결 방법을 확인하세요.",
               "查看校方说明，确认 HY-WiFi 使用资格及对应设备的连接方法。"),
            bi("교내 공용 공간에서 연결을 시도하고, 계정이 없다면 소속 부서에 이용 방법을 문의하세요.",
               "在校内公共区域尝试连接。若尚无校园账号，向所属部门咨询使用方式。"),
        ],
        "source_url": "https://it.hanyang.ac.kr/hywifi-intro",
    },
    {
        "id": "student-id",
        "stage": "first_week",
        "programs": DEGREE_PROGRAMS,
        "title": bi("모바일 학생증 확인", "确认移动学生证"),
        "steps": [
            bi("학번을 받은 뒤 ERICA 학생증 안내에서 외국인 신입생 절차를 확인하세요.",
               "取得学号后，在 ERICA 学生证指南中查看外国新生的办理流程。"),
            bi("공식 안내에 따라 헤이영 캠퍼스 앱에서 모바일 학생증을 확인하세요.",
               "按官方指南在 HeyYoung Campus 应用中查看移动学生证。"),
        ],
        "source_url": "https://site.hanyang.ac.kr/web/esc/-4",
    },
    {
        "id": "language-placement",
        "stage": "first_week",
        "programs": LANGUAGE_PROGRAM,
        "title": bi("한국어 과정 분반 확인", "确认韩语课程分班"),
        "steps": [
            bi("국제교육원의 해당 학기 공지에서 분반 시험 일정과 응시 방법을 확인하세요.",
               "在国际教育院当期公告中确认分班测试的时间和参加方式。"),
            bi("결과가 발표되면 본인 반과 수업 시간대를 확인하세요.",
               "分班结果公布后，确认自己的班级和上课时段。"),
        ],
        "source_url": "https://ericaiie.hanyang.ac.kr/archives/category/notice",
    },
    {
        "id": "courses",
        "stage": "term_start",
        "title": bi("첫 수업 시간표와 강의실 확인", "核对第一周课表与教室"),
        "steps": [
            bi("HY-in에서 신청한 과목과 시간표를 확인하세요.",
               "在 HY-in 核对已选课程和课表。"),
            bi("HY-ON LMS에서 과목 공지를 열어 첫 수업 장소와 안내를 확인하세요.",
               "在 HY-ON LMS 打开课程公告，核对第一节课的地点和安排。"),
        ],
        "source_url": "https://ectl.hanyang.ac.kr/-37",
        "language_variant": {
            "id": "language-courses",
            "steps": [
                bi("국제교육원의 학기 일정에서 개강일을 확인하세요.",
                   "在国际教育院的学期日程中核对开课日期。"),
                bi("분반 결과와 반별 공지를 보고 첫 수업 시간과 장소를 확인하세요.",
                   "结合分班结果及班级通知，确认首节课的时间和地点。"),
            ],
            "source_url": "https://ericaiie.hanyang.ac.kr/korean-language-course/kor-course/kor-schedule",
        },
    },
    {
        "id": "scholarships",
        "stage": "term_start",
        "programs": DEGREE_PROGRAMS,
        "title": bi("첫 학기 장학 안내 확인", "查看第一学期奖学金指南"),
        "steps": [
            bi("ERICA 국제처에서 외국인 학부·대학원생 장학 안내를 확인하세요.",
               "在 ERICA 国际处查看面向外国本科生和研究生的奖学金指南。"),
            bi("관심 있는 장학금의 대상, 신청 기간과 서류를 해당 학기 공지에서 확인하세요.",
               "在当期公告中核对感兴趣的奖项适用对象、申请时间和材料。"),
        ],
        "source_url": "https://global.hanyang.ac.kr/s3/s3_3_1.php",
    },
)


SEOUL_OVERRIDES = {
    "housing": {"source_url": "https://www.dormitory.hanyang.ac.kr/", "place": None},
    "campus-route": {
        "title": bi("서울캠퍼스로 가는 길 확인", "确认前往首尔校区的路线"),
        "steps": [bi("서울캠퍼스 지도에서 주소와 첫 방문 장소를 확인하세요.", "在首尔校区地图核对地址和到校后要去的第一个地点。")],
        "source_url": "https://www.hanyang.ac.kr/web/www/map_seoul",
    },
    "orientation": {"source_url": "https://oia.hanyang.ac.kr/notice", "place": None},
    "student-id": {
        "steps": [bi("학번을 받은 뒤 서울캠퍼스 학생증 안내에서 발급 절차를 확인하세요.", "取得学号后，在首尔校区学生证指南中核对申领流程。")],
        "source_url": "https://site.hanyang.ac.kr/web/studentid_s",
    },
    "language-placement": {"source_url": "https://iie.hanyang.ac.kr/front/regular/introduce/schedule"},
    "scholarships": {
        "steps": [bi("서울캠퍼스 국제처에서 장학 대상과 신청 안내를 확인하세요.", "在首尔校区国际处核对奖学金适用对象和申请指南。")],
        "source_url": "https://oia.hanyang.ac.kr/",
    },
}


def onboarding_items(school_id, program_type, *, demo=False):
    if school_id not in {SCHOOL, ERICA}:
        return []
    available = []
    for item in ITEMS:
        if "programs" in item and program_type not in item["programs"]:
            continue
        entry = {key: item[key] for key in ("id", "stage", "title", "steps", "source_url", "place") if key in item}
        if program_type == "language":
            entry.update(item.get("language_variant", {}))
        if school_id == SCHOOL and not demo:
            entry.update(SEOUL_OVERRIDES.get(item["id"], {}))
            if program_type == "language" and item["id"] in {"orientation", "courses"}:
                entry["source_url"] = "https://iie.hanyang.ac.kr/front/regular/introduce/schedule"
        available.append(entry)
    return available
