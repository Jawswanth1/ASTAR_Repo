/* Run against the local server. Playwright is a test dependency, not an app dependency. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.ASTAR_PLAYWRIGHT || 'playwright');
const base = process.env.ASTAR_URL || 'http://127.0.0.1:8765';
const results = path.resolve('test-results');
fs.mkdirSync(results,{recursive:true});

(async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.ASTAR_CHROMIUM?{executablePath:process.env.ASTAR_CHROMIUM}:{})});
  const context=await browser.newContext({viewport:{width:1440,height:1050},acceptDownloads:true});
  const page=await context.newPage();
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);await page.getByRole('heading',{name:'Textbook library',exact:true}).waitFor();
  await page.screenshot({path:path.join(results,'01-library.png'),fullPage:true});
  await page.getByRole('link',{name:'Prepare a textbook'}).click();
  await page.locator('#pdf-file').setInputFiles(path.join(results,'sample-science.pdf'));
  await page.locator('[name=title]').fill('Sample science · Original test content');
  await page.screenshot({path:path.join(results,'02-import.png'),fullPage:true});
  await page.getByRole('button',{name:'Prepare lessons'}).click();
  await page.waitForURL(/course\/[a-f0-9]+\/triage/,{timeout:90000});
  await page.getByRole('button',{name:'All lessons',exact:true}).click();
  await page.locator('#lesson-title').waitFor();
  const courseId=page.url().match(/course\/([a-f0-9]+)/)[1];
  const original=await (await page.request.get(`${base}/api/courses/${courseId}`)).json();
  assert.equal(original.chapters.length,2);assert(original.lessons.length>1);
  await page.locator('#lesson-title').fill('Sunlight and leaves');
  await page.locator('#add-mcq').click();
  const q=page.locator('[data-q]').first();
  await q.locator('[data-prop=prompt]').fill('Which part of a plant captures sunlight?');
  for (const [i,value] of ['Leaves','Roots','Soil','Stones'].entries()) await q.locator(`[data-option="${i}"]`).fill(value);
  await q.locator('[data-answer="0"]').check();
  await page.locator('#add-written').click();
  await page.locator('[data-q]').nth(1).locator('[data-prop=prompt]').fill('Explain how water moves through a plant. Answer in your notebook.');
  await page.locator('#reviewed').check();
  await page.locator('#save-course').click();await page.getByText('Course saved.',{exact:true}).waitFor();
  await page.screenshot({path:path.join(results,'03-review.png'),fullPage:true});
  const saved=await (await page.request.get(`${base}/api/courses/${courseId}`)).json();
  assert.equal(saved.lessons[0].title,'Sunlight and leaves');assert.equal(saved.lessons[0].questions.length,2);assert.equal(saved.lessons[0].reviewed,true);
  const [readerDownload]=await Promise.all([page.waitForEvent('download'),page.locator('#export-reader').click()]);
  const offlinePath=path.join(results,'astar-reader.html');await readerDownload.saveAs(offlinePath);
  const [packageDownload]=await Promise.all([page.waitForEvent('download'),page.locator('#export-package').click()]);
  const packagePath=path.join(results,'sample.astar.json');await packageDownload.saveAs(packagePath);
  const exported=JSON.parse(fs.readFileSync(packagePath,'utf8'));assert(Object.keys(exported.assets).length>=4);
  // Correct source attribution survives editing and package export.
  assert.equal(exported.source.pages,4);assert.equal(exported.lessons[0].questions[0].origin,'teacher');
  await page.getByRole('button',{name:'Reader',exact:true}).click();
  await page.locator('[data-chapter]').first().click();await page.locator('[data-lesson]').first().click();
  await page.getByRole('button',{name:'Reading text',exact:true}).click();
  await page.locator('[data-answer="0"]').first().click();await page.getByText('Correct.',{exact:true}).waitFor();
  await page.screenshot({path:path.join(results,'04-reader.png'),fullPage:true});
  await page.getByRole('button',{name:'Mark complete & continue'}).click();
  assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem(Object.keys(localStorage).find(k=>k.startsWith('astar-progress-')))).completed.length),1);
  await page.getByRole('button',{name:'3-button view'}).click();
  await page.screenshot({path:path.join(results,'05-device.png'),fullPage:true});
  // Exercise boundary editing and save validation after real UI mutations.
  await page.goto(`${base}/#course/${courseId}/review/0`);
  const split=page.locator('[data-split]').first();
  if(await split.count()){
    await split.click();await page.locator('#save-course').click();await page.locator('#save-status').filter({hasText:'Saved on this computer'}).waitFor();
    const splitCourse=await (await page.request.get(`${base}/api/courses/${courseId}`)).json();
    assert.equal(splitCourse.lessons.length,saved.lessons.length+1);
    await page.locator('#merge-next').click();await page.locator('#save-course').click();await page.locator('#save-status').filter({hasText:'Saved on this computer'}).waitFor();
    const merged=await (await page.request.get(`${base}/api/courses/${courseId}`)).json();assert.equal(merged.lessons.length,saved.lessons.length);
  }
  // Package install via real UI, with a new local course ID.
  await page.getByRole('link',{name:'Textbook library'}).click();
  await page.locator('#package-file').setInputFiles(packagePath);await page.waitForURL(/course\/[a-f0-9]+\/review\/0/);
  assert.notEqual(page.url().match(/course\/([a-f0-9]+)/)[1],courseId);
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('link',{name:'Prepare a textbook'}).click();
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
  await page.screenshot({path:path.join(results,'06-mobile.png'),fullPage:true});
  // Network disabled; this file has its own scripts, images, course, and progress.
  const offline=await browser.newContext({viewport:{width:1000,height:900},offline:true});
  const offlinePage=await offline.newPage();const offlineErrors=[];offlinePage.on('pageerror',e=>offlineErrors.push(e.message));
  const remote=[];offlinePage.on('request',r=>{if(/^https?:/.test(r.url()))remote.push(r.url());});
  await offlinePage.goto(pathToFileURL(offlinePath).href);
  await offlinePage.locator('[data-chapter]').first().click();await offlinePage.locator('[data-lesson]').first().click();
  await offlinePage.getByRole('button',{name:'Original pages + diagrams',exact:true}).click();
  const image=offlinePage.locator('.source-page img').first();await image.waitFor();
  assert.equal(await image.evaluate(i=>i.complete&&i.naturalWidth>0),true);
  await offlinePage.getByRole('button',{name:'Reading text',exact:true}).click();
  await offlinePage.locator('[data-answer="0"]').first().click();await offlinePage.getByText('Correct.',{exact:true}).waitFor();
  await offlinePage.getByRole('button',{name:'Mark complete & continue'}).click();
  await offlinePage.reload();await offlinePage.getByRole('button',{name:/Continue:/}).waitFor();
  await offlinePage.screenshot({path:path.join(results,'07-offline.png'),fullPage:true});
  assert.deepEqual(remote,[]);assert.deepEqual(errors,[]);assert.deepEqual(offlineErrors,[]);
  // Host / origin checks and invalid import handling.
  const rejected=await page.request.post(`${base}/api/packages`,{headers:{Origin:'https://unrelated.example'},data:{}});assert.equal(rejected.status(),400);
  const invalid=await page.request.post(`${base}/api/import`,{data:'This is not a PDF'});assert.equal(invalid.status(),400);
  fs.writeFileSync(path.join(results,'browser-results.json'),JSON.stringify({passed:true,courseId,lessons:original.lessons.length,remoteRequests:remote,consoleErrors:errors},null,2));
  await browser.close();console.log('PASS: import, review, MCQ, notebook practice, save, split/merge, packages, progress, mobile layout, and standalone reader with networking disabled.');
})().catch(error=>{console.error(error);process.exit(1);});
