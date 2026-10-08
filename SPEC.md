# SPEC 产品规格

暂定名 UniAction 校园行动（未宣称商标注册）。中文主题：把校园通知转成个人行动清单的 AI 助手。韩文主题：대학 공지를 개인별 실행계획으로 바꾸는 AI 서비스。

## 使用者和边界

主要使用者为入学初期、不了解学校流程的外国学生。首批采购对象为国际交流处及独立办理申请的语言教育院。首期仅奖学金、宿舍续住、校内活动。回答相关性、缺失资料、材料、下一步与联系处。学校显示名称为 Hanyang University／한양대학교／汉阳大学；所有通知与预设人物虚构，不表示学校合作或授权；个人账号扩展可在本机填写自己的必要资料。预设演示身份与本地个人账号均非学校 SSO。仅本地运行，不自动申请、发邮件或联系学校。

## 数据与职责

学生基础：school_id、program_type（language/undergraduate/master/doctor）、enrollment_status（enrolled/leave/graduated）、year、semester、department_id、international_student。按需资料：gpa_value、gpa_scale、gpa_period、current_dorm_resident、language_qualification。null 保留未知；年级与学期分离；GPA 满分制与期间分离且不换算。不得收集护照、外国人登记证、银行、健康或完整住址。

通知保存 id、school_id、双语 title、category、source_url、source_text、source_hash、version、publication_status、reviewed_by、reviewed_at、eligibility_rules、required_documents、official_deadline、application_window、application_url、office_contact、task_templates、evidence、ambiguities、change_summary。draft → under_review → approved；archived 可保留。每版本原文不可丢失。重要条件、材料与日期必须有真实原文片段；时间未给出时保留日期，不补 18:00/23:59。办理入口标注 official/demo。

AI 只起草结构化内容与表达；受控规则计算；工作人员审核批准。固定演示提取器只匹配完整固定文本。真实模式用环境变量密钥及模型、结构校验、字段/操作符白名单、原文证据校验，不执行生成程序、不 eval。API 异常与无效草稿不会自动发布，可人工补充。未审核版本不能替换正式个人结论。

## 规则与状态

规则操作符仅 all、any、eq、in、gte、lte、is_true、is_false、needs_staff_review。字段白名单仅上述学生字段。AND 有确定 false → false；无 false 有 unknown → unknown。OR 有 true → true；无 true 有 unknown → unknown。明显不符合优先于无关缺失信息；例如 B 不是本科，N1 返回条件不满足而非缺 GPA。

| 状态 | 韩文 | 中文 |
|---|---|---|
| conditions_met | 조건 충족 | 条件满足 |
| conditions_not_met | 조건 불충족 | 条件不满足 |
| missing_information | 정보 부족 | 信息不足 |
| needs_staff_review | 담당자 확인 필요 | 需要工作人员确认 |

结果说明逐条条件、true/false/unknown、缺失字段、原文、人工确认。GPA 口径不一致需确认；N5 “能够顺畅使用韩语沟通”不能生成 TOPIK 门槛。条件满足声明：按当前提供的信息满足通知明确条件，最终受理、资格核验及选拔结果由学校确认。申请尚未开放、开放、过期、时刻待确认与匹配状态分开。

## 行动与协助

任务字段 id、student_id、notice_id、notice_version、title、description、task_type、required_or_suggested、source_evidence、official_due_at、suggested_start_at、depends_on、status。任务状态 todo/in_progress/done/needs_help/requires_reconfirmation。区分正式必需与可调整准备建议；依赖无循环；生成幂等，进度持久化。自报提交仅 self_reported_submitted，非学校收件或批准。

sharing_scope 默认 none；case_only 仅明确发送案例及必要内容；tasks_and_cases 为相关事项任务+案例。工作人员无学生完整资料/GPA接口。服务端验证身份、school_id 和授权；撤销后后续访问立即拒绝，前端同样反映。处理案例不等于申请成功。

## 版本更新

N1 v2 新截止 2026-10-14 18:00 +09:00，新增在学证明，其他条件不变。新版重新审核；批准后重新匹配并比较条件、必需材料、截止、入口与任务说明。新增材料新任务；保留未受影响的完成进度；受影响且已完成任务 requires_reconfirmation。禁止统一重置。旧、新原文都可查看，展示变化摘要与依据。

## 固定案例与验收

时钟可注入，默认 2026-10-07T10:00:00+09:00（Asia/Seoul），页面注明固定演示时间。五则完整虚构原文由后端 fixtures 提供并可导出。

| 学生 | N1 奖学金 | N2 新生 | N3 宿舍 | N4 商科 | N5 志愿 |
|---|---|---|---|---|---|
| A | conditions_met | conditions_not_met | conditions_met | conditions_not_met | needs_staff_review |
| B | conditions_not_met | conditions_met | conditions_not_met | conditions_met | needs_staff_review |
| C | missing_information | conditions_not_met | missing_information | conditions_not_met | needs_staff_review |

A 本科在读，year=2、semester=3、engineering、外国学生、3.8/4.5/previous_semester、宿舍 true。B master、在读、semester=1、business、外国学生、GPA null、宿舍 false。C 本科在读，year=2、semester=3、engineering、外国学生、GPA null、宿舍 null。


## 个人学生账号


注册字段为username、password、display_name、program_type、enrollment_status、department_id。用户名3—32位英文、数字或_ . -，服务端归一为小写；密码15—128字符；显示名称去首尾空白后1—50字符；注册院系仅engineering、business、humanities。界面要求学生明确选择后三个分类，不用预设A的资料作为注册默认值。服务端将school_id固定为hanyang_demo、role固定为student；客户端不能通过请求获得工作人员或跨学校身份。其余年级、学期、国际学生、GPA数值/满分/期间、当前宿舍和语言资格初始为null，不猜测或自动转为false。后续资料编辑保留原有用途说明、按需提示和重新匹配。

注册和登录返回account并设置HttpOnly会话Cookie；GET auth/me在有效会话下返回account、无Cookie时返回null，无效或过期Cookie返回401要求重新登录。退出登录撤销会话；无会话或会话过期时退出同样返回200并清除Cookie。密码不明文保存；服务端保存会话令牌的哈希。会话有效8小时，到期使用真实UTC时钟，业务期限继续使用可注入的固定演示时钟。有效个人会话优先于X-Demo-Account，演示身份头不得覆盖个人会话读取其他学生资料；无效Cookie不回退到演示身份。预设比赛账号仍保留独立入口，身份头仅允许本地回环客户端。

个人资料保存在运行服务的本机数据库，不上传GitHub。工作人员仍只可按school_id、角色、sharing_scope访问授权案例/相关任务，不新增读取完整个人资料或GPA的权限。不收集既定禁止的敏感字段，不接入学校SSO。

重置保护：存在任何注册账号时，POST demo/reset必须以409拒绝，账号、资料、任务和案例不得被清除。比赛需要重置时使用新的DATABASE_PATH启动独立演示数据库，不通过清除个人数据解锁重置。
