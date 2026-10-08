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
  const waitIdle=async()=>{await page.locator('.loading').waitFor({state:'hidden'});await page.locator('.notice-card').first().waitFor();};
  const login=async id=>{if(await page.locator('.account-current').count())await page.locator('.account-current').click();await Promise.all([page.waitForResponse(r=>r.url().endsWith('/api/notices')&&r.request().headers()['x-demo-account']===id&&r.status()===200),page.getByTestId('account-'+id).click()]);await waitIdle();};
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
      await page.getByRole('button',{name:'학생 정보',exact:true}).click();
      await page.locator('.optional-profile > summary').click();
      await page.getByTestId('profile-gpa_value').fill('3.8');
      await page.getByTestId('profile-gpa_scale').fill('4.5');
      await page.getByTestId('profile-gpa_period').selectOption('previous_semester');
      await page.getByRole('button',{name:'저장하고 조건 다시 확인',exact:true}).click();
      await page.getByRole('button',{name:'나의 할 일',exact:true}).click();
      await waitIdle();
      assert.match(await page.getByTestId('notice-N1').innerText(),/조건 충족/);
      await page.reload();await waitIdle();
      assert.equal((await api('C','/profile')).data.gpa_value,3.8);
    });
    await login('A');await page.getByTestId('notice-N1').click();
    await check('Generate tasks, dependencies and progress persist',async()=>{
      await page.getByTestId('generate-tasks').click();
      await page.getByTestId('task-status-A_N1_transcript').selectOption('done');
      await page.getByTestId('task-status-A_N1_application_form').selectOption('done');
      await page.getByTestId('task-status-A_N1_prepare').selectOption('in_progress');
      await page.getByTestId('task-status-A_N1_apply').selectOption('done');
      await page.reload();await waitIdle();await page.getByTestId('notice-N1').click();
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
    await login('staff');
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
      await shot('05_Review_工作人员草稿审核.png');
      await Promise.all([page.waitForResponse(r=>r.url().endsWith('/approve')&&r.status()===200),page.getByTestId('approve-version').click()]);
      await page.getByTestId('approve-version').waitFor({state:'visible'});
      await page.waitForFunction(()=>document.querySelector('[data-testid="approve-version"]')?.disabled);
      assert.equal((await api('A','/notices/N1')).data.notice.version,2);
    });
    await login('A');await page.getByTestId('notice-N1').click();
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
      await page.locator('.language').click();
      assert.equal(await page.locator('html').getAttribute('lang'),'zh-CN');
      assert.match(await page.locator('body').innerText(),/请求协助/);
      await page.setViewportSize({width:390,height:844});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
      await shot('09_MobileZH_中文手机界面.png');
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
