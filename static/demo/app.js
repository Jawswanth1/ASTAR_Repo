'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, x => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
  let course = null, progress = {completed:[],attempts:{}}, queue = [], cursor = 0;
  let currentLesson = null, route = null, menu = null, menuSelected = 0, displayRevision = 0, menuBlob = null;
  let importBusy = false, explorer = null;
  const base = () => `/demos/${course.id}/`;
  const qById = id => course.questions.find(q => q.id === id);
  const tell = (text, error=false) => { $('notice').textContent = text; $('notice').classList.toggle('error',error); };
  const api = async (url, options) => {
    const res = await fetch(url, options);
    if (!res.ok) { let message; try { message = (await res.json()).error; } catch {} throw new Error(message || `Request failed (${res.status}).`); }
    return res;
  };
  function saveProgress() {
    if (!course) return;
    try { localStorage.setItem(`astar-demo:${course.source.sha256}`, JSON.stringify(progress)); }
    catch { tell('Progress could not be saved in this browser. Use a browser profile that permits local storage.',true); }
    renderProgress();
  }
  function renderProgress() {
    if (!course) return;
    $('progress-value').textContent = `${progress.completed.length} / ${course.lessons.length}`;
    $('progress-fill').style.width = `${progress.completed.length / course.lessons.length * 100}%`;
    document.querySelectorAll('.lesson-card').forEach(el => el.classList.toggle('done', progress.completed.includes(Number(el.dataset.lesson))));
    $('resume').disabled = false;
  }
  function flash() {
    if (!$('refresh').checked || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    $('device').classList.remove('flash');
    void $('device').offsetWidth;
    $('device').classList.add('flash');
  }
  function resizeDevice() {
    const area = $('stage'), holder = $('device-holder');
    const pixels = $('simulator').classList.contains('pixel-mode');
    const width = pixels ? 800 : 586, height = pixels ? 600 : 425;
    const scale = Math.min(1, Math.max(.2,(area.clientWidth - 38)/width), (area.clientHeight-30)/height);
    holder.style.width = `${width*scale}px`; holder.style.height = `${height*scale}px`;
    $('device').style.transform = `scale(${scale})`;
  }
  new ResizeObserver(resizeDevice).observe($('stage'));
  function setTab(tab) {
    document.querySelectorAll('.panel-view').forEach(el => { el.hidden = el.id !== tab; });
    document.querySelectorAll('[data-tab]').forEach(el => el.classList.toggle('active',el.dataset.tab === tab));
    if (tab === 'simulator') requestAnimationFrame(resizeDevice);
    if (tab === 'questions') renderQuestions();
    if (tab === 'source') renderSource();
    if (tab === 'audit') renderAudit();
  }
  document.querySelectorAll('[data-tab]').forEach(el => el.addEventListener('click',() => setTab(el.dataset.tab)));
  async function showMenu(title,entries,selected=0,kind='home') {
    explorer=null;
    menu = {title,entries,kind}; menuSelected = Math.min(selected,entries.length-1);
    await paintMenu();
  }
  async function paintMenu() {
    const revision = ++displayRevision;
    try {
      const response = await api('/api/demo-menu',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        title:menu.title,entries:menu.entries.map(e=>e.label),selected:menuSelected,subtitle:course ? `${course.source.publisher.split(' (')[0]} / Chapter 1` : 'ASTAR / Chapter One Lab'
      })});
      const blob = await response.blob();
      if (revision !== displayRevision) return;
      if (menuBlob) URL.revokeObjectURL(menuBlob);
      menuBlob = URL.createObjectURL(blob);
      $('display').src = menuBlob;
      $('display').alt = `${menu.title}. ${menu.entries.map((e,i)=>(i===menuSelected?'Selected: ':'')+e.label).join('. ')}`;
      flash();
      $('screen-title').textContent = menu.title;
      $('screen-detail').textContent = `${menu.entries[menuSelected].label}. Use the physical UP, DOWN and SELECT buttons, or the arrow keys and Enter.`;
      $('screen-origin').textContent='ASTAR SYSTEM'; $('screen-ref').textContent=''; $('context-extra').textContent='';
      $('download-frame').hidden=true; $('download-bin').hidden=true;
    } catch(error) { tell(error.message,true); }
  }
  function home(selected=0) {
    if (!course) return showMenu('Welcome to ASTAR',[
      {label:'Load SCERT demonstration',action:loadReference},
      {label:'Import a textbook PDF',action:()=> $('import-dialog').showModal()}
    ]);
    return showMenu('Chapter 1 / Lessons',[
      ...course.lessons.map(l=>({label:`${l.id}. ${l.short}`,action:()=>startCore(l.id)})),
      {label:`Chapter assessment (${course.assessment.length})`,action:assessmentMenu},
      {label:'Original chapter archive',action:sourceMenu}
    ],selected);
  }
  function openQueue(ids, info) {
    if (!ids.length) return tell('No screens were available for this route.',true);
    queue=ids; cursor=Math.max(0,Math.min(info.cursor || 0,ids.length-1));
    route=info; currentLesson=info.lesson ?? null; menu=null;explorer=null;
    setTab('simulator'); paintScreen();
  }
  function paintScreen() {
    if (!course || !queue.length) return;
    ++displayRevision; menu=null;
    const sid=queue[cursor], s=course.screens[sid], q=s.questionId ? qById(s.questionId) : null;
    $('display').src=base()+`frames/${sid}.png`; flash();
    $('display').alt = `${s.title}. Screen ${cursor+1} of ${queue.length}. ${s.text || (q ? q.text : 'Original textbook source image; use Source evidence for its transcription.')}`;
    $('screen-title').textContent=s.title;
    $('screen-detail').textContent=`Screen ${cursor+1} of ${queue.length}${currentLesson ? ` · Lesson ${currentLesson}` : ''}. ${s.tile ? `Source tile row ${s.tile.row}/${s.tile.rows}, column ${s.tile.column}/${s.tile.columns}. Read left to right, then down. Overlap: 28 pixels.` : '18 px main text, paginated to the fixed display.'}`;
    $('screen-origin').textContent=s.origin;
    const ref=s.source;
    $('screen-ref').textContent=ref ? (ref.pdfPage ? `Printed p.${ref.printedPage ?? 'unverified'} / PDF p.${ref.pdfPage}` : `Source printed pp.${ref.printedPages}`) : 'ASTAR learning instructions; not quoted textbook content.';
    if (ref?.pdfPage) {
      const a=document.createElement('a'); a.href='#'; a.textContent=' Compare original page ↗';
      a.addEventListener('click',e=>{e.preventDefault();selectSource(ref.pdfPage);});$('screen-ref').append(a);
    }
    $('context-extra').innerHTML=q ? `<p class="small-note"><b>${esc(q.label)}</b><br>${progress.attempts[q.id] ? '✓ Attempt recorded in this browser.' : 'Write your response in your notebook. SELECT to record an attempt.'}<br>Teacher review; no automatic grading.</p>` : '';
    for (const [id,ext] of [['download-frame','png'],['download-bin','bin']]) {
      $(id).hidden=false; $(id).href=base()+`frames/${sid}.${ext}`; $(id).download=`astar-${sid}.${ext}`;
    }
    progress.last={...route,cursor}; saveProgress();
  }
  const startCore=id=>{const l=course.lessons.find(l=>l.id===id);openQueue(l.core,{type:'core',lesson:id});};
  function startQuestion(id) { const q=qById(id);openQueue(q.screens,{type:'question',question:id,lesson:q.lesson}); }
  const qMenuLabel=q=>q.exercise ? `Ex ${q.exercise} / Q${q.number}${progress.attempts[q.id]?' [done]':''}` : `Prompt ${course.questions.indexOf(q)+1} / p.${q.printedPage ?? q.pdfPage}`;
  function practiceMenu(id) {
    const l=course.lessons.find(l=>l.id===id);
    return showMenu(`Lesson ${id} / Practice`,[
      ...l.practice.map(id=>{const q=qById(id);return {label:qMenuLabel(q),action:()=>startQuestion(id)};}),
      {label:'Back to lesson menu',action:()=>home(id-1)}
    ],0,'practice');
  }
  function assessmentMenu() {
    return showMenu('Chapter assessment',[
      ...course.assessment.map(id=>{const q=qById(id);return {label:qMenuLabel(q),action:()=>startQuestion(id)};}),
      {label:'Back to lessons',action:()=>home()}
    ],0,'assessment');
  }
  function sourceMenu() {
    return showMenu('Original chapter archive',[
      ...course.sourcePages.map(p=>({label:`Printed p.${p.printedPage ?? '?'} / PDF p.${p.pdfPage}`,action:()=>openQueue(p.screens,{type:'source',page:p.pdfPage})})),
      {label:'Back to lessons',action:()=>home()}
    ],0,'source');
  }
  function actionsMenu() {
    const s=course.screens[queue[cursor]], entries=[{label:'Continue reading',action:paintScreen}];
    if (s.questionId) entries.push({label:'Record notebook attempt',action:()=>{progress.attempts[s.questionId]=true;saveProgress();paintScreen();}});
    if (route.type==='core' && cursor===queue.length-1) entries.push({label:'Mark lesson complete',action:()=>{
      if (!progress.completed.includes(currentLesson))progress.completed.push(currentLesson);
      saveProgress();home(Math.min(currentLesson,course.lessons.length-1));
    }});
    if (currentLesson) {
      if(currentLesson===4 && course.curated)entries.push({label:'Explore the number line',action:()=>openExplorer()});
      entries.push({label:'Original lesson questions',action:()=>practiceMenu(currentLesson)});
      entries.push({label:'Original lesson archive',action:()=>openQueue(course.lessons.find(l=>l.id===currentLesson).sourceScreens,{type:'lesson-source',lesson:currentLesson})});
    }
    entries.push({label:'Return to lessons',action:()=>home(currentLesson ? currentLesson-1 : 0)});
    return showMenu('Learning actions',entries,0,'actions');
  }
  function key(action) {
    if ($('import-dialog').open || importBusy)return;
    if(explorer!==null){
      if(action==='select'){explorer=null;return actionsMenu();}
      explorer=Math.max(-8,Math.min(8,explorer+(action==='up'?-1:1)));
      return paintExplorer();
    }
    if (menu) {
      if(action==='select') return Promise.resolve(menu.entries[menuSelected].action()).catch(e=>tell(e.message,true));
      menuSelected=(menuSelected+(action==='down'?1:-1)+menu.entries.length)%menu.entries.length;
      return paintMenu();
    }
    if (!course || !queue.length)return;
    if (action==='select') return actionsMenu();
    if (action==='up') {if(cursor>0){cursor--;paintScreen();}else actionsMenu();}
    else if(cursor<queue.length-1){cursor++;paintScreen();}else actionsMenu();
  }
  function openExplorer(){menu=null;explorer=0;return paintExplorer();}
  function paintExplorer(){
    ++displayRevision;
    $('display').src=`/api/demo-numberline?n=${explorer}`;flash();
    $('display').alt=`ASTAR number line investigation. Position ${explorer}/4 equals ${explorer/4}. UP moves left, DOWN moves right, SELECT returns.`;
    $('screen-title').textContent='Explore the number line';
    $('screen-detail').textContent='Move the marker in quarter steps using UP and DOWN. SELECT returns to the lesson actions.';
    $('screen-origin').textContent='ASTAR-GENERATED INVESTIGATION';
    $('screen-ref').textContent='Additional interactive explanation based on section 1.4, printed pp.23–25.';
    $('context-extra').textContent='';$('download-frame').hidden=true;$('download-bin').hidden=true;
  }
  document.querySelectorAll('[data-key]').forEach(el=>el.addEventListener('click',()=>key(el.dataset.key)));
  document.addEventListener('keydown',e=>{
    if (['INPUT','TEXTAREA','SELECT','BUTTON','A'].includes(document.activeElement.tagName) || $('import-dialog').open)return;
    const action={ArrowUp:'up',ArrowDown:'down',Enter:'select',' ':'select'}[e.key];
    if(action && !$('simulator').hidden){e.preventDefault();key(action);}
  });
  for (const [id,pixel] of [['physical-view',false],['pixel-view',true]]) $(id).addEventListener('click',()=>{
    $('simulator').classList.toggle('pixel-mode',pixel);$('pixel-controls').hidden=!pixel;
    $('physical-view').classList.toggle('selected',!pixel);$('pixel-view').classList.toggle('selected',pixel);
    $('physical-view').setAttribute('aria-pressed',String(!pixel));$('pixel-view').setAttribute('aria-pressed',String(pixel));
    requestAnimationFrame(resizeDevice);
  });
  $('device-home').addEventListener('click',()=>home());
  $('resume').addEventListener('click',()=>{
    const p=progress.last;
    if (!p)return startCore(course.lessons.find(l=>!progress.completed.includes(l.id))?.id || 1);
    if(p.type==='question')return openQueue(qById(p.question).screens,p);
    if(p.type==='source')return openQueue(course.sourcePages.find(s=>s.pdfPage===p.page).screens,p);
    const l=course.lessons.find(l=>l.id===p.lesson);
    if(l)openQueue(p.type==='lesson-source'?l.sourceScreens:l.core,p);else startCore(1);
  });
  function renderLessons() {
    $('lessons').innerHTML=course.lessons.map(l=>`<article class="lesson-card" data-lesson="${l.id}"><div class="lesson-top"><span class="lesson-number">${l.id}</span><span>~${l.minutes} MIN</span></div><h3>${esc(l.title)}</h3><p>Sections ${esc(l.sections.join(', '))}<br>${l.core.length} core screens · ${l.practice.length} prompt groups</p><button data-start="${l.id}">Start lesson <span>→</span></button><button data-practice="${l.id}">Original questions <span>↗</span></button></article>`).join('');
    document.querySelectorAll('[data-start]').forEach(el=>el.addEventListener('click',()=>startCore(Number(el.dataset.start))));
    document.querySelectorAll('[data-practice]').forEach(el=>el.addEventListener('click',()=>practiceMenu(Number(el.dataset.practice))));
    $('lesson-filter').innerHTML='<option value="">All lessons</option>'+course.lessons.map(l=>`<option value="${l.id}">${l.id}. ${esc(l.title)}</option>`).join('');
    $('journey-time').textContent=`${course.lessons.length} lessons · ~30 minutes per core route`;
    document.querySelector('.journey-heading h2').textContent=course.lessons.length===5?'Five concepts. One connected story.':`${course.lessons.length} concept-based lessons.`;
  }
  function renderQuestions() {
    if(!course){$('question-summary').textContent='Load a textbook to see its question map.';return;}
    const query=$('question-search').value.toLowerCase(),lesson=$('lesson-filter').value,type=$('type-filter').value;
    const list=course.questions.filter(q=>(!lesson||q.lesson===Number(lesson))&&(!type||(type==='exercise')===Boolean(q.exercise))&&[q.label,q.text,...q.concepts].join(' ').toLowerCase().includes(query));
    $('question-summary').textContent=`${list.length} of ${course.questions.length} prompt groups · ${course.report.counts.exerciseQuestions} numbered exercise questions · subparts retained within parents. Native search text may misorder mathematical notation; compare the original.`;
    $('question-list').innerHTML=list.map(q=>`<article class="question-card"><div><h3>${esc(q.label)} ${progress.attempts[q.id]?'✓':''}</h3><span class="tag">${esc(q.type)}</span><pre>${esc(q.text || 'No reliable native transcription. Read the original source region.')}</pre><details><summary>Concepts, prerequisites & source</summary><p>${esc(q.concepts.join(' · '))}<br>Subsections: ${esc(q.subsection.join(', '))}<br>Prerequisite lessons: ${q.prerequisites.length?q.prerequisites.join(', '):'None assigned'}<br>${esc(q.rationale)} ${esc(q.note || '')}<br>${esc(q.transcription)}</p></details></div><div class="assignment"><strong>Lesson ${q.lesson}<br>${esc(course.lessons[q.lesson-1].short)}</strong><p>Printed p.${q.printedPage ?? '?'} / PDF ${q.pdfPage}<br>${esc(q.placement)}</p><button data-question="${q.id}">Read on device →</button><br><button data-source="${q.pdfPage}">Compare source ↗</button></div></article>`).join('') || '<p>No matching questions.</p>';
    document.querySelectorAll('[data-question]').forEach(el=>el.addEventListener('click',()=>startQuestion(el.dataset.question)));
    document.querySelectorAll('[data-source]').forEach(el=>el.addEventListener('click',()=>selectSource(Number(el.dataset.source))));
  }
  ['question-search','lesson-filter','type-filter'].forEach(id=>$(id).addEventListener('input',renderQuestions));
  function selectSource(number){$('source-page').value=String(number);setTab('source');}
  function renderSource() {
    if(!course)return;
    const p=course.sourcePages.find(p=>p.pdfPage===Number($('source-page').value)) || course.sourcePages[0];
    if(!p)return;
    $('source-page').value=p.pdfPage;$('source-image').src=base()+p.evidence;
    $('source-image').alt=`Unmodified original textbook page: printed ${p.printedPage ?? 'unverified'}, PDF ${p.pdfPage}`;
    $('source-text').textContent=p.nativeText;
  }
  $('source-page').addEventListener('change',renderSource);
  $('source-device').addEventListener('click',()=>{
    if(!course)return;const p=course.sourcePages.find(p=>p.pdfPage===Number($('source-page').value));openQueue(p.screens,{type:'source',page:p.pdfPage});
  });
  function renderAudit() {
    if(!course){$('audit').innerHTML='<h2>Load a textbook to see its extraction report.</h2>';return;}
    const r=course.report,s=course.source;
    $('audit').innerHTML=`<div class="section-heading"><div><div class="eyebrow">EVIDENCE, NOT ASSUMPTIONS</div><h2>What was preserved. What needs review.</h2><p>${course.curated?'Curated SCERT demonstration. This source is not NCERT.':'Provisional automated import. Teacher review is required.'}</p></div></div><div class="audit-grid"><div class="audit-stat"><strong>${r.counts.sourcePages}</strong><span>Chapter 1 source pages</span></div><div class="audit-stat"><strong>${r.counts.questions}</strong><span>Question / prompt groups</span></div><div class="audit-stat"><strong>${r.counts.screens}</strong><span>Real 400 × 300 framebuffers</span></div></div>
    <div class="audit-block"><h3>Source identity & exact scope</h3><p>${esc(s.book)} · ${esc(s.publisher)} · ${esc(s.edition)}<br>Subject: ${esc(s.subject)} · Class: ${esc(s.className)}<br>Physical PDF pages ${s.first}–${s.last} (inclusive). ${esc(s.boundaryNote)}<br>${esc(r.excluded)}<br>SHA-256: <code>${esc(s.sha256)}</code></p></div>
    <div class="audit-block"><h3>Question alignment</h3><p>${esc(r.questionCatalogue)} ${r.counts.exerciseQuestions} numbered exercise questions are retained. Each is assigned once to a primary lesson; the catalogue and assessment reference the same source screens. Checkpoints are excluded from the remaining assessment. In the SCERT map, Exercise 1.3 Q3–Q10 return to arithmetic in Lesson 1 despite appearing in the decimal exercise. Q5 additionally needs prior knowledge of simple equations.</p></div>
    <div class="audit-block"><h3>The 30-minute route</h3><table><thead><tr><th>Lesson</th><th>Introduction</th><th>Concepts</th><th>Example / activity</th><th>Checkpoint</th><th>Recap</th></tr></thead><tbody>${course.lessons.map(l=>`<tr><td>${l.id}. ${esc(l.short)}</td>${l.timing.map(t=>`<td>${t.minutes} min</td>`).join('')}</tr>`).join('')}</tbody></table><p>${esc(r.timings)} Timing is an instructional estimate, not a measured learner completion time.</p></div>
    <div class="audit-block"><h3>Display validation</h3><p>400 × 300 pixels · black and white only · mode-1 PNG · 15,000-byte packed framebuffer per screen. Main generated text is 18 px; interface metadata is 12–15 px. Text wraps into additional screens; a layout exception aborts the build rather than truncating content. Original source is rendered at 1.7× PDF scale, then tiled with 28 px overlap and no downscaling. Small source subscripts keep their original relative size.</p></div>
    <div class="audit-block"><h3>Extraction failures: ${r.extractionFailures.length}</h3>${r.extractionFailures.length?'<ul>'+r.extractionFailures.map(w=>`<li>PDF ${w.pdfPage}: ${esc(w.reason)}</li>`).join('')+'</ul>':'<p>No failed or text-empty chapter pages were detected. This check does not establish perfect mathematical transcription.</p>'}<p>${esc(r.review)}</p><p>Native transcription warnings: ${r.transcriptionWarnings.length}. ${r.transcriptionWarnings.map(w=>`PDF ${w.pdfPage}: ${esc(w.reason)}`).join(' ')}</p></div>
    <div class="audit-block"><h3>Original content & ASTAR additions</h3><p>Original wording, equations, tables, diagrams, activities and question options remain in the source-region screens, full source archive and unmodified PDF. Introductions, conceptual explanations, worked guides, instructions and recaps carry the label “ASTAR”. They are educational additions and are not presented as verbatim textbook quotations.</p><p>${esc(r.sourceRender)}</p></div>
    <div class="audit-block"><h3>Practical limits</h3><p>This is a browser simulator and data package, not deployed hardware firmware. Screen size in inches depends on monitor calibration; the enclosure-to-display ratio is proportional. Notebook answers record attempts without grading. Arbitrary new PDFs use provisional heading grouping and lexical question alignment; they do not inherit this book’s curated map. Scanned pages are flagged and preserved visually; this workflow does not infer missing OCR or answer keys.</p></div>`;
  }
  async function loadCourse(id) {
    course=await (await api(`/api/demos/${id}`)).json();
    let valid=null;
    try{valid=JSON.parse(localStorage.getItem(`astar-demo:${course.source.sha256}`)||'null');}catch{tell('Stored progress could not be read; starting a fresh session.',true);}
    progress=valid && Array.isArray(valid.completed) && valid.attempts && typeof valid.attempts==='object' ? valid : {completed:[],attempts:{}};
    progress.completed=[...new Set(progress.completed.filter(id=>course.lessons.some(l=>l.id===id)))];
    const s=course.source;
    $('book-bar').innerHTML=`<div class="book-icon">1</div><div><strong>${esc(s.title)} <span class="muted">/ ${esc(s.book)}</span></strong><p>${esc(s.publisher)} · ${esc(s.edition)} · PDF ${s.first}–${s.last} · ${course.curated?'Labelled SCERT demonstration; not NCERT':'Provisional import; review required'}</p></div><span class="tag">CHAPTER 1 ONLY</span>`;
    $('q-count').textContent=course.questions.length;$('export').disabled=false;
    $('original-pdf').href=base()+'source.pdf';
    $('source-page').innerHTML=course.sourcePages.map(p=>`<option value="${p.pdfPage}">Printed ${p.printedPage ?? '?'} / PDF ${p.pdfPage}</option>`).join('');
    renderLessons();renderProgress();renderQuestions();renderSource();renderAudit();
    await home();
    tell(course.curated?'SCERT reference loaded. Chapter 1 only. Original mathematical notation is preserved in source tiles.':'Provisional import ready. Review the lesson boundaries, question groups and source extraction before teaching.',!course.curated);
  }
  async function importResult(result) {
    if(result.demoId)return loadCourse(result.demoId);
    const deadline=Date.now()+15*60*1000;
    while(Date.now()<deadline) {
      const job=await (await api(`/api/demo-jobs/${result.jobId}`)).json();
      tell(`${job.message}${job.total>1?` (${job.done}/${job.total} pages)`:''}`);
      if(job.status==='complete')return loadCourse(job.demoId);
      if(job.status==='error')throw new Error(job.message);
      await new Promise(resolve=>setTimeout(resolve,900));
    }
    throw new Error('Import is still running. Reload the lab to find the completed demonstration.');
  }
  async function loadReference() {
    if(importBusy)return;importBusy=true;$('reference').disabled=true;
    try {tell('Preparing the curated SCERT chapter. Rendering original source tiles and real framebuffers…');await importResult(await (await api('/api/demo-scert',{method:'POST'})).json());}
    catch(e){tell(e.message,true);}finally{importBusy=false;$('reference').disabled=false;}
  }
  $('reference').addEventListener('click',loadReference);
  $('upload-open').addEventListener('click',()=> $('import-dialog').showModal());
  $('import-cancel').addEventListener('click',()=> $('import-dialog').close());
  $('import-form').addEventListener('submit',async e=>{
    e.preventDefault();if(importBusy)return;
    const form=new FormData(e.target),file=form.get('file'),start=form.get('start'),end=form.get('end');
    if(Boolean(start)!==Boolean(end))return tell('Enter both the first and last physical PDF page, or leave both on Auto.',true);
    if(file.size>100*1024*1024)return tell('Choose a PDF under 100 MB.',true);
    const params=new URLSearchParams({filename:file.name,title:form.get('title')});
    if(start){params.set('start',start);params.set('end',end);}
    $('import-dialog').close();importBusy=true;$('reference').disabled=true;
    try{tell('Uploading to the local ASTAR server…');await importResult(await(await api(`/api/demo-import?${params}`,{method:'POST',body:file,headers:{'Content-Type':'application/pdf'}})).json());setTab('simulator');}
    catch(e){tell(e.message,true);}finally{importBusy=false;$('reference').disabled=false;}
  });
  $('export').addEventListener('click',()=>{if(course)location.href=`/api/demos/${course.id}/export`;});
  $('catalogue-export').addEventListener('click',()=>{
    if(!course)return;
    const blob=URL.createObjectURL(new Blob([JSON.stringify({source:course.source,questions:course.questions},null,2)],{type:'application/json'}));
    const a=document.createElement('a');a.href=blob;a.download='astar-question-catalogue.json';a.click();setTimeout(()=>URL.revokeObjectURL(blob),1000);
  });
  (async()=>{try{const list=await(await api('/api/demos')).json();if(list.length)await loadCourse(list[0].id);else await home();}catch(e){tell(e.message,true);await home();}})();
})();
