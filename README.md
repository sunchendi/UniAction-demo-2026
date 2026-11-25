# UniAction 校园行动

把校园通知转成个人行动清单的本地原型。React + TypeScript + Vite，FastAPI + Pydantic + SQLite。界面采用白金配色、黑色字体，默认韩语，另有简体中文、英语、法语、俄语、西班牙语、德语和葡萄牙语。

支持个人注册与资料编辑、条件匹配及原文依据、材料任务与进度、授权协助、工作人员草稿审核、通知版本更新。学校展示名为 Hanyang University／한양대학교／汉阳大学；预设人物、通知及申请入口均为虚构演示资料，不表示学校合作或正式接入。项目名称暂定，未宣称商标注册。

## 安装与启动

需要 Python 3.12+、Node.js 24 和 pnpm 10。Windows 在项目目录执行：

```powershell
.\Setup_安装依赖.ps1
.\Start_Demo_启动演示.ps1
```

依赖和前端构建已存在时，只需第二条命令。打开 [网页](http://127.0.0.1:8000/) 或 [API 文档](http://127.0.0.1:8000/docs)。终端须保持运行，按 Ctrl+C 停止；127.0.0.1 只能从运行服务的本机访问。

手动安装与构建：

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
cd frontend
pnpm install --frozen-lockfile
pnpm build
cd ..
.\Start_Demo_启动演示.ps1
```

Linux/macOS 使用 `python3` 和 `backend/.venv/bin/python`，以 `python -m uvicorn backend.main_主程序:app --host 127.0.0.1 --port 8000` 启动。开发时在 frontend 执行 `pnpm dev`，同时保持后端运行。

## 使用与演示

通过页面顶部的语言菜单切换，浏览器会记住选择。也可以用 `?lang=en`、`?lang=fr`、`?lang=ru`、`?lang=es`、`?lang=de` 或 `?lang=pt` 直接打开对应界面。预设演示内容有译文；公告原文、证据引用和用户填写的内容保持原样。新导入的内容没有对应译文时显示原文。

登录页可创建个人学生账号，或选择预设演示身份。注册时须选择学校（汉阳大学或汉阳大学 ERICA）、该校区的院系和专业、学位类型及在读状态。学生资料里可修改院系和专业，校区随账号保存。注册用户名可使用 3–32 位英文、数字或 `_.-`，密码须为 10–32 个字符。会话有效 8 小时；这是本地认证，尚未接入学校 SSO。

院系目录以校方本科院系和主修方向为基础，另含两校区国际教育院的韩语正规课程。ERICA 学生送审的通知由 ERICA 工作人员演示账号核对。旧账号保留原校区，并可在「学生资料」补选更具体的院系和专业。 [首尔校区院系目录](https://www.hanyang.ac.kr/web/www/s_college_department-info) · [ERICA 校区院系目录](https://www.hanyang.ac.kr/e_college_department-info)

学生登录后进入「今日行动」，可查看未来 7 天的相关截止事项、近期需要准备的任务、已审核公告变更和待补资料。点击提醒可打开原有的任务、版本或条件依据，正式截止与建议准备日期分别显示。通过「我的事项」可以查看完整通知列表。

「今日行动 → 我的日历」按学校时间（KST）显示最新已审核公告的正式截止日和未完成任务的建议准备日。可按月浏览、点选日期查看安排、打开对应通知或任务，并下载当月 `.ics` 文件导入个人日历。文件记录导出时的当月安排，只有日期的事项显示为全天事件。

在通知详情记录「我已提交」后，可从「今日行动 → 申请后续跟踪」查看相应申请，更新个人跟踪状态、下次查看日期和私人备注。到达所选日期时，跟踪页会标记该事项。受理、审批与结果仍由学校的官方流程确认。

「入学清单」按到校前、到校第一周、学期初整理建议。清单根据学生资料中的课程类型显示适用事项。每项可展开查看步骤与 ERICA 校方说明，勾选与取消勾选都保存在当前账号的本地进度中。

部分材料任务和入学事项附有「办事地点卡」。卡片显示楼栋和楼层，展开可查看开放时间、到访提示、校园地图和校方出处。首版覆盖证明发放、国际处咨询和宿舍咨询，具体提交办法按当期通知执行。

学生可从「我的事项」进入「导入公告」，粘贴原文或输入受支持的汉阳大学公开公告链接。预览显示从原文找到的日期和材料片段。送审后，工作人员可在「通知管理」筛选「学生送审」，打开原文并沿用现有审核流程。同一来源和原文的重复送审会复用草稿。图片、附件和需要登录的公告可通过粘贴文字导入。

「导入公告」也支持选择 2 MB 以内的 `.eml` 邮件文件。系统提取邮件主题和正文，预览日期与材料候选。学生可编辑文本后送审，工作人员收到的是确认后的公告文字。

工作人员可在「通知管理」用「待核对」筛选缺截止日期、依据待核对或疑似重复的草稿。审核页并排展示原文和当前编辑的提取结果，点击依据可定位原文。疑似重复按已保存草稿与同校其他公告的原文、来源链接和标题核对，供人工判断。

通知详情的「办事问答」提供资格、待准备材料与办理地点三个问题。答案使用当前已批准的通知及账号的任务进度，并可查看原文依据、打开相关任务或请求协助。「今日行动」的「今日食堂」链接到所选校区的菜单，ERICA 另有「校车时刻表」。[首尔今日菜单](https://fnb.hanyang.ac.kr/front/fnbmMdMenu) · [ERICA 今日菜单](https://life.hanyang.ac.kr/theme/pages/home.php) · [ERICA 校车时刻表](https://hybus.app/)

演示使用固定时间 `2026-10-07 10:00 Asia/Seoul`。A 满足 N1 奖学金明确条件，B 因非本科不符合，C 因缺少 GPA 信息不足；N5 的模糊语言条件需工作人员确认。N1 第二版提前截止并新增在学证明，保留无关完成进度。完整操作见 [三分钟脚本](docs_配套材料/DemoScript_三分钟演示脚本.md) 和 [演示前检查表](docs_配套材料/DemoChecklist_演示前检查表.md)。

工作人员页面提供重置，或执行：

```powershell
python .\reset_demo_重置演示.py
backend/.venv/Scripts/python.exe .\Verify_Baseline_检查演示基线.py
```

存在个人注册账号时，重置返回 409 并保留资料。比赛可先停止服务，使用独立数据库重新启动：

```powershell
$env:DATABASE_PATH = Join-Path $PWD 'backend/data/competition-demo.sqlite3'
.\Start_Demo_启动演示.ps1
```

默认个人数据库为 `backend/data/demo.sqlite3`，不上传 GitHub。旧学校标识迁移前会自动保存本地数据库备份。不要通过删除个人数据库重置比赛。

## 提取模式

默认 **固定演示数据**，只识别五则完整原文及 N1 第二版；其他文本可人工补充草稿。真实提取接口已实现，但没有真实 API 调用验证。需要时将 `.env.example` 复制为 `.env`，设置 `OPENAI_API_KEY` 和 `OPENAI_MODEL`，由工作人员选择真实模式。所有重要字段仍需校验、审核后批准。

公告读取由学生在导入页发起。条件满足不代表学校受理或获奖；“我已提交”仅为学生自报。协助只共享学生授权的案例或相关任务，不向工作人员开放 GPA 等完整资料。真实学校接入、生产隐私与安全、市场需求及付费价格仍需验证。

## 开发检查

在项目根目录运行后端及隔离浏览器检查：

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider
backend/.venv/Scripts/python.exe Run_AccountChecks_运行账号检查.py --demo
backend/.venv/Scripts/python.exe Run_AccountChecks_运行账号检查.py
```

在 frontend 运行 `pnpm typecheck` 和 `pnpm build`。首次浏览器检查如缺少 Chromium，执行 `pnpm exec playwright install chromium`。浏览器检查使用临时数据库，不重置个人数据；默认只输出终端结果。需要截图时设置 `QA_OUTPUT_DIR` 指向项目外目录。

## 文件入口

| 路径 | 用途 |
|---|---|
| backend/ | 接口、认证、受控规则、存储、提取器与业务测试 |
| frontend/ | 八种界面语言与白金主题 |
| tests/ | 比赛流程和个人账号浏览器检查 |
| SPEC.md | 字段、状态、规则与验收要求 |
| API_CONTRACT.md | 开发接口契约 |
| ASSUMPTIONS.md | 尚未验证的需求、价格、成本假设 |
| SOURCE_REGISTER.md | 市场与竞品的可核对事实来源 |
| docs_配套材料/ | 中韩事业计划书、答辩、脚本、虚构案例、财务模型及未来计划 |

[中文事业计划书](docs_配套材料/BusinessPlan_ZH_中文事业计划书.md) · [韩文事业计划书](docs_配套材料/BusinessPlan_KO_韩文事业计划书.md) · [教授用韩文介绍](docs_配套材料/ProfessorIntro_KO_教授用韩文介绍.md) · [竞赛答辩问答](docs_配套材料/DefenseQA_竞赛答辩问答.md)
