const $ = (selector, root=document) => root.querySelector(selector);
const $$ = (selector, root=document) => [...root.querySelectorAll(selector)];
const esc = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = {course:null, dirty:false, reader:null, status:null, job:null};
const app = $('#app');
function notice(message, error=false) {
  $('#notice').className = message ? 'notice'+(error?' error':'') : '';
  $('#notice').textContent = message;
}
async function api(path, options={}) {
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) throw Error(result.error || 'Request failed.');
  return result;
}
function fail(error) { notice(error.message || String(error),true); }
function dirty() { state.dirty=true; const s=$('#save-status'); if(s)s.textContent='Unsaved changes'; }
function unreview(lesson) { lesson.reviewed=false;if($('#reviewed'))$('#reviewed').checked=false;dirty(); }
async function save(silent=false) {
  if (!state.course || !state.dirty) return true;
  const saved=await api('/api/courses/'+state.course.id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(state.course)});
  if(saved.quality)state.course.report.quality=saved.quality;
  if(saved.lessonQuality)for(const item of saved.lessonQuality){const l=state.course.lessons.find(l=>l.id===item.id);if(l){l.quality=item.quality;l.warnings=item.warnings;}}
  state.dirty=false;
  if ($('#save-status')) $('#save-status').textContent='Saved on this computer';
  if (!silent) {
    const parts=location.hash.replace(/^#\/?/,'').split('/');
    if(parts[0]==='course'&&parts[2]==='review')review(Number(parts[3])||0);
    notice('Course saved.');
  }
  return true;
}
function download(url) { const a=document.createElement('a');a.href=url;a.download='';a.click(); }
function bindClicks() {
  $$('[data-go]',app).forEach(b=>b.onclick=()=>{location.hash=b.dataset.go;});
}
async function library() {
  const courses=await api('/api/courses');
  app.innerHTML=`<div class="content"><div class="page-heading"><div><p class="eyebrow">YOUR OFFLINE LEARNING WORKSPACE</p><h1>A whole textbook.<br>One lesson at a time.</h1><p class="subtitle">Turn textbook PDFs into small, portable lessons. Keep the original explanations, diagrams, and questions within reach.</p></div><button class="primary" data-go="import">＋ Prepare a textbook</button></div>
    <div class="stats"><div class="stat"><small>TEXTBOOKS IN YOUR LIBRARY</small><strong>${courses.length.toString().padStart(2,'0')}</strong><span>stored locally</span></div><div class="stat"><small>LESSONS PREPARED</small><strong>${courses.reduce((a,c)=>a+c.lessons,0).toString().padStart(2,'0')}</strong><span>ready to explore</span></div><div class="stat"><small>NEED ATTENTION</small><strong>${courses.reduce((a,c)=>a+(c.attention||0),0).toString().padStart(2,'0')}</strong><span>likely extraction problems</span></div></div>
    <div class="section-row"><h2>Textbook library</h2><label class="package-import tiny">Import an ASTAR package<input type="file" id="package-file" accept=".json"></label></div>
    <div class="book-grid">${courses.length?courses.map(c=>`<article class="book-card"><div class="book-cover"><div class="book-emblem">▤</div><span class="pill">${c.analyzerVersion==='1.0'?'REBUILD AVAILABLE':c.attention?'CHECK FLAGGED LESSONS':'AUTOMATIC CHECKS PASSED'}</span></div><div class="book-body"><p class="eyebrow">${esc(c.subject)}</p><h3>${esc(c.title)}</h3><p>${c.chapters} chapters · ${c.lessons} lessons · ${c.attention||0} need attention</p><div class="book-actions"><button data-go="course/${c.id}/triage">View checks</button><button class="primary" data-go="course/${c.id}/read">Open reader →</button></div></div></article>`).join(''):
      '<div class="empty"><div class="symbol">▤</div><h2>Your first textbook starts here.</h2><p>Choose a PDF from your computer. ASTAR will prepare a draft course for you to check and take offline.</p><button class="primary" data-go="import">Choose a textbook PDF →</button></div>'}</div>
    <div class="callout"><span class="symbol">☼</span><div><h3>Prepared here. Learned anywhere.</h3><p>Export a complete offline reader. The studio highlights likely problems for targeted review. Copy it by USB or memory card and open it in a browser, with no account or internet connection.</p></div></div>
    <p class="footer-note">Original textbook wording is retained where extraction allows. Source pages stay alongside the text for diagrams and verification.</p></div>`;
  bindClicks();
  $('#package-file').onchange=async e=>{
    const file=e.target.files[0];if(!file)return;
    notice('Importing the course package…');
    try { if(file.size>300*1024*1024)throw Error('Package exceeds 300 MB.');const result=await api('/api/packages',{method:'POST',headers:{'Content-Type':'application/json'},body:await file.text()});notice('Package installed.');location.hash=`course/${result.courseId}/review/0`; }catch(error){fail(error);}
  };
}
function importView() {
  app.innerHTML=`<div class="content"><div class="page-heading"><div><p class="eyebrow">TEXTBOOK → CHAPTERS → LESSONS</p><h1>Prepare a textbook.</h1><p class="subtitle">Start with the original PDF. All processing happens on this computer.</p></div></div><div class="steps"><span><b>1</b> Import your PDF</span><span><b>2</b> Review the lessons</span><span><b>3</b> Take it offline</span></div>
    <div class="form-layout"><section class="panel"><form id="import-form"><div class="dropzone"><label for="pdf-file">Choose your textbook PDF</label><input id="pdf-file" type="file" accept="application/pdf,.pdf" required><p>Digital or scanned PDF · up to 200 MB / 2,000 pages</p></div>
    <label class="field">Book title<input name="title" maxlength="500" placeholder="e.g. Science · Class 8"></label><div class="field-row"><label class="field">Subject<input name="subject" value="Science" maxlength="500"></label><label class="field">OCR language code<input name="language" value="eng" maxlength="100"><small>Tesseract codes: eng, hin, tam, or eng+hin. The matching language files must be installed.</small></label></div>
    <label class="field">Organise lessons<select name="planningMode" id="planning-mode"><option value="sessions">30-minute study sessions within each unit</option><option value="words">Custom word-based lessons</option></select></label>
    <div id="session-settings"><div class="field-row"><label class="field">Session minutes<input name="sessionMinutes" type="number" value="30" min="10" max="90" required></label><label class="field">Minutes for textbook practice and review<input name="practiceMinutes" type="number" value="15" min="0" max="89" required></label></div><div class="field-row"><label class="field">Reading pace (words/minute)<input name="readingWpm" type="number" value="120" min="40" max="300" required></label><label class="field">Number of units in the textbook (optional)<input name="expectedUnits" type="number" value="0" min="0" max="2000"><small>0 = detect automatically. A mismatch is flagged; no units are invented.</small></label></div><p class="tiny">A 30-minute target defaults to 15 minutes reading and 15 minutes for the textbook's activities. Timing is an estimate. Short units remain short; exercises stay in their original place.</p></div>
    <div id="word-settings" class="hidden"><div class="field-row"><label class="field">Words per lesson<input name="wordsPerLesson" type="number" value="220" min="80" max="1200" required></label><label class="field">Target minimum lessons<input name="minLessons" type="number" value="1" min="1" max="2000" required></label></div></div>
    <label class="field">Monochrome images<select name="imageMode"><option value="dither">Pattern shading · preserves colour differences</option><option value="threshold">Strict black & white · cleaner line art</option></select></label>
    <label class="check"><input name="ocr" type="checkbox" checked><span>Try offline OCR on scanned pages.<br><small class="tiny">${state.status?.ocr?'Tesseract is available on this computer.':'Tesseract is not installed. Scanned pages will still be readable as images, with a warning that text needs transcription.'}</small></span></label>
    <details><summary class="tiny">Set unit / chapter boundaries manually (optional)</summary><label class="field" style="margin-top:16px">One chapter per line<textarea name="chapterPlan" placeholder="5 | Chapter 1: Crop Production&#10;18 | Chapter 2: Microorganisms"></textarea><small>Use physical PDF page numbers, starting at 1. Without a plan, ASTAR tries PDF bookmarks and English chapter headings. Pages before the first chapter are excluded from lessons and kept in the audit log.</small></label></details>
    <div class="divider"></div><button class="primary" type="submit" id="prepare-button">Prepare lessons →</button></form><div id="import-progress"></div></section>
    <aside class="panel"><h2>What stays with the book</h2><div class="aside-item"><div class="aside-number">01 / ORIGINAL WORDING</div><h3>Reading, without summarizing</h3><p>Text is divided into smaller lessons while keeping its wording and sequence.</p></div><div class="aside-item"><div class="aside-number">02 / MONOCHROME SOURCE</div><h3>Diagrams stay available</h3><p>Every page is preserved in black and white, including vector diagrams, tables, equations, and questions.</p></div><div class="aside-item"><div class="aside-number">03 / HUMAN REVIEW</div><h3>Check the source when uncertain</h3><p>ASTAR filters non-learning pages and repeated page furniture, then ranks uncertain extraction for targeted review.</p></div><div class="aside-item"><div class="aside-number">04 / NOTEBOOK PRACTICE</div><h3>Room to think on paper</h3><p>Original textbook questions stay word for word, in source order. Answers are not invented. Optional author-added practice is labelled separately.</p></div></aside></div></div>`;
  $('#planning-mode').onchange=e=>{const sessions=e.target.value==='sessions';$('#session-settings').classList.toggle('hidden',!sessions);$('#word-settings').classList.toggle('hidden',sessions);};
  $('#pdf-file').onchange=e=>{const f=e.target.files[0];if(f&&!$('#import-form').elements.title.value)$('#import-form').elements.title.value=f.name.replace(/\.pdf$/i,'');};
  $('#import-form').onsubmit=async e=>{
    e.preventDefault();const form=e.currentTarget,file=$('#pdf-file').files[0];if(!file)return;
    if(file.size>200*1024*1024)return fail(Error('PDF exceeds 200 MB.'));
    if(Number(form.elements.practiceMinutes.value)>=Number(form.elements.sessionMinutes.value))return fail(Error('Practice time must be shorter than the whole session.'));
    const values=new FormData(form),params=new URLSearchParams();
    for(const [k,v] of values)params.set(k,String(v));params.set('ocr',form.elements.ocr.checked?'true':'false');params.set('filename',file.name);
    $('#prepare-button').disabled=true;notice('Uploading to the local converter…');
    try {const job=await api('/api/import?'+params,{method:'POST',headers:{'Content-Type':'application/pdf'},body:file});state.job=job.jobId;sessionStorage.setItem('astar-job',job.jobId);await pollJob();}
    catch(error){fail(error);if($('#prepare-button'))$('#prepare-button').disabled=false;}
  };
  if(state.job){$('#prepare-button').disabled=true;pollJob().catch(fail);}
}
async function pollJob() {
  const jobId=state.job;
  while(state.job===jobId && jobId) {
    const job=await api('/api/jobs/'+jobId);
    const slot=$('#import-progress');
    if(slot)slot.innerHTML=`<div class="progress-box"><h3>${esc(job.message)}</h3><progress max="${job.total||1}" value="${job.done||0}"></progress><p>Keep the local server running. You can return to the library while this finishes.</p></div>`;
    if(job.status==='complete'){state.job=null;sessionStorage.removeItem('astar-job');notice('Learning content prepared. The attention queue shows likely extraction problems first.');location.hash=`course/${job.courseId}/triage`;return;}
    if(job.status==='error'){state.job=null;sessionStorage.removeItem('astar-job');if($('#prepare-button'))$('#prepare-button').disabled=false;throw Error(job.message);}
    await new Promise(resolve=>setTimeout(resolve,700));
  }
}
function toolbar(course,tab) {
  return `<div class="course-toolbar"><div class="tabs"><button data-go="course/${course.id}/triage" class="${tab==='triage'?'active':''}">Needs attention${course.report.quality?.attention?' · '+course.report.quality.attention:''}</button><button data-go="course/${course.id}/review/0" class="${tab==='review'?'active':''}">All lessons</button><button data-go="course/${course.id}/report" class="${tab==='report'?'active':''}">Conversion report</button><button data-go="course/${course.id}/read" class="${tab==='read'?'active':''}">Reader</button></div><div class="actions"><button id="rebuild-course">Rebuild import</button><button id="export-package">Export package</button><button class="primary" id="export-reader">↓ Offline reader</button></div></div>`;
}
function bindToolbar() {
  const structureButton=document.createElement('button');structureButton.textContent='Structure review';structureButton.dataset.go=`course/${state.course.id}/structure`;$('.course-toolbar .tabs',app).prepend(structureButton);
  if(state.course.structure && !location.hash.includes('/structure')){const note=document.createElement('p');note.className='warning';note.textContent='Automatic lesson checks do not certify textbook structure. Review detected questions, options, figures and answer relationships in Structure review before using this material for teaching.';$('.course-toolbar',app).after(note);}
  bindClicks();
  $('#export-package').onclick=async()=>{try{await save(true);download('/api/courses/'+state.course.id+'/export');notice('Downloading the course with its source images.');}catch(error){fail(error);}};
  $('#export-reader').onclick=async()=>{try{await save(true);download('/api/courses/'+state.course.id+'/reader');notice('Downloading one HTML file. Open that file directly to study without this server.');}catch(error){fail(error);}};
  $('#rebuild-course').onclick=async()=>{try{await save(true);const result=await api('/api/courses/'+state.course.id+'/rebuild',{method:'POST'});state.job=result.jobId;sessionStorage.setItem('astar-job',result.jobId);notice('Rebuilding into a new course with document analysis. Your existing course and edits are retained.');await pollJob();}catch(error){fail(error);}};
}
function makeQuestion(q) {
  return `<div class="question-editor" data-q="${esc(q.id)}"><div class="field-row"><label class="field">Question type<select data-prop="type"><option value="mcq" ${q.type==='mcq'?'selected':''}>Multiple choice</option><option value="notebook" ${q.type==='notebook'?'selected':''}>Notebook answer</option></select></label><label class="field">Placement<select data-prop="placement"><option value="middle" ${q.placement==='middle'?'selected':''}>Between lesson text</option><option value="end" ${q.placement==='end'?'selected':''}>End of lesson</option></select></label></div><label class="field">Prompt<textarea data-prop="prompt">${esc(q.prompt)}</textarea></label>${q.type==='mcq'?`<p class="tiny">Select the correct answer. You are responsible for checking this key.</p>${q.options.map((o,i)=>`<label class="question-option"><input type="radio" name="answer-${q.id}" data-answer="${i}" ${q.answer===i?'checked':''}><input type="text" data-option="${i}" value="${esc(o)}" placeholder="Option ${String.fromCharCode(65+i)}" maxlength="2000"></label>`).join('')}`:''}<button class="link-button" data-remove-q="${esc(q.id)}">Remove question</button></div>`;
}
function review(index) {
  const c=state.course,lesson=c.lessons[Math.min(Math.max(0,index),c.lessons.length-1)];
  app.innerHTML=`<div class="content"><div class="page-heading"><div><p class="eyebrow">TEXTBOOK STUDIO · DRAFT REVIEW</p><h1>${esc(c.title)}</h1><p class="subtitle">${c.lessons.length} lessons · ${c.chapters.length} chapters · ${c.lessons.filter(l=>l.reviewed).length} reviewed</p></div></div>${toolbar(c,'review')}<div class="review-layout"><aside class="lesson-list">${c.chapters.map(ch=>`<h3>${esc(ch.title)}</h3>${c.lessons.map((l,i)=>l.chapterId===ch.id?`<button class="lesson-row ${l.id===lesson.id?'active':''}" data-go="course/${c.id}/review/${i}"><span class="num">${l.reviewed?'✓':i+1}</span><span>${esc(l.title)}<small>PDF ${l.pageStart}–${l.pageEnd} · ${l.reviewed?'Reviewed':'Draft'}</small></span></button>`:'').join('')}`).join('')}</aside><section class="editor"><div class="editor-head"><h2>Lesson ${c.lessons.indexOf(lesson)+1}</h2><span class="tiny">Compare with the source →</span></div><div class="editor-columns"><div class="editor-fields"><label class="field">Lesson title<input id="lesson-title" value="${esc(lesson.title)}" maxlength="500"></label><label class="field">Chapter<select id="lesson-chapter">${c.chapters.map(ch=>`<option value="${esc(ch.id)}" ${ch.id===lesson.chapterId?'selected':''}>${esc(ch.title)}</option>`).join('')}</select></label>${lesson.warnings.map(w=>`<div class="warning">${esc(w)}</div>`).join('')}
    <h3>Text & original questions</h3><p class="tiny">Text stays in source order. Use “Start a new lesson here” to adjust a boundary. Mark original questions so they appear as notebook prompts.</p><div id="blocks">${lesson.blocks.map((b,i)=>`<div class="block-edit" data-block="${esc(b.id)}"><div class="block-tools"><span>PDF ${b.page} · ${esc(b.source)}</span><select aria-label="Block type" data-block-type><option value="text" ${b.type==='text'?'selected':''}>Reading text</option><option value="question" ${b.type==='question'?'selected':''}>Original question</option><option value="source" ${b.type==='source'?'selected':''}>Source image</option></select>${i>0?`<button data-split="${i}">Start new lesson</button>`:''}</div><textarea aria-label="Text block ${i+1}" data-block-text>${esc(b.text)}</textarea></div>`).join('')}</div><button id="add-block">＋ Add text block</button><hr class="divider"><h3>Additional practice</h3><p class="tiny">Questions entered here are labelled “Added in studio”. Middle questions appear after the midpoint text block unless you choose another block below.</p><div id="questions">${lesson.questions.map(q=>makeQuestion(q)+ (q.placement==='middle'?`<label class="field">Place after<select data-placement="${esc(q.id)}"><option value="">Midpoint of lesson</option>${lesson.blocks.map((b,i)=>`<option value="${esc(b.id)}" ${q.afterBlockId===b.id?'selected':''}>Block ${i+1}: ${esc(b.text.slice(0,50))}</option>`).join('')}</select></label>`:'')).join('')}</div><div class="actions"><button id="add-mcq">＋ Multiple choice</button><button id="add-written">＋ Notebook question</button></div><hr class="divider"><label class="check"><input id="reviewed" type="checkbox" ${lesson.reviewed?'checked':''}><span>I have checked this lesson's text, diagrams, questions, and boundaries against the textbook.</span></label><button id="merge-next" ${c.lessons.indexOf(lesson)===c.lessons.length-1?'disabled':''}>Merge with next lesson</button></div><aside class="source-pane">${lesson.panels.map(p=>`<p>PDF PAGE ${p.page} · MONOCHROME SOURCE</p><a href="/courses/${c.id}/${esc(p.image)}" target="_blank" rel="noopener">Open image at full size ↗</a><img src="/courses/${c.id}/${esc(p.image)}" alt="Original PDF page ${p.page}" loading="lazy">`).join('')}</aside></div><div class="save-bar"><span id="save-status">${state.dirty?'Unsaved changes':'Saved on this computer'}</span><div class="actions"><button id="save-course">Save draft</button><button id="save-next">Save & next →</button></div></div></section></div></div>`;
  bindToolbar();
  $('.page-heading .eyebrow',app).textContent='LESSON EDITOR · '+(lesson.quality?.status==='attention'?'NEEDS ATTENTION':lesson.reviewed?'CHECKED BY YOU':'AUTOMATIC CHECKS PASSED');
  $('.page-heading .subtitle',app).textContent=`${c.lessons.length} lessons · ${c.report.quality?.attention||0} need attention · ${c.report.quality?.automatic||0} passed automatic checks`;
  const returnQueue=document.createElement('button');returnQueue.textContent='← Back to attention queue';returnQueue.onclick=()=>{location.hash=`course/${c.id}/triage`;};$('.editor-head',app).append(returnQueue);
  $$('[data-block]',app).forEach(el=>{const b=lesson.blocks.find(b=>b.id===el.dataset.block);if(b.type==='figure'){const option=document.createElement('option');option.value='figure';option.textContent='Learning diagram';option.selected=true;$('[data-block-type]',el).append(option);const img=document.createElement('img');img.src=`/courses/${c.id}/${b.image}`;img.alt='Extracted learning diagram';img.className='extracted-figure';el.append(img);$('[data-block-text]',el).classList.add('hidden');}});
  const refresh=()=>review(c.lessons.indexOf(lesson));
  $('#lesson-title').oninput=e=>{lesson.title=e.target.value;unreview(lesson);};
  $('#lesson-chapter').onchange=e=>{lesson.chapterId=e.target.value;unreview(lesson);};
  $('#reviewed').onchange=e=>{lesson.reviewed=e.target.checked;dirty();};
  $$('[data-block]').forEach(el=>{const block=lesson.blocks.find(b=>b.id===el.dataset.block);$('[data-block-text]',el).oninput=e=>{block.text=e.target.value;unreview(lesson);};$('[data-block-type]',el).onchange=e=>{block.type=e.target.value;unreview(lesson);};});
  $$('[data-split]').forEach(button=>button.onclick=()=>{
    const at=Number(button.dataset.split),moved=lesson.blocks.splice(at);
    const movedIds=new Set(moved.map(b=>b.id));
    const other={...lesson,id:'lesson-'+crypto.randomUUID(),title:lesson.title+' (continued)',blocks:moved,reviewed:false,
      questions:lesson.questions.filter(q=>q.afterBlockId?movedIds.has(q.afterBlockId):q.placement==='end')};
    const transferred=new Set(other.questions.map(q=>q.id));lesson.questions=lesson.questions.filter(q=>!transferred.has(q.id));lesson.reviewed=false;
    c.lessons.splice(c.lessons.indexOf(lesson)+1,0,other);updatePanels(lesson);updatePanels(other);dirty();refresh();
  });
  $('#add-block').onclick=()=>{lesson.blocks.push({id:'block-'+crypto.randomUUID(),type:'text',text:'',page:lesson.pageEnd,source:'teacher'});lesson.reviewed=false;dirty();refresh();};
  $$('[data-q]').forEach(box=>{const q=lesson.questions.find(q=>q.id===box.dataset.q);
    $$('[data-prop]',box).forEach(input=>input.oninput=()=>{q[input.dataset.prop]=input.value;unreview(lesson);if(input.tagName==='SELECT'){if(q.type==='mcq'&&!q.options){q.options=['','','',''];q.answer=0;}refresh();}});
    $$('[data-option]',box).forEach(input=>input.oninput=()=>{q.options[Number(input.dataset.option)]=input.value;unreview(lesson);});
    $$('[data-answer]',box).forEach(input=>input.onchange=()=>{q.answer=Number(input.dataset.answer);unreview(lesson);});
    $('[data-remove-q]',box).onclick=()=>{lesson.questions=lesson.questions.filter(x=>x.id!==q.id);lesson.reviewed=false;dirty();refresh();};
  });
  $$('[data-placement]').forEach(input=>input.onchange=()=>{const q=lesson.questions.find(q=>q.id===input.dataset.placement);q.afterBlockId=input.value||undefined;unreview(lesson);});
  const addQuestion=type=>{lesson.questions.push({id:'q-'+crypto.randomUUID(),type,prompt:'',placement:type==='mcq'?'middle':'end',origin:'teacher',...(type==='mcq'?{options:['','','',''],answer:0}:{})});lesson.reviewed=false;dirty();refresh();};
  $('#add-mcq').onclick=()=>addQuestion('mcq');$('#add-written').onclick=()=>addQuestion('notebook');
  $('#merge-next').onclick=()=>{
    const i=c.lessons.indexOf(lesson),next=c.lessons[i+1];if(!next)return;
    if(next.chapterId!==lesson.chapterId)return fail(Error('Move the next lesson into the same chapter before merging.'));
    lesson.blocks.push(...next.blocks);lesson.questions.push(...next.questions);lesson.panels=[...new Map([...lesson.panels,...next.panels].map(p=>[p.page,p])).values()];lesson.reviewed=false;c.lessons.splice(i+1,1);updatePanels(lesson);dirty();refresh();
  };
  $('#save-course').onclick=()=>save().catch(fail);
  $('#save-next').textContent='Save & next problem →';
  $('#save-next').onclick=async()=>{try{await save(true);const next=c.report.quality?.queue.find(id=>id!==lesson.id);if(next)location.hash=`course/${c.id}/review/${c.lessons.findIndex(l=>l.id===next)}`;else location.hash=`course/${c.id}/triage`;}catch(error){fail(error);}};
}
function updatePanels(lesson) {
  lesson.pageStart=Math.min(...lesson.blocks.map(b=>b.page));lesson.pageEnd=Math.max(...lesson.blocks.map(b=>b.page));
  lesson.panels=lesson.panels.filter(p=>p.page>=lesson.pageStart&&p.page<=lesson.pageEnd);
}
function report() {
  const c=state.course,r=c.report;
  app.innerHTML=`<div class="content"><div class="page-heading"><div><p class="eyebrow">EXTRACTION & QUALITY CHECKS</p><h1>Conversion report.</h1><p class="subtitle">${esc(c.title)} · ${c.source.pages} source pages · ${r.words.toLocaleString()} extracted words · ${c.lessons.length} current lessons</p></div></div>${toolbar(c,'report')}${r.warnings.map(w=>`<div class="warning">${esc(w)}</div>`).join('')}<div class="panel" style="margin:22px 0"><h2>Book & chapter titles</h2><p class="tiny">Chapter boundaries: ${esc(r.chapterMethod)}. To change chapter start pages, re-import the PDF with a chapter plan. You can move individual lessons between chapters in Review.</p><label class="field">Book title<input id="book-title" value="${esc(c.title)}" maxlength="500"></label><label class="field">Subject<input id="book-subject" value="${esc(c.subject)}" maxlength="500"></label>${c.chapters.map(ch=>`<label class="field">PDF page ${ch.startPage}<input data-chapter-title="${esc(ch.id)}" value="${esc(ch.title)}" maxlength="500"></label>`).join('')}<button class="primary" id="report-save">Save titles</button></div><div class="section-row"><h2>Page-by-page extraction</h2><span class="tiny">${esc(c.source.filename)}</span></div><div class="report-grid">${r.pages.map(p=>`<article class="report-page"><h3>Page ${p.number}</h3><span class="pill">${esc(p.source==='ocr'?'OCR TEXT':p.warnings.some(w=>w.includes('no extractable'))?'SOURCE IMAGE':'PDF TEXT')}</span>${p.warnings.length?p.warnings.map(w=>`<p>${esc(w)}</p>`).join(''):'<p>No extraction problems detected.</p>'}<a class="link-button" target="_blank" rel="noopener" href="/courses/${c.id}/${esc(p.image)}">Inspect source page ↗</a></article>`).join('')}</div><p class="footer-note">An automatic check cannot certify factual accuracy, original reading order, or diagram legibility. Review each lesson before using the course for teaching.</p></div>`;
  bindToolbar();$('#book-title').oninput=e=>{c.title=e.target.value;dirty();};$('#book-subject').oninput=e=>{c.subject=e.target.value;dirty();};$$('[data-chapter-title]').forEach(input=>input.oninput=()=>{c.chapters.find(ch=>ch.id===input.dataset.chapterTitle).title=input.value;dirty();});$('#report-save').onclick=()=>save().catch(fail);
  $('.footer-note',app).textContent='Source pages and the exclusion log remain available for audit. Automatic checks identify extraction problems; they do not certify factual correctness.';
  const audit=document.createElement('section');audit.className='panel exclusion-audit';audit.innerHTML=auditHTML(c);$('.course-toolbar',app).after(audit);bindAudit(c,audit);
}
function auditHTML(c) {
  const entries=c.report.analysis?.excluded||[],pageGroups=new Map();
  for(const entry of entries){if(!pageGroups.has(entry.page))pageGroups.set(entry.page,[]);pageGroups.get(entry.page).push(entry);}
  const omitted=c.report.pages.filter(p=>p.disposition==='excluded');
  return `<h2>What ASTAR left out</h2><p class="tiny">${omitted.length} non-learning pages · ${entries.filter(e=>!e.restored).length} excluded text blocks. The original PDF is retained. Restore any text below if needed.</p>${[...pageGroups].map(([page,items])=>`<details class="audit-page"><summary>PDF page ${page} · ${items.length} blocks · ${esc(items[0].reason)}</summary>${items.map(e=>`<div class="audit-entry"><span class="pill">${esc(e.category)}</span><p>${esc(e.text)}</p><small>${esc(e.reason)}</small><button data-restore="${esc(e.id)}" ${e.restored?'disabled':''}>${e.restored?'Restored':'Restore to nearest lesson'}</button></div>`).join('')}</details>`).join('')||'<p class="tiny">No content was automatically excluded.</p>'}`;
}
function bindAudit(c,root) {
  $$('[data-restore]',root).forEach(button=>button.onclick=async()=>{
    try{
      const e=c.report.analysis.excluded.find(e=>e.id===button.dataset.restore);if(e.restored)return;
      const lesson=[...c.lessons].sort((a,b)=>Math.abs(a.pageStart-e.page)-Math.abs(b.pageStart-e.page))[0];
      lesson.blocks.push({id:'restored-'+crypto.randomUUID(),type:'text',role:'text',text:e.text,page:e.page,bbox:e.bbox,source:'restored'});
      if(!lesson.panels.some(p=>p.page===e.page))lesson.panels.push({page:e.page,image:c.report.pages.find(p=>p.number===e.page).image});
      lesson.blocks.sort((a,b)=>a.page-b.page||(a.bbox?.[1]||0)-(b.bbox?.[1]||0));lesson.pageStart=Math.min(lesson.pageStart,e.page);lesson.pageEnd=Math.max(lesson.pageEnd,e.page);lesson.reviewed=false;e.restored=true;dirty();await save(true);report();notice(`Text restored to “${lesson.title}”.`);
    }catch(error){fail(error);}
  });
}
function triage() {
  const c=state.course,q=c.report.quality||{},groups=new Map();
  for(const id of q.queue||[]){const l=c.lessons.find(l=>l.id===id);if(!l)continue;const key=l.quality.issues.map(i=>i.code+':'+i.pages.join(',')).sort().join('|');if(!groups.has(key))groups.set(key,{lesson:l,lessons:[],risk:l.quality.risk});groups.get(key).lessons.push(l);}
  const excluded=c.report.pages.filter(p=>p.disposition==='excluded');
  app.innerHTML=`<div class="content"><div class="page-heading"><div><p class="eyebrow">AUTOMATIC EXTRACTION · EXCEPTIONS FIRST</p><h1>${esc(c.title)}</h1><p class="subtitle">${q.automatic||0} lessons passed automatic checks. ${q.attention||0} need attention. You can read or export the course without approving every lesson.</p></div></div>${toolbar(c,'triage')}${c.report.warnings.map(w=>`<div class="warning">${esc(w)}</div>`).join('')}<div class="stats"><div class="stat"><small>AUTOMATIC CHECKS PASSED</small><strong>${q.automatic||0}</strong><span>no detected extraction issues</span></div><div class="stat"><small>PROBLEM GROUPS</small><strong>${groups.size}</strong><span>${q.high||0} high-risk lessons</span></div><div class="stat"><small>NON-LEARNING PAGES SKIPPED</small><strong>${excluded.length}</strong><span>cover, contents, publication & reference matter</span></div></div>${!c.report.analysis?'<div class="warning">This book was prepared with the older importer. Choose Rebuild import to apply content filtering and improved lesson boundaries. A new course is created and your existing edits are retained.</div>':''}
  <div class="section-row"><h2>${groups.size?'Look at these first':'No extraction problems detected'}</h2><button data-go="course/${c.id}/read" class="primary">Open reader →</button></div>${groups.size?[...groups.values()].map(group=>`<article class="triage-card"><div><span class="pill">${group.lesson.quality.severity==='high'?'HIGH PRIORITY':'CHECK SUGGESTED'} · PDF ${[...new Set(group.lesson.quality.issues.flatMap(i=>i.pages))].join(', ')}</span><h3>${esc(group.lesson.title)}</h3>${group.lesson.quality.issues.map(i=>`<p>${esc(i.message)}</p>`).join('')}<small>${group.lessons.length} affected ${group.lessons.length===1?'lesson':'lessons'} · grouped to avoid repeating the same source problem</small></div><button data-go="course/${c.id}/review/${c.lessons.indexOf(group.lesson)}">Open affected lesson →</button></article>`).join(''):'<div class="empty"><div class="symbol">✓</div><h2>Your course is ready for a first read.</h2><p>Routine text and original questions are kept out of the attention queue. Automatic checks screen extraction quality; they do not guarantee that every textbook layout was understood perfectly.</p></div>'}
  <div class="callout"><span class="symbol">▤</span><div><h3>Learning content comes first.</h3><p>Original wording is retained. Clear page furniture and introductory publication matter are filtered out; uncertain side notes stay available and are flagged. Diagrams appear with reading text.</p><button class="link-button" data-go="course/${c.id}/report">See excluded content and source pages →</button></div></div></div>`;
  bindToolbar();
}
let routeVersion=0;
async function route() {
  const version=++routeVersion;
  try {
    await save(true);
    state.reader?.destroy();state.reader=null;
    const parts=location.hash.replace(/^#\/?/,'').split('/'),page=parts[0]||'library';
    $('#nav-library').classList.toggle('active',page!=='import');$('#nav-import').classList.toggle('active',page==='import');
    $('#breadcrumb').textContent='Workspace / '+(page==='import'?'Prepare a textbook':page==='course'?'Textbook studio':'Library');
    if(page==='library')return await library();
    if(page==='import')return importView();
    if(page==='course'&&/^[a-f0-9]{32}$/.test(parts[1])) {
      if(state.course?.id!==parts[1]){app.innerHTML='<div class="content" role="status">Opening course…</div>';const c=await api('/api/courses/'+parts[1]);if(version!==routeVersion)return;state.course=c;state.dirty=false;}
      const tab=parts[2]||'triage';
      if(tab==='read') {
        const c=state.course;
        app.innerHTML=`<div class="content" style="padding-bottom:0">${toolbar(c,'read')}</div><div id="reader-root"></div>`;bindToolbar();
        state.reader=new AstarReader($('#reader-root'),c,p=>`/courses/${c.id}/${p}`,()=>{location.hash=`course/${c.id}/review/0`;});return;
      }
      if(tab==='report')return report();
      if(tab==='structure')return structureReview();
      if(tab==='triage')return triage();
      return review(Number(parts[3])||0);
    }
    location.hash='library';
  } catch(error) { fail(error); }
}
window.addEventListener('hashchange',route);
window.addEventListener('beforeunload',e=>{if(state.dirty){e.preventDefault();e.returnValue='';}});
async function start() {
  try{state.status=await api('/api/status');state.job=sessionStorage.getItem('astar-job');await route();if(state.job&&!location.hash.includes('import'))pollJob().catch(fail);}
  catch(error){fail(Error('The local ASTAR server is unavailable. Start it with start.bat, then refresh this page.'));}
}
start();
