const {chromium}=require('C:/Users/ranji/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('assert/strict'),fs=require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Users/ranji/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe'});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8782/#course/11111111111111111111111111111111/structure');
 await page.locator('#structure-page').waitFor({timeout:90000});
 await page.locator('#structure-page').fill('351');await page.locator('#structure-page').press('Tab');
 await page.locator('#structure-kind').selectOption('question');
 const opts=await page.locator('#structure-object option').evaluateAll(xs=>xs.map(x=>({id:x.value,text:x.textContent})));
 assert.equal(opts.length,10);const q=opts.find(x=>x.text.includes('question 7 ·'));
 assert(q);await page.locator('#structure-object').selectOption(q.id);
 await page.getByRole('heading',{name:'question 7',exact:true}).waitFor();
 await page.locator('.source-overlay img').evaluate(img=>img.decode());
 await page.screenshot({path:'benchmarks/representative-book/review-question-7.png',fullPage:true});
 await page.locator('#structure-page').fill('367');await page.locator('#structure-page').press('Tab');
 await page.locator('#structure-kind').selectOption('answer');assert.equal(await page.locator('#structure-object option').count(),10);
 await page.screenshot({path:'benchmarks/representative-book/review-answers.png',fullPage:true});
 assert.deepEqual(errors,[]);fs.writeFileSync('benchmarks/representative-book/browser-validation.json',JSON.stringify({passed:true,questionObjectsOnPage351:10,answerObjectsOnPage367:10,originalImageDecoded:true,consoleErrors:errors},null,2));
 console.log('Full-book review browser PASS');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
