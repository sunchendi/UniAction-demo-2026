# UniAction 校园行动

把校园通知转成个人行动清单的本地原型。React + TypeScript + Vite，FastAPI + Pydantic + SQLite。界面采用白金配色、黑色字体，默认韩文，支持中文。

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

登录页可创建个人学生账号，或选择 A／B／C／staff 预设账号。个人账号需明确选择学位、在读状态和院系；其他资料初始未知，仅相关申请需要时补充。用户名 3–32 位英文、数字或 `_.-`，密码 15–128 字符。会话有效 8 小时；这是本地认证，尚未接入学校 SSO。

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

尚未自动读取邮箱或学校公告。条件满足不代表学校受理或获奖；“我已提交”仅为学生自报。协助只共享学生授权的案例或相关任务，不向工作人员开放 GPA 等完整资料。真实学校接入、生产隐私与安全、市场需求及付费价格仍需验证。

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
| frontend/ | 韩中界面与白金主题 |
| tests/ | 比赛流程和个人账号浏览器检查 |
| SPEC.md | 字段、状态、规则与验收要求 |
| API_CONTRACT.md | 开发接口契约 |
| ASSUMPTIONS.md | 尚未验证的需求、价格、成本假设 |
| SOURCE_REGISTER.md | 市场与竞品的可核对事实来源 |
| docs_配套材料/ | 中韩事业计划书、答辩、脚本、虚构案例、财务模型及未来计划 |

[中文事业计划书](docs_配套材料/BusinessPlan_ZH_中文事业计划书.md) · [韩文事业计划书](docs_配套材料/BusinessPlan_KO_韩文事业计划书.md) · [教授用韩文介绍](docs_配套材料/ProfessorIntro_KO_教授用韩文介绍.md) · [竞赛答辩问答](docs_配套材料/DefenseQA_竞赛答辩问答.md)
