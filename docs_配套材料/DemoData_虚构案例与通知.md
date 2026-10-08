# Demo Data 虚构案例与通知原文

通知与预设人物为固定虚构演示数据，学校显示名称为Hanyang University／한양대학교／汉阳大学；不表示合作、授权或正式接入。不能当作真实学校规则。N1—N5的approved状态为初始演示审核状态，不表示真实学校工作人员已审核；N1-v2初始为draft。

固定时钟 `2026-10-07T10:00:00+09:00`，Asia/Seoul。

## 学生基础资料

```json
{
  "A": {
    "school_id": "hanyang_demo",
    "program_type": "undergraduate",
    "enrollment_status": "enrolled",
    "year": 2,
    "semester": 3,
    "department_id": "engineering",
    "international_student": true,
    "gpa_value": 3.8,
    "gpa_scale": 4.5,
    "gpa_period": "previous_semester",
    "current_dorm_resident": true,
    "language_qualification": null
  },
  "B": {
    "school_id": "hanyang_demo",
    "program_type": "master",
    "enrollment_status": "enrolled",
    "year": null,
    "semester": 1,
    "department_id": "business",
    "international_student": true,
    "gpa_value": null,
    "gpa_scale": null,
    "gpa_period": null,
    "current_dorm_resident": false,
    "language_qualification": null
  },
  "C": {
    "school_id": "hanyang_demo",
    "program_type": "undergraduate",
    "enrollment_status": "enrolled",
    "year": 2,
    "semester": 3,
    "department_id": "engineering",
    "international_student": true,
    "gpa_value": null,
    "gpa_scale": null,
    "gpa_period": null,
    "current_dorm_resident": null,
    "language_qualification": null
  }
}
```

字段用途：program_type用于学位限制；enrollment_status用于在读条件；year用于年级门槛；semester用于第一学期条件；department_id用于院系分类；international_student用于外国学生对象。gpa_value、gpa_scale、gpa_period分别用于成绩、满分制和期间，只在相关申请需要时补充；current_dorm_resident用于当前住宿舍条件；language_qualification只记录学生自述，不自动推导TOPIK要求。空值不等于false。不收集用户禁止的证件、银行、健康和地址资料。

## 预期匹配矩阵

| 学生 | N1 | N2 | N3 | N4 | N5 |
|---|---|---|---|---|---|
| A | conditions_met | conditions_not_met | conditions_met | conditions_not_met | needs_staff_review |
| B | conditions_not_met | conditions_met | conditions_not_met | conditions_met | needs_staff_review |
| C | missing_information | conditions_not_met | missing_information | conditions_not_met | needs_staff_review |

## 状态对应

| 程序状态 | 韩文 | 中文 |
|---|---|---|
| conditions_met | 조건 충족 | 条件满足 |
| conditions_not_met | 조건 불충족 | 条件不满足 |
| missing_information | 정보 부족 | 信息不足 |
| needs_staff_review | 담당자 확인 필요 | 需要工作人员确认 |

## N1 version 1 外国人本科生奖学金

以下为本原型保存的完整韩文源文，包含虚构标记、申请期、占位入口和占位联系方式。

```text
[가상 데모 공지 · 한양대학교 공식 공지가 아닙니다]
Hanyang University / 한양대학교 / 汉阳大学
공고 번호: N1, 버전: 1
제목: 외국인 학부생 장학금
공고일: 2026-10-01, 한국시간.
지원 대상: 외국인 학부 재학생, 2학년 이상. 직전 학기 GPA 4.5 만점 기준 3.5 이상.
필수 제출 자료: 직전 학기 성적증명서, 신청서.
신청 기간: 2026-10-01 09:00부터 2026-10-16 18:00까지, 한국시간.
신청 마감: 2026-10-16 18:00, 한국시간 Asia/Seoul (UTC+09:00).
신청 방법: https://demo.invalid/hanyang/n1/apply 에서 신청서를 제출하세요. 이 주소는 데모용 자리표시자이며 실제 신청은 진행되지 않습니다.
문의: 국제교류처 데모 담당자, demo-office@hanyang.invalid (실제 연락처 아님).
조건 충족 여부와 최종 접수·선발 결과는 다릅니다. 최종 확인은 학교 담당자가 수행합니다.
```

条件、材料和日期的证据必须对应此原文；中文字段只作已审核演示表达。N5没有TOPIK分数或等级，必须人工确认。

## N2 version 1 外国新入学学生活动

以下为本原型保存的完整韩文源文，包含虚构标记、申请期、占位入口和占位联系方式。

```text
[가상 데모 공지 · 한양대학교 공식 공지가 아닙니다]
Hanyang University / 한양대학교 / 汉阳大学
공고 번호: N2, 버전: 1
제목: 외국인 신입생 환영 활동
공고일: 2026-10-01, 한국시간.
지원 대상: 외국인 재학생, 입학 후 첫 번째 학기. 학위 과정 유형 제한 없음.
필수 제출 자료: 별도 제출 자료 없음.
신청 기간: 2026-10-01 09:00부터 2026-10-09 18:00까지, 한국시간.
신청 마감: 2026-10-09 18:00, 한국시간 Asia/Seoul (UTC+09:00).
신청 방법: https://demo.invalid/hanyang/n2/apply 에서 신청서를 제출하세요. 이 주소는 데모용 자리표시자이며 실제 신청은 진행되지 않습니다.
문의: 국제교류처 데모 담당자, demo-office@hanyang.invalid (실제 연락처 아님).
조건 충족 여부와 최종 접수·선발 결과는 다릅니다. 최종 확인은 학교 담당자가 수행합니다.
```

条件、材料和日期的证据必须对应此原文；中文字段只作已审核演示表达。N5没有TOPIK分数或等级，必须人工确认。

## N3 version 1 外国学生宿舍续住

以下为本原型保存的完整韩文源文，包含虚构标记、申请期、占位入口和占位联系方式。

```text
[가상 데모 공지 · 한양대학교 공식 공지가 아닙니다]
Hanyang University / 한양대학교 / 汉阳大学
공고 번호: N3, 버전: 1
제목: 외국인 학생 기숙사 연장
공고일: 2026-10-01, 한국시간.
지원 대상: 외국인 재학생이며 현재 학교 기숙사 거주자.
필수 제출 자료: 기숙사 연장 신청서.
신청 기간: 2026-10-01 09:00부터 2026-10-20 18:00까지, 한국시간.
신청 마감: 2026-10-20 18:00, 한국시간 Asia/Seoul (UTC+09:00).
신청 방법: https://demo.invalid/hanyang/n3/apply 에서 신청서를 제출하세요. 이 주소는 데모용 자리표시자이며 실제 신청은 진행되지 않습니다.
문의: 국제교류처 데모 담당자, demo-office@hanyang.invalid (실제 연락처 아님).
조건 충족 여부와 최종 접수·선발 결과는 다릅니다. 최종 확인은 학교 담당자가 수행합니다.
```

条件、材料和日期的证据必须对应此原文；中文字段只作已审核演示表达。N5没有TOPIK分数或等级，必须人工确认。

## N4 version 1 商科学生交流活动

以下为本原型保存的完整韩文源文，包含虚构标记、申请期、占位入口和占位联系方式。

```text
[가상 데모 공지 · 한양대학교 공식 공지가 아닙니다]
Hanyang University / 한양대학교 / 汉阳大学
공고 번호: N4, 버전: 1
제목: 경영학 학생 교류 활동
공고일: 2026-10-01, 한국시간.
지원 대상: 경영학 계열 재학생. 학위 과정 유형 제한 없음.
필수 제출 자료: 별도 제출 자료 없음.
신청 기간: 2026-10-01 09:00부터 2026-10-15 18:00까지, 한국시간.
신청 마감: 2026-10-15 18:00, 한국시간 Asia/Seoul (UTC+09:00).
신청 방법: https://demo.invalid/hanyang/n4/apply 에서 신청서를 제출하세요. 이 주소는 데모용 자리표시자이며 실제 신청은 진행되지 않습니다.
문의: 국제교류처 데모 담당자, demo-office@hanyang.invalid (실제 연락처 아님).
조건 충족 여부와 최종 접수·선발 결과는 다릅니다. 최종 확인은 학교 담당자가 수행합니다.
```

条件、材料和日期的证据必须对应此原文；中文字段只作已审核演示表达。N5没有TOPIK分数或等级，必须人工确认。

## N5 version 1 外国学生志愿活动

以下为本原型保存的完整韩文源文，包含虚构标记、申请期、占位入口和占位联系方式。

```text
[가상 데모 공지 · 한양대학교 공식 공지가 아닙니다]
Hanyang University / 한양대학교 / 汉阳大学
공고 번호: N5, 버전: 1
제목: 외국인 학생 자원봉사 활동
공고일: 2026-10-01, 한국시간.
지원 대상: 외국인 재학생이며 한국어로 원활하게 의사소통할 수 있는 학생. TOPIK 점수 또는 등급 기준은 명시하지 않습니다.
필수 제출 자료: 별도 제출 자료 없음.
신청 기간: 2026-10-01 09:00부터 2026-10-14 18:00까지, 한국시간.
신청 마감: 2026-10-14 18:00, 한국시간 Asia/Seoul (UTC+09:00).
신청 방법: https://demo.invalid/hanyang/n5/apply 에서 신청서를 제출하세요. 이 주소는 데모용 자리표시자이며 실제 신청은 진행되지 않습니다.
문의: 국제교류처 데모 담당자, demo-office@hanyang.invalid (실제 연락처 아님).
조건 충족 여부와 최종 접수·선발 결과는 다릅니다. 최종 확인은 학교 담당자가 수행합니다.
```

条件、材料和日期的证据必须对应此原文；中文字段只作已审核演示表达。N5没有TOPIK分数或等级，必须人工确认。

## N1 version 2 外国人本科生奖学金

以下为本原型保存的完整韩文源文，包含虚构标记、申请期、占位入口和占位联系方式。

```text
[가상 데모 공지 · 한양대학교 공식 공지가 아닙니다]
Hanyang University / 한양대학교 / 汉阳大学
공고 번호: N1, 버전: 2
제목: 외국인 학부생 장학금
공고일: 2026-10-01, 한국시간.
지원 대상: 외국인 학부 재학생, 2학년 이상. 직전 학기 GPA 4.5 만점 기준 3.5 이상.
필수 제출 자료: 직전 학기 성적증명서, 신청서, 재학증명서.
신청 기간: 2026-10-01 09:00부터 2026-10-14 18:00까지, 한국시간.
신청 마감: 2026-10-14 18:00, 한국시간 Asia/Seoul (UTC+09:00).
신청 방법: https://demo.invalid/hanyang/n1/apply 에서 신청서를 제출하세요. 이 주소는 데모용 자리표시자이며 실제 신청은 진행되지 않습니다.
문의: 국제교류처 데모 담당자, demo-office@hanyang.invalid (실제 연락처 아님).
조건 충족 여부와 최종 접수·선발 결과는 다릅니다. 최종 확인은 학교 담당자가 수행합니다.
```

条件、材料和日期的证据必须对应此原文；中文字段只作已审核演示表达。N5没有TOPIK分数或等级，必须人工确认。
