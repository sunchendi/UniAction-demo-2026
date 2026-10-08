/* Browser checks of local account registration and user-owned persistent data. */
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const {chromium}=require(path.join(root,'frontend/node_modules/playwright'));
const base=process.env.DEMO_BASE_URL;
if(!base)throw new Error('Use Run_AccountChecks_运行账号检查.py with an isolated temporary database.');
const out=process.env.QA_OUTPUT_DIR ? path.resolve(process.env.QA_OUTPUT_DIR) : null;
if(out)fs.mkdirSync(out,{recursive:true});
const checks=[];
const runtimeErrors=[];
const password='LocalAccountTest!2026'; // Artificial QA password; never a real user credential.
const first='qa_learner_'+Date.now();
const second=first+'_b';
async function check(name,action){await action();checks.push(name);console.log('PASS '+name);}
async function ready(){for(let n=0;n<50;n++){try{if((await fetch(base+'/api/health')).ok)return;}catch{}await new Promise(r=>setTimeout(r,200));}throw new Error('Temporary backend not ready.');}
(async()=>{
  await ready();
  const chrome='C:/Program Files/Google/Chrome/Application/chrome.exe';
  const browser=await chromium.launch({headless:true,...(fs.existsSync(chrome)?{executablePath:chrome}:{})});
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  const page=await context.newPage();
  page.on('pageerror',error=>runtimeErrors.push(error.message));
  const idle=async()=>{await page.locator('.loading').waitFor({state:'hidden'});await page.getByTestId('notice-N1').waitFor();};
  const get=async route=>{const response=await page.request.get(base+'/api'+route);return {status:response.status(),data:await response.json()};};
  const shot=async name=>{if(out)await page.screenshot({path:path.join(out,name),fullPage:true});};
  async function register(username,name,program='undergraduate',department='engineering'){
    await page.getByTestId('auth-register-tab').click();
    await page.getByTestId('auth-username').fill(username);
    await page.getByTestId('auth-password').fill(password);
    await page.getByTestId('auth-display-name').fill(name);
    await page.getByTestId('auth-program').selectOption(program);
    await page.getByTestId('auth-enrollment').selectOption('enrolled');
    await page.getByTestId('auth-department').selectOption(department);
    await Promise.all([page.waitForResponse(r=>r.url().endsWith('/auth/register')&&r.status()===200),page.getByTestId('auth-submit').click()]);
    await page.getByTestId('save-profile').waitFor();
    await page.getByTestId('nav-notices').click();await idle();
  }
  async function logout(){await page.getByTestId('logout').click();await page.getByTestId('auth-login-tab').waitFor();}
  async function login(username,pass=password){
    await page.getByTestId('auth-login-tab').click();
    await page.getByTestId('auth-username').fill(username);
    await page.getByTestId('auth-password').fill(pass);
    await page.getByTestId('auth-submit').click();
  }
  try{
    await page.goto(base);
    await check('Explicit local registration without GPA collection',async()=>{
      await page.getByTestId('auth-register-tab').click();
      assert.equal(await page.getByTestId('auth-password').getAttribute('type'),'password');
      assert.equal(await page.getByTestId('auth-program').inputValue(),'');
      assert.equal(await page.getByTestId('auth-enrollment').inputValue(),'');
      assert.equal(await page.getByTestId('auth-department').inputValue(),'');
      assert.equal(await page.getByTestId('profile-gpa_value').count(),0);
      await shot('01_Registration_个人注册.png');
    });
    let accountId;
    await check('Registration creates an independent student and unknown optional fields',async()=>{
      await register(first,'QA 학생');
      const me=(await get('/auth/me')).data;
      accountId=me.account.id;
      assert.equal(me.account.is_demo,false);
      assert.equal(me.account.role,'student');
      assert(!['A','B','C','staff'].includes(accountId));
      const profile=(await get('/profile')).data;
      for(const field of ['year','semester','international_student','current_dorm_resident','gpa_value','gpa_scale','gpa_period'])assert.equal(profile[field],null);
      assert.equal((await get('/notices/N1')).data.match.status,'missing_information');
      const cookies=await context.cookies();
      const session=cookies.find(cookie=>cookie.httpOnly);
      assert(session&&session.sameSite==='Lax');
      assert(!(await page.evaluate(()=>document.cookie)).includes(session.name));
      const storage=await page.evaluate(()=>JSON.stringify({...localStorage}));
      assert(!storage.includes(password)&&!storage.includes(session.value));
    });
    await check('Custom student information changes matching and survives refresh',async()=>{
      await page.getByTestId('nav-profile').click();
      await page.getByTestId('profile-year').fill('2');
      await page.getByTestId('profile-semester').fill('3');
      await page.getByTestId('profile-international_student').selectOption('true');
      await page.locator('.optional-profile > summary').click();
      await page.getByTestId('profile-current_dorm_resident').selectOption('true');
      const gpa=page.getByTestId('profile-gpa_value');
      if(!await gpa.isVisible())await page.locator('.optional-profile > summary').click();
      await gpa.fill('3.8');
      await page.getByTestId('profile-gpa_scale').fill('4.5');
      await page.getByTestId('profile-gpa_period').selectOption('previous_semester');
      await Promise.all([page.waitForResponse(r=>r.url().endsWith('/profile')&&r.request().method()==='PUT'&&r.status()===200),page.getByTestId('save-profile').click()]);
      await page.reload();await idle();
      assert.equal((await get('/auth/me')).data.account.id,accountId);
      const profile=(await get('/profile')).data;
      assert.equal(profile.gpa_value,3.8);assert.equal(profile.gpa_scale,4.5);
      assert.equal((await get('/notices/N1')).data.match.status,'conditions_met');
      assert.equal((await get('/notices/N3')).data.match.status,'conditions_met');
      await page.getByTestId('notice-N1').click();
      await page.getByTestId('generate-tasks').click();
      await page.locator('.task-item').first().waitFor();
      const tasks=(await get('/notices/N1')).data.tasks;
      assert.equal(tasks.length,4);
      const documentTask=tasks.find(task=>task.task_type==='document');
      assert(documentTask);
      await page.getByTestId('task-status-'+documentTask.id).selectOption('done');
      await page.waitForFunction(()=>document.querySelectorAll('.status-done').length>0);
      await page.reload();await idle();
      const restored=(await get('/notices/N1')).data.tasks;
      assert.equal(restored.find(task=>task.id===documentTask.id).status,'done');
      await page.getByTestId('notice-N1').click();await page.locator('.task-item').first().waitFor();
      await shot('02_PersonalTasks_自定义资料与进度.png');
    });
    await check('Cookie identity cannot be replaced by a demo header',async()=>{
      const response=await page.request.get(base+'/api/profile',{headers:{'X-Demo-Account':'B'}});
      assert.equal(response.status(),200);assert.equal((await response.json()).gpa_value,3.8);
      const denied=await page.request.get(base+'/api/staff/students/A/notices/N1/tasks',{headers:{'X-Demo-Account':'staff'}});
      assert.equal(denied.status(),403);
    });
    await check('Demo reset refuses to erase registered accounts or progress',async()=>{
      const response=await fetch(base+'/api/demo/reset',{method:'POST',headers:{'Content-Type':'application/json','X-Demo-Account':'staff'},body:'{}'});
      assert.equal(response.status,409);
      assert.equal((await get('/profile')).data.gpa_value,3.8);
      assert.equal((await get('/notices/N1')).data.tasks.length,4);
    });
    await check('Logout clears the session; two local students remain isolated',async()=>{
      await logout();
      assert.equal((await get('/profile')).status,401);
      await register(second,'QA 학생 B','master','business');
      assert.notEqual((await get('/auth/me')).data.account.id,accountId);
      assert.equal((await get('/profile')).data.gpa_value,null);
      assert.equal((await get('/notices/N1')).data.tasks.length,0);
      await logout();
      await login(first.toUpperCase());await idle();
      assert.equal((await get('/auth/me')).data.account.id,accountId);
      assert.equal((await get('/notices/N1')).data.tasks.length,4);
    });
    await check('Wrong password is a visible failure and does not create a session',async()=>{
      await logout();
      const result=page.waitForResponse(r=>r.url().endsWith('/auth/login')&&r.status()===401);
      await login(first,'IncorrectPassword!2026');await result;
      assert.equal((await get('/auth/me')).data.account,null);
      assert(await page.locator('.error').count()||await page.getByRole('alert').count());
      await login(first);await idle();
    });
    await check('Chinese mobile local account remains readable',async()=>{
      const language=page.getByRole('button',{name:'中文로 전환',exact:true});
      if(await language.count())await language.click();
      await page.setViewportSize({width:390,height:844});
      await page.getByTestId('nav-profile').click();
      assert.equal(await page.locator('html').getAttribute('lang'),'zh-CN');
      const dimensions=await page.evaluate(()=>({viewport:innerWidth,width:document.documentElement.scrollWidth}));
      assert(dimensions.width<=dimensions.viewport);
      await shot('03_Mobile_中文个人资料.png');
    });
    assert.equal(runtimeErrors.length,0);
    const result={checked_at:new Date().toISOString(),result:'PASS',checks,groups:checks.length,browser_runtime_errors:runtimeErrors.length,scope:'Artificial QA accounts in a temporary local database. Not production, SSO or school verification.'};
    if(out)fs.writeFileSync(path.join(out,'AccountResults_账号结果.json'),JSON.stringify(result,null,2));
    console.log(JSON.stringify({result:'PASS',groups:checks.length,runtimeErrors:runtimeErrors.length}));
  }catch(error){await shot('Failure_账号验证现场.png').catch(()=>{});console.error(error);process.exitCode=1;}
  finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
