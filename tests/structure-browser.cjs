const {chromium}=require('C:/Users/ranji/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),assert=require('assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Users/ranji/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe'});
 try{
 const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));const base='http://127.0.0.1:8781',id='a'.repeat(32);
 const before=await(await page.request.get(base+'/api/courses/'+id)).json();
 const question=before.structure.objects.find(o=>o.kind==='question');
 await page.goto(base+'/#course/'+id+'/structure');await page.locator('#structure-page').waitFor();
 await page.locator('#structure-kind').selectOption('question');await page.locator('#structure-object').selectOption(question.id);
 await page.locator('#object-correction').fill('Reviewer correction retained separately.');
 await page.locator('#object-note').fill('Fixture review: source image compared.');
 await page.locator('#object-status').selectOption('needs-correction');
 await page.locator('#save-structure').click();
 await page.waitForTimeout(1500);console.log('Save notice:',await page.locator('#notice').innerText(), 'errors:',errors);
 await page.getByText('Structural review saved. Original evidence is unchanged.',{exact:true}).waitFor();
 await page.screenshot({path:'test-results/structure-desktop.png',fullPage:true});
 await page.reload();await page.locator('#structure-kind').selectOption('question');await page.locator('#structure-object').selectOption(question.id);
 assert.equal(await page.locator('#object-correction').inputValue(),'Reviewer correction retained separately.');
 const after=await(await page.request.get(base+'/api/courses/'+id)).json();
 assert.equal(after.structure.evidenceHash,before.structure.evidenceHash);
 assert.equal(after.structure.objects.find(o=>o.id===question.id).text,question.text);
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-package').click()]);
 await download.saveAs('test-results/structure-package.astar.json');
 const pkg=JSON.parse(fs.readFileSync('test-results/structure-package.astar.json','utf8'));
 assert(pkg.assets['assets/original-0002.png']);
 assert(pkg.structure.objects.some(o=>o.kind==='answer'&&o.links.some(l=>l.kind==='answer-candidate'&&l.status==='unverified')));
 await page.locator('#structure-page').fill('2');await page.locator('#structure-page').press('Tab');
 await page.locator('#structure-kind').selectOption('answer');
 assert(await page.locator('#structure-object option').count()>0);
 await page.setViewportSize({width:390,height:844});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.screenshot({path:'test-results/structure-mobile.png',fullPage:true});
 assert.deepEqual(errors,[]);
 fs.writeFileSync('test-results/structure-browser-results.json',JSON.stringify({passed:true,checks:['source page and object side-by-side','saved correction survives reload','raw evidence and extracted text unchanged','source images and answer candidates exported','answer-page review','mobile width'],consoleErrors:errors},null,2));
 console.log('Structure browser PASS');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
