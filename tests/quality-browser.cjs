const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.ASTAR_PLAYWRIGHT||'playwright');
const base=process.env.ASTAR_URL||'http://127.0.0.1:8765';
(async()=>{
 const b=await chromium.launch({headless:true,...(process.env.ASTAR_CHROMIUM?{executablePath:process.env.ASTAR_CHROMIUM}:{})});
 const c=await b.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});const p=await c.newPage();
 const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto(base+'/#import');await p.locator('#pdf-file').setInputFiles(path.resolve('test-results/layout-challenge.pdf'));
 await p.locator('[name=title]').fill('Layout challenge · filtering and triage');await p.locator('[name=minLessons]').fill('1');
 await p.getByRole('button',{name:'Prepare lessons'}).click();await p.waitForURL(/\/triage/,{timeout:90000});
 await p.locator('.triage-card').first().waitFor();
 const id=p.url().match(/course\/([a-f0-9]+)/)[1];
 let course=await(await p.request.get(base+'/api/courses/'+id)).json();
 assert.equal(course.lessons[0].pageStart,5);assert.equal(course.chapters.length,2);
 assert.equal(course.report.quality.high,1);assert(course.report.quality.automatic>0);
 assert.match(await p.locator('.triage-card').first().textContent(),/HIGH PRIORITY.*PDF 8/s);
 const groupCount=await p.locator('.triage-card').count();assert(groupCount<course.lessons.length);
 await p.screenshot({path:'test-results/10-triage.png',fullPage:true});
 await p.getByRole('button',{name:'Open affected lesson'}).first().click();await p.locator('#reviewed').check();await p.locator('#save-course').click();
 await p.locator('#save-status').filter({hasText:'Saved on this computer'}).waitFor();
 await p.getByRole('button',{name:'Back to attention queue'}).click();
 assert.equal(await p.locator('.triage-card').count(),groupCount-1);
 await p.getByRole('button',{name:'Conversion report',exact:true}).click();
 await p.getByRole('heading',{name:'What ASTAR left out'}).waitFor();
 await p.locator('.audit-page').first().locator('summary').click();
 await p.screenshot({path:'test-results/11-exclusion-log.png',fullPage:true});
 const entry=course.report.analysis.excluded[0];await p.locator(`[data-restore="${entry.id}"]`).click();
 await p.getByText(/Text restored to/).waitFor();
 course=await(await p.request.get(base+'/api/courses/'+id)).json();assert.equal(course.report.analysis.excluded[0].restored,true);
 assert(course.lessons.some(l=>l.blocks.some(b=>b.source==='restored')));
 await p.setViewportSize({width:390,height:844});await p.getByRole('button',{name:/Needs attention/}).click();
 assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await p.screenshot({path:'test-results/12-triage-mobile.png',fullPage:true});
 const real=process.env.ASTAR_REAL_COURSE;
 if(real){
  await p.setViewportSize({width:1440,height:1000});const original=await(await p.request.get(base+'/api/courses/'+real)).json();await p.goto(base+'/#course/'+real+'/triage');
  await p.getByRole('heading',{name:original.title,exact:true}).waitFor();
  await p.locator('#rebuild-course').click();
  await p.waitForURL(u=>u.hash.endsWith('/triage')&&!u.hash.includes(real),{timeout:240000});
  const rebuiltId=p.url().match(/course\/([a-f0-9]+)/)[1];
  const rebuilt=await(await p.request.get(base+'/api/courses/'+rebuiltId)).json();
  assert(rebuilt.report.analysis);assert.equal(rebuilt.lessons[0].pageStart,13);
  assert.equal(rebuilt.chapters.length,15);
  assert(!rebuilt.lessons.some(l=>l.blocks.some(b=>/SCERT\s+TELANGANA/.test(b.text))));
  assert(!rebuilt.lessons.some(l=>l.blocks.some(b=>b.page<13)));
  assert(!rebuilt.lessons.some(l=>l.blocks.some(b=>b.page>=352)));
  assert(rebuilt.lessons.some(l=>l.presentation==='layout'));
  await p.screenshot({path:'test-results/13-real-book-triage.png',fullPage:true});
  await p.getByRole('button',{name:'Reader',exact:true}).click();await p.locator('[data-chapter]').first().click();await p.locator('[data-lesson]').first().click();
  await p.locator('.focused-page img').first().waitFor();
  await p.screenshot({path:'test-results/14-real-maths-lesson.png',fullPage:true});
  fs.writeFileSync('test-results/real-book-results.json',JSON.stringify({rebuiltId,title:rebuilt.title,pages:rebuilt.source.pages,chapters:rebuilt.chapters.length,lessons:rebuilt.lessons.length,
   skippedPages:rebuilt.report.pages.filter(p=>p.disposition==='excluded').map(p=>p.number),quality:rebuilt.report.quality,
   layoutLessons:rebuilt.lessons.filter(l=>l.presentation==='layout').length},null,2));
 }
 assert.deepEqual(errors,[]);await b.close();console.log('PASS: ranked triage, grouped issues, selective resolution, exclusion restore, responsive layout'+(real?', and actual textbook rebuild':''));
})().catch(e=>{console.error(e);process.exit(1);});
