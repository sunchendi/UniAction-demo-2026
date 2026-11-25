/* Real browser checks against the local fictional prototype; no real applications. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const playwright = require(path.join(root, 'frontend/node_modules/playwright'));
const base = process.env.DEMO_BASE_URL || 'http://127.0.0.1:8000';
const out = process.env.QA_OUTPUT_DIR ? path.resolve(process.env.QA_OUTPUT_DIR) : null;
if(out)fs.mkdirSync(out, {recursive:true});
const checks = [];
const errors = [];
async function api(account, endpoint, method='GET', body) {
  const response = await fetch(base+'/api'+endpoint, {method, headers:{'Content-Type':'application/json','X-Demo-Account':account}, ...(body===undefined?{}:{body:JSON.stringify(body)})});
  const data = await response.json();
  return {status:response.status, data};
}
async function check(name, action) { await action(); checks.push(name); console.log('PASS '+name); }
async function ready() {
  for(let attempt=0;attempt<50;attempt++){
    try { if((await fetch(base+'/api/health')).ok)return; }catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  throw new Error('Local backend not available at '+base);
}
(async()=>{
  await ready();
  assert.equal((await api('staff','/demo/reset','POST',{})).status,200);
  const localChrome = process.env.PLAYWRIGHT_EXECUTABLE_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
  const browser = await playwright.chromium.launch({headless:true,...(fs.existsSync(localChrome)?{executablePath:localChrome}:{})});
  const context = await browser.newContext({viewport:{width:1440,height:1000},locale:'ko-KR'});
  const page = await context.newPage();
  page.on('pageerror',error=>errors.push(error.message));
  const openNotices=async()=>{await page.getByTestId('nav-notices').click();await page.locator('.notice-card').first().waitFor();};
  const login=async id=>{
    if(await page.locator('.account-current').count())await page.locator('.account-current').click();
    await page.getByTestId('account-'+id).click();
    if(id!=='staff')await page.getByTestId('today-page').waitFor();
    await openNotices();
  };
  const shot=async name=>{if(out)await page.screenshot({path:path.join(out,name),fullPage:true});};
  try {
    await page.goto(base);
    await page.getByTestId('account-A').waitFor();
    await check('Korean default / fictional demo login',async()=>{
      assert.equal(await page.locator('html').getAttribute('lang'),'ko');
      assert.match(await page.locator('body').innerText(),/데모 인물.*공지.*가상/s);
      await shot('01_Login_演示登录.png');
    });
    const labels={conditions_met:'조건 충족',conditions_not_met:'조건 불충족',missing_information:'정보 부족',needs_staff_review:'담당자 확인 필요'};
    const expected={
      A:['conditions_met','conditions_not_met','conditions_met','conditions_not_met','needs_staff_review'],
      B:['conditions_not_met','conditions_met','conditions_not_met','conditions_met','needs_staff_review'],
      C:['missing_information','conditions_not_met','missing_information','conditions_not_met','needs_staff_review'],
    };
    for(const id of ['A','B','C']){
      await login(id);
      await check(id+' five notice match results',async()=>{
        assert.equal(await page.locator('.notice-card').count(),5);
        for(let i=0;i<5;i++)assert.match(await page.getByTestId('notice-N'+(i+1)).innerText(),new RegExp(labels[expected[id][i]]));
        await shot(`02_Student${id}_学生${id}事项.png`);
      });
      if(id==='B')await check('Irrelevant GPA fields not requested for master B',async()=>{
        await page.getByRole('button',{name:'학생 정보',exact:true}).click();
        assert.equal(await page.getByTestId('profile-gpa_value').count(),0);
      });
    }
    await check('C profile edit, rematch and reload persistence',async()=>{
      await page.getByTestId('nav-today').click();
      await page.getByTestId('today-missing-N1').click();
      assert.equal(await page.getByTestId('detail-tab-evidence').getAttribute('aria-selected'),'true');
      await page.getByTestId('detail-tab-questions').click();
      const answer=page.locator('#notice-question-answer');
      assert.match(await answer.innerText(),/정보 부족.*학점/s);
      await page.locator('.back-button').click();
      await page.getByTestId('today-page').getByRole('button',{name:'정보 보완',exact:true}).click();
      await page.locator('.optional-profile > summary').click();
      await page.getByTestId('profile-gpa_value').fill('3.8');
      await page.getByTestId('profile-gpa_scale').fill('4.5');
      await page.getByTestId('profile-gpa_period').selectOption('previous_semester');
      await Promise.all([page.waitForResponse(r=>r.url().endsWith('/api/profile')&&r.request().method()==='PUT'&&r.status()===200),page.getByTestId('save-profile').click()]);
      await page.getByRole('button',{name:'나의 할 일',exact:true}).click();
      await page.getByTestId('notice-N1').locator('.conditions_met').waitFor();
      assert.match(await page.getByTestId('notice-N1').innerText(),/조건 충족/);
      await page.getByTestId('nav-today').click();
      await page.locator('.today-grid').waitFor();
      assert.equal(await page.getByTestId('today-missing-N1').count(),0);
      await page.reload();await openNotices();
      assert.equal((await api('C','/profile')).data.gpa_value,3.8);
    });
    await login('A');await page.getByTestId('notice-N1').click();
    await check('Application questions cite approved evidence before tasks exist',async()=>{
      await page.getByTestId('detail-tab-questions').click();
      const answer=page.locator('#notice-question-answer');
      assert.match(await answer.innerText(),/조건 충족/);
      assert.match(await answer.locator('blockquote').innerText(),/학부 재학생/);
      await page.getByTestId('question-materials').click();
      assert.match(await answer.innerText(),/자료 2개/);
      await page.getByTestId('question-location').click();
      const kiosk=answer.getByTestId('place-certificate-kiosk');
      assert.match(await kiosk.locator('summary').innerText(),/102.*2층/);
      assert.equal((await api('A','/notices/N1')).data.tasks.length,0);
      await shot('14_NoticeQuestions_办事问答.png');
      await answer.getByRole('button',{name:'직전 학기 성적증명서',exact:true}).click();
      assert.equal(await page.getByTestId('detail-tab-tasks').getAttribute('aria-selected'),'true');
    });
    await check('Generate tasks, dependencies and progress persist',async()=>{
      await page.getByTestId('generate-tasks').click();
      await page.getByTestId('task-status-A_N1_transcript').selectOption('done');
      await page.getByTestId('task-status-A_N1_application_form').selectOption('done');
      await page.getByTestId('task-status-A_N1_prepare').selectOption('in_progress');
      await page.getByTestId('task-status-A_N1_apply').selectOption('done');
      await page.locator('.task-item.status-done').filter({has:page.getByTestId('task-status-A_N1_apply')}).waitFor();
      await page.reload();await openNotices();await page.getByTestId('notice-N1').click();
      assert.equal(await page.getByTestId('task-status-A_N1_transcript').inputValue(),'done');
      assert.equal(await page.getByTestId('task-status-A_N1_prepare').inputValue(),'in_progress');
      assert.equal((await api('A','/notices/N1/tasks','POST',{})).data.length,4);
      await shot('03_Tasks_材料行动清单.png');
    });
    await check('Evidence can be opened',async()=>{
      await page.getByRole('tab',{name:'조건과 원문',exact:true}).click();
      for(const disclosure of await page.locator('.condition-list details').all())if(await disclosure.getAttribute('open')===null)await disclosure.locator('summary').click();
      assert.match(await page.locator('.condition-list').innerText(),/4.5 만점 기준/);
      await shot('04_Evidence_条件原文依据.png');
    });
    await check('Email file populates the notice preview and sends the edited text for review',async()=>{
      await openNotices();
      await page.getByTestId('language-select').selectOption('zh');
      await page.getByTestId('student-import-open').click();
      const subject='校园讲座报名邮件';
      const body='报名截止 2026-11-27 17:00\n申请材料\n- 在学证明';
      const file=[`Subject: =?UTF-8?B?${Buffer.from(subject).toString('base64')}?=`,
        'Content-Type: text/plain; charset=UTF-8','From: office@example.invalid','',body].join('\r\n');
      await page.getByTestId('student-import-email').setInputFiles({name:'campus.eml',mimeType:'message/rfc822',buffer:Buffer.from(file)});
      const preview=page.locator('.student-intake-preview');
      await preview.getByRole('heading',{name:subject}).waitFor();
      assert.match(await preview.innerText(),/日期候选.*2026-11-27 17:00.*材料候选.*在学证明/s);
      assert.equal(await page.getByTestId('student-import-text').inputValue(),`${subject}\n\n${body}`);
      assert.equal((await api('staff','/notices')).data.some(notice=>notice.id.startsWith('STU-')),false);
      await shot('18_EmailImport_邮件公告导入.png');
      await page.setViewportSize({width:390,height:844});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      await page.setViewportSize({width:1440,height:1000});
      const edited=`${subject}\n\n${body}\n咨询学生支持中心`;
      await page.getByTestId('student-import-text').fill(edited);
      await page.getByTestId('student-import-preview').click();
      await page.getByTestId('student-import-send').click();
      const id=await page.getByTestId('student-import-receipt').locator('code').innerText();
      const draft=(await api('staff','/notices/'+id)).data.notice;
      assert.equal(draft.publication_status,'draft');
      assert.equal(draft.source_text,edited);
      assert.equal((await api('A','/notices/'+id)).status,404);
      await page.getByTestId('language-select').selectOption('ko');
      await page.getByRole('heading',{name:'내 공지 가져오기',exact:true}).waitFor();
    });
    await check('Student imports a notice and staff can find its unpublished draft',async()=>{
      const source='교내 활동 안내\n신청 마감: 2026-11-30 17:00\n제출 서류\n- 재학증명서\n- 신청 양식';
      await openNotices();
      await page.getByTestId('student-import-open').click();
      await page.getByTestId('student-import-text').fill(source);
      await page.getByTestId('student-import-preview').click();
      const preview=page.locator('.student-intake-preview');
      await preview.waitFor();
      assert.match(await preview.innerText(),/2026-11-30 17:00/);
      assert.match(await preview.innerText(),/재학증명서/);
      await shot('13_StudentImport_学生导入公告.png');
      await page.getByTestId('student-import-text').fill(source+'\n문의: 학생지원팀');
      assert.equal(await page.getByTestId('student-import-send').count(),0);
      await page.getByTestId('student-import-preview').click();
      await page.getByTestId('student-import-send').click();
      const receipt=page.getByTestId('student-import-receipt');
      await receipt.waitFor();
      const id=await receipt.locator('code').innerText();
      assert.match(id,/^STU-/);
      assert.equal((await api('A','/notices/'+id)).status,404);
      const original=(await api('staff','/notices/'+id)).data.notice;
      const duplicate=await api('staff','/staff/manual','POST',{...original,id:'DUP-REVIEW'});
      assert.equal(duplicate.status,200);
      await login('staff');
      await page.locator('#notice-filter').selectOption('review-checks');
      const flagged=page.getByTestId('notice-'+id);
      assert.equal(await flagged.getByTestId('review-no-date').count(),1);
      assert.equal(await flagged.getByTestId('review-no-evidence').count(),1);
      assert.equal(await flagged.getByTestId('review-duplicates').count(),1);
      assert.equal(await page.getByTestId('notice-N1').count(),0);
      await page.locator('#notice-filter').selectOption('student-review');
      await page.getByTestId('notice-'+id).click();
      assert.equal(await page.locator('.source-text').textContent(),source+'\n문의: 학생지원팀');
      await page.locator('.tab-edit').click();
      await page.getByTestId('approve-version').waitFor();
      const draft=JSON.parse(await page.getByRole('textbox',{name:'구조화 초안 JSON 편집',exact:true}).inputValue());
      assert.equal(draft.publication_status,'draft');
      assert.equal(draft.source_text,source+'\n문의: 학생지원팀');
      assert.match(await page.locator('.review-related').innerText(),/DUP-REVIEW.*원문 일치/s);
      await page.locator('.review-related button').click();
      await page.getByTestId('detail-tab-evidence').waitFor();
      await page.locator('.back-button').click();
      await page.getByTestId('review-source').waitFor();
      await openNotices();
      await page.locator('#notice-filter').selectOption('all');
    });
    await check('Unrecognized fixed input fails visibly, no fake success',async()=>{
      await page.getByRole('button',{name:'공지 가져오기',exact:true}).click();
      await page.getByTestId('source-text').fill('[가상 데모] 임의의 공지 — 고정 자료와 다름');
      await page.getByTestId('extract-draft').click();
      await page.locator('[role=alert]').waitFor();
      assert.match(await page.locator('[role=alert]').innerText(),/고정 데모|固定演示|demo_source_unknown/);
      assert.equal((await api('A','/notices/N1')).data.notice.version,1);
    });
    await check('Manual draft fallback is usable and remains unpublished',async()=>{
      await page.getByRole('button',{name:'수동 초안 작성',exact:true}).click();
      await page.getByRole('textbox',{name:'구조화 초안 JSON 편집',exact:true}).waitFor();
      const body=JSON.parse(await page.getByRole('textbox',{name:'구조화 초안 JSON 편집',exact:true}).inputValue());
      await Promise.all([page.waitForResponse(r=>r.url().endsWith('/api/staff/manual')&&r.status()===200),page.getByRole('button',{name:'초안 저장',exact:true}).click()]);
      assert.equal((await api('staff',`/notices/${body.id}`)).data.notice.publication_status,'draft');
      assert.equal((await api('A',`/notices/${body.id}`)).status,404);
      await shot('10_Manual_人工补充草稿.png');
      await page.getByRole('button',{name:'공지 가져오기',exact:true}).click();
    });
    await check('N1 v2 staff draft and reviewed publishing',async()=>{
      await page.getByTestId('source-selector').selectOption('N1-v2');
      await page.getByTestId('extract-draft').click();
      await page.getByTestId('approve-version').waitFor();
      assert.equal((await api('A','/notices/N1')).data.notice.version,1);
      assert.equal((await api('A','/notices/N1/versions/2')).status,404);
      assert.equal((await api('A','/today')).data.changes.length,0);
      await shot('05_Review_工作人员草稿审核.png');
      const editor=page.getByRole('textbox',{name:'구조화 초안 JSON 편집',exact:true});
      const current=await editor.inputValue();
      const fields=JSON.parse(current);
      const deadline=page.locator('.review-fields > div').filter({hasText:'학교 공식 마감'});
      await deadline.getByRole('button',{name:'원문 근거 찾기'}).click();
      assert.equal(await page.getByTestId('review-source').locator('mark').textContent(),fields.evidence.official_deadline);
      await editor.fill(JSON.stringify({...fields,evidence:{...fields.evidence,official_deadline:'missing source excerpt'}}));
      await page.locator('.review-flags').getByTestId('review-no-evidence').waitFor();
      assert.equal(await deadline.getByRole('button').count(),0);
      await editor.fill(current);
      assert.equal(await page.locator('.review-flags').getByTestId('review-no-evidence').count(),0);
      await page.getByTestId('language-select').selectOption('zh');
      await page.getByRole('heading',{name:'提取结果',exact:true}).waitFor();
      await page.evaluate(()=>window.scrollTo(0,0));
      await shot('19_ReviewWorkbench_审核台原文对照.png');
      await page.evaluate(()=>window.scrollTo(0,450));
      const sourceTop=await page.locator('.review-source-panel').evaluate(element=>element.getBoundingClientRect().top);
      assert(sourceTop>=0&&sourceTop<=20);
      await page.setViewportSize({width:390,height:844});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      await page.setViewportSize({width:1440,height:1000});
      await page.getByTestId('language-select').selectOption('ko');
      await page.getByRole('heading',{name:'추출 결과',exact:true}).waitFor();
      await Promise.all([page.waitForResponse(r=>r.url().endsWith('/approve')&&r.status()===200),page.getByTestId('approve-version').click()]);
      await page.getByTestId('approve-version').waitFor({state:'visible'});
      await page.waitForFunction(()=>document.querySelector('[data-testid="approve-version"]')?.disabled);
      assert.equal((await api('A','/notices/N1')).data.notice.version,2);
    });
    await login('A');
    await check('Calendar uses the latest approved deadline, opens tasks and exports the month',async()=>{
      await page.getByTestId('nav-today').click();
      await page.getByTestId('calendar-open').click();
      const deadline=page.getByTestId('calendar-event-deadline:N1');
      await deadline.waitFor();
      assert.match(await page.getByTestId('calendar-month').innerText(),/2026.*10/);
      await shot('15_Calendar_我的日历.png');
      await page.getByTestId('calendar-day-2026-10-14').click();
      assert.match(await deadline.innerText(),/18:00/);
      await page.getByTestId('calendar-day-2026-10-16').click();
      assert.equal(await deadline.count(),0);
      await page.getByTestId('calendar-day-2026-10-11').click();
      await page.getByTestId('calendar-event-preparation:N1:enrollment_certificate').click();
      await page.waitForFunction(()=>document.activeElement?.id==='task-A_N1_enrollment_certificate');
      await page.locator('.back-button').click();
      assert.equal(await page.getByTestId('calendar-day-2026-10-11').getAttribute('aria-pressed'),'true');

      const downloadEvent=page.waitForEvent('download');
      await page.getByTestId('calendar-export').click();
      const download=await downloadEvent;
      assert.equal(download.suggestedFilename(),'UniAction-2026-10.ics');
      const ics=fs.readFileSync(await download.path(),'utf8');
      assert(ics.split('\r\n').every(line=>Buffer.byteLength(line,'utf8')<=75));
      const unfolded=ics.replace(/\r\n /g,'');
      const deadlineEvent=unfolded.split('BEGIN:VEVENT').find(event=>event.includes('UID:deadline%3AN1@uniaction.local'));
      assert.match(deadlineEvent,/SEQUENCE:2\r\n/);
      assert.match(deadlineEvent,/DTSTART:20261014T090000Z\r\n/);
      assert.match(unfolded,/DTSTART;VALUE=DATE:20261011\r\n/);

      await page.getByTestId('calendar-next').click();
      await page.getByTestId('calendar-day-2026-11-01').waitFor();
      assert(await page.getByTestId('calendar-export').isDisabled());
      await page.getByTestId('calendar-prev').click();
      await deadline.waitFor();
    });
    await check('Today shows approved changes, near deadlines and actionable tasks',async()=>{
      await page.getByTestId('nav-today').click();
      const notice=page.getByTestId('today-upcoming-N1');
      await notice.waitFor();
      assert.equal(await notice.locator('..').locator('time').first().getAttribute('datetime'),'2026-10-14T18:00:00+09:00');
      assert.equal(await page.getByTestId('today-task-A_N1_transcript').count(),0);
      assert.equal(await page.getByTestId('today-task-A_N1_prepare').locator('..').locator('time').getAttribute('datetime'),'2026-10-11');
      assert.equal(await page.getByTestId('campus-shortcut-dining').innerText(),'오늘의 학식');
      assert.equal(await page.getByTestId('campus-shortcut-dining').getAttribute('href'),'https://fnb.hanyang.ac.kr/front/fnbmMdMenu');
      assert.equal(await page.getByTestId('campus-shortcut-shuttle').count(),0);
      assert.equal(await page.getByTestId('campus-shortcut-map').getAttribute('href'),'https://www.hanyang.ac.kr/web/www/map_seoul');
      await shot('11_Today_今日行动.png');
      await page.getByTestId('today-task-A_N1_enrollment_certificate').click();
      const certificate=page.getByTestId('task-A_N1_enrollment_certificate');
      await certificate.waitFor();
      await page.waitForFunction(id=>document.activeElement?.id===id,await certificate.getAttribute('id'));
      const kiosk=certificate.getByTestId('place-certificate-kiosk');
      assert.match(await kiosk.locator('summary').innerText(),/102.*2층/);
      await kiosk.locator('summary').click();
      assert.match(await kiosk.innerText(),/24시간/);
      assert.equal(await kiosk.getByRole('link',{name:'캠퍼스 지도 열기'}).getAttribute('href'),'https://www.hanyang.ac.kr/map_erica');
      assert.equal(await kiosk.getByRole('link',{name:'증명 발급 안내'}).getAttribute('href'),'https://ehaksa.hanyang.ac.kr/ko/certificate');
      assert.equal(await page.getByTestId('task-A_N1_application_form').locator('.place-card').count(),0);
      await shot('12_PlaceCard_办事地点卡.png');
      await page.locator('.back-button').click();
      await page.getByTestId('today-change-N1').click();
      assert.equal(await page.getByTestId('detail-tab-versions').getAttribute('aria-selected'),'true');
      await openNotices();
    });
    await page.getByTestId('notice-N1').click();
    await check('Updated material answer focuses the remaining task',async()=>{
      await page.getByTestId('detail-tab-questions').click();
      await page.getByTestId('question-materials').click();
      const answer=page.locator('#notice-question-answer');
      assert.match(await answer.innerText(),/자료 1개/);
      assert.match(await answer.locator('blockquote').innerText(),/재학증명서/);
      assert.equal(await answer.getByRole('button',{name:/직전 학기 성적증명서/}).count(),0);
      await answer.getByRole('button',{name:/재학증명서/}).click();
      await page.waitForFunction(()=>document.activeElement?.id==='task-A_N1_enrollment_certificate');
    });
    await check('Version update adds material, preserves unrelated work and reconfirms affected work',async()=>{
      await page.getByTestId('task-status-A_N1_enrollment_certificate').waitFor();
      assert.equal(await page.getByTestId('task-status-A_N1_transcript').inputValue(),'done');
      assert.equal(await page.getByTestId('task-status-A_N1_application_form').inputValue(),'done');
      assert.equal(await page.getByTestId('task-status-A_N1_prepare').inputValue(),'in_progress');
      assert.equal(await page.getByTestId('task-status-A_N1_apply').inputValue(),'requires_reconfirmation');
      assert.match(await page.locator('.deadline-box').innerText(),/14/);
      await shot('06_Update_版本更新进度保留.png');
      await page.getByRole('tab',{name:'변경 이력',exact:true}).click();
      assert.equal(await page.locator('.version-card').count(),2);
      await page.locator('.version-card').filter({has:page.getByText('v1',{exact:true})}).getByRole('button',{name:'이 버전 원문 보기',exact:true}).click();
      await page.locator('.version-preview').waitFor();
      assert.match(await page.locator('.version-preview').innerText(),/2026-10-16/);
    });
    await check('Student self-reported submit stays unofficial',async()=>{
      await page.getByTestId('detail-tab-tasks').click();
      await Promise.all([page.waitForResponse(r=>r.url().endsWith('/submit')&&r.status()===200),page.getByRole('button',{name:'내가 제출했다고 기록',exact:true}).click()]);
      const result=(await api('A','/notices/N1')).data.submission_status;
      assert.equal(result.status,'self_reported_submitted');assert.equal(result.school_received,false);assert.equal(result.school_approved,false);
    });
    await check('Application follow-up saves a private status, date and note',async()=>{
      await page.getByTestId('submission-followup-open').click();
      const card=page.getByTestId('app-followup-N1');
      assert.equal(await card.getByTestId('followup-status').innerText(),'결과 기다리는 중');
      await card.getByTestId('followup-edit').click();
      await card.getByTestId('followup-edit-status').selectOption('needs_documents');
      await card.getByTestId('followup-edit-date').fill('2026-10-07');
      await card.getByTestId('followup-edit-note').fill('确认在学证明的补交方式');
      await card.getByTestId('followup-save').click();
      await card.getByTestId('followup-due').waitFor();
      assert.equal(await card.getByTestId('followup-status').innerText(),'보완 서류 필요');
      await page.getByTestId('language-select').selectOption('zh');
      await page.getByRole('heading',{name:'申请后续跟踪',exact:true}).waitFor();
      await shot('16_ApplicationFollowup_申请后续跟踪.png');
      await page.setViewportSize({width:390,height:844});
      await card.getByTestId('followup-edit').click();
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      await shot('17_ApplicationFollowupMobile_手机申请后续跟踪.png');
      await card.getByRole('button',{name:'取消',exact:true}).click();
      await page.setViewportSize({width:1440,height:1000});
      await page.getByTestId('language-select').selectOption('ko');
      await page.getByRole('heading',{name:'신청 후속 관리',exact:true}).waitFor();
      await page.reload();
      await page.getByTestId('applications-open').click();
      assert.equal(await card.getByTestId('followup-status').innerText(),'보완 서류 필요');
      assert.match(await card.innerText(),/确认在学证明的补交方式/);
      assert.equal((await api('B','/applications')).data.items.length,0);
      await card.getByTestId('followup-notice').click();
      await page.getByTestId('submission-followup-open').waitFor();
      await page.locator('.back-button').click();
      await card.waitFor();
      await openNotices();
      await page.getByTestId('notice-N1').click();
    });
    await page.locator('.back-button').click();await page.getByTestId('notice-N5').click();
    await check('Ambiguous language condition, explicit sharing and staff case',async()=>{
      await page.getByTestId('generate-tasks').click();
      await page.getByRole('tab',{name:'도움 요청',exact:true}).click();
      await page.getByTestId('help-message').fill('한국어 의사소통 조건은 어떤 절차로 확인하나요? (가상 데모 질문)');
      await page.getByTestId('help-scope').selectOption('case_only');
      await Promise.all([page.waitForResponse(r=>r.url().endsWith('/api/cases')&&r.request().method()==='POST'&&r.status()===200),page.getByTestId('send-help').click()]);
      assert.equal((await api('staff','/staff/students/A/notices/N5/tasks')).status,403);
      await shot('07_Consent_学生授权协助.png');
      await login('staff');await page.getByRole('button',{name:/도움 요청함/}).click();
      await page.locator('.case-card').first().waitFor();
      assert.match(await page.locator('main').innerText(),/가상 데모 질문/);
      await shot('08_StaffCases_工作人员案例.png');
    });
    await check('Staff response does not confirm an application result',async()=>{
      const card=page.locator('.case-card').first();
      await card.getByRole('textbox').fill('원문의 의사소통 기준은 별도 담당자 확인이 필요합니다. (데모 답변)');
      await card.getByRole('combobox').selectOption('resolved');
      await Promise.all([page.waitForResponse(r=>r.url().includes('/api/cases/')&&r.request().method()==='PATCH'&&r.status()===200),card.getByRole('button',{name:'답변과 상태 저장',exact:true}).click()]);
      const cases=(await api('A','/cases')).data;
      assert.equal(cases[0].status,'resolved');assert.equal(cases[0].school_application_result,'not_confirmed');
    });
    await check('Task progress sharing requires additional explicit consent',async()=>{
      assert.equal(await page.getByRole('button',{name:'허용된 과제 보기',exact:true}).count(),0);
      await login('A');await page.getByTestId('notice-N5').click();await page.getByRole('tab',{name:'도움 요청',exact:true}).click();
      await Promise.all([page.waitForResponse(r=>r.url().endsWith('/sharing')&&r.request().method()==='PUT'&&r.status()===200),page.getByLabel('후속 접근 범위 변경',{exact:true}).selectOption('tasks_and_cases')]);
      await login('staff');await page.getByRole('button',{name:/도움 요청함/}).click();
      await page.getByRole('button',{name:'허용된 과제 보기',exact:true}).click();await page.locator('.shared-tasks').waitFor();
      assert.match(await page.locator('.shared-tasks').innerText(),/이 공지의 관련 진행만/);
      assert.doesNotMatch(await page.locator('.shared-tasks').innerText(),/3\.8|gpa_value/);
    });
    await check('Revocation and cross-school denial',async()=>{
      await login('A');await page.getByTestId('notice-N5').click();await page.getByRole('tab',{name:'도움 요청',exact:true}).click();
      await Promise.all([page.waitForResponse(r=>r.url().endsWith('/sharing')&&r.request().method()==='PUT'&&r.status()===200),page.getByTestId('revoke-sharing').click()]);
      assert.equal((await api('staff','/cases')).data.length,0);
      assert.equal((await api('other_staff','/notices/N1')).status,404);
    });
    await check('Chinese language and mobile layout',async()=>{
      await page.getByTestId('language-select').selectOption('zh');
      assert.equal(await page.locator('html').getAttribute('lang'),'zh-CN');
      assert.match(await page.locator('body').innerText(),/请求协助/);
      await page.setViewportSize({width:390,height:844});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
      await shot('09_MobileZH_中文手机界面.png');
    });
    await check('Six added languages across login, student and staff pages',async()=>{
      const language=page.getByTestId('language-select');
      const locales={en:'en',fr:'fr',ru:'ru',es:'es',de:'de',pt:'pt-BR'};
      const switchTo=async code=>{
        await language.selectOption(code);
        await page.waitForFunction(locale=>document.documentElement.lang===locale,locales[code]);
        assert.equal(new URL(page.url()).searchParams.get('lang'),code);
      };
      const noOverflow=async stage=>{
        const overflow=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth?null:{width:innerWidth,scrollWidth:document.documentElement.scrollWidth,elements:[...document.querySelectorAll('body *')].filter(element=>element.getBoundingClientRect().right>innerWidth+1).slice(0,8).map(element=>`${element.tagName}.${element.getAttribute('class')??''}`)});
        assert.equal(overflow,null,`Mobile overflow: ${stage} ${JSON.stringify(overflow)}`);
      };
      const translated=async locator=>{
        const text=(await locator.innerText()).trim();
        assert(text&&!/[가-힣\u4e00-\u9fff]/u.test(text),`Untranslated interface text: ${text}`);
        return text;
      };
      assert.deepEqual(await language.locator('option').evaluateAll(options=>options.map(option=>option.value)),['ko','zh','en','fr','ru','es','de','pt']);
      await page.getByTestId('account-switch').click();
      await page.getByTestId('auth-register-tab').click();
      const authHeadings=new Set();
      for(const code of Object.keys(locales)){
        await switchTo(code);
        authHeadings.add(await translated(page.locator('.auth-card h2')));
        await translated(page.getByTestId('auth-submit'));
        await noOverflow(`${code} registration`);
      }
      assert.equal(authHeadings.size,6);
      await page.getByTestId('auth-demo-tab').click();
      await login('A');
      await page.getByTestId('notice-N1').click();
      await page.getByTestId('detail-tab-evidence').click();
      const original=(await api('A','/notices/N1')).data.notice.source_text;
      const noticeTitles=new Set();
      for(const code of Object.keys(locales)){
        await switchTo(code);
        await page.getByTestId('nav-onboarding').click();
        const housing=page.getByTestId('onboarding-item-housing');
        await housing.waitFor();
        await housing.locator('.onboarding-details > summary').click();
        await translated(page.getByTestId('onboarding-page').getByRole('heading',{level:1}));
        await translated(housing.locator('ol'));
        const dormOffice=housing.getByTestId('place-dormitory-office');
        await dormOffice.locator('summary').click();
        await translated(dormOffice);
        await noOverflow(`${code} onboarding`);
        await page.getByTestId('nav-today').click();
        await page.locator('.today-grid').waitFor();
        await translated(page.getByTestId('today-page').getByRole('heading',{level:1}));
        await noOverflow(`${code} today`);
        await page.getByTestId('today-change-N1').click();
        await page.getByTestId('detail-tab-questions').click();
        await translated(page.getByTestId('question-materials'));
        await page.getByTestId('question-materials').click();
        await translated(page.locator('.question-result'));
        await noOverflow(code+' notice questions');
        await page.getByTestId('detail-tab-evidence').click();
        noticeTitles.add(await translated(page.locator('.notice-heading h1')));
        await translated(page.getByTestId('detail-tab-evidence'));
        assert.equal(await page.locator('.source-text').textContent(),original);
        assert.match(await page.locator('.deadline-box strong').innerText(),/KST · UTC\+09:00/);
        await noOverflow(`${code} notice evidence`);
      }
      assert.equal(noticeTitles.size,6);
      await login('staff');
      await page.getByTestId('nav-import').click();
      const staffHeadings=new Set();
      for(const code of Object.keys(locales)){
        await switchTo(code);
        staffHeadings.add(await translated(page.locator('.page-title h1')));
        await translated(page.getByTestId('extract-draft'));
        await noOverflow(`${code} staff import`);
      }
      assert.equal(staffHeadings.size,6);
      await page.goto(base+'/?lang=ru&theme=whitegold');
      await page.waitForFunction(()=>document.documentElement.lang==='ru');
      await switchTo('fr');
      assert.equal(new URL(page.url()).searchParams.get('theme'),'whitegold');
      await page.goto(base);
      await page.waitForFunction(()=>document.documentElement.lang==='fr');
      await page.goto(base+'/?lang=ar');
      await language.waitFor();
      assert.equal(await language.inputValue(),'fr');
      await page.getByTestId('account-switch').click();
      await page.getByTestId('auth-login-tab').click();
      await page.getByTestId('auth-username').fill('missing_locale_user');
      await page.getByTestId('auth-password').fill('wrong-local-password-2026');
      await page.getByTestId('auth-submit').click();
      const authError=page.getByRole('alert');await authError.waitFor();
      assert.match(await translated(authError),/mot de passe/i);
    });
    assert.deepEqual(errors,[],'Browser runtime errors');
    console.log('PASS no browser runtime errors');checks.push('No browser runtime errors');
    if(out)fs.writeFileSync(path.join(out,'BrowserResults_浏览器结果.json'),JSON.stringify({executed_at:new Date().toISOString(),base,browser:'headless Chromium / installed Chrome or Playwright Chromium',checks,errors,screenshots:'Actual running application screenshots, fictional data'},null,2));
  } catch(error) {
    await shot('Failure_验证失败现场.png').catch(()=>{});
    if(out)fs.writeFileSync(path.join(out,'BrowserResults_浏览器结果.json'),JSON.stringify({executed_at:new Date().toISOString(),base,checks,errors,failure:error.message},null,2));
    throw error;
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
