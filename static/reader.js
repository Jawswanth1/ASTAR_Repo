/* One dependency-free reader is shared by the studio and exported offline HTML. */
(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  class AstarReader {
    constructor(root, course, asset, onExit) {
      this.root = root; this.course = course; this.asset = asset; this.onExit = onExit;
      this.view = 'chapters'; this.chapter = null; this.lesson = null;
      this.mode = 'text'; this.device = false; this.font = 17; this.selected = 0;
      this.key = 'astar-progress-' + (course.source?.sha256 || course.id);
      this.progress = {completed: [], lastLesson: null}; this.storageWarning = '';
      try {
        const saved = JSON.parse(localStorage.getItem(this.key) || 'null');
        if (saved && Array.isArray(saved.completed)) this.progress = saved;
      } catch { this.storageWarning = 'Progress storage is unavailable. Export progress before closing.'; }
      const known = new Set(course.lessons.map(l => l.id));
      this.progress.completed = this.progress.completed.filter(id => known.has(id));
      this.onKey = e => {
        if (!this.root.isConnected || !this.device || /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
        if (['ArrowUp','ArrowDown','Enter'].includes(e.key)) {
          e.preventDefault(); this.deviceAction(e.key === 'ArrowUp' ? 'up' : e.key === 'ArrowDown' ? 'down' : 'ok');
        }
      };
      document.addEventListener('keydown', this.onKey);
      this.render();
    }
    destroy() { document.removeEventListener('keydown', this.onKey); }
    save() {
      try { localStorage.setItem(this.key, JSON.stringify(this.progress)); }
      catch { this.storageWarning = 'Progress could not be saved. Use Export progress before closing.'; }
    }
    openLesson(lesson) {
      this.lesson = lesson; this.chapter = this.course.chapters.find(c => c.id === lesson.chapterId);
      this.view = 'lesson'; this.progress.lastLesson = lesson.id; this.save(); this.selected = 0;
      this.render(); this.root.scrollIntoView({block:'start', behavior:'instant'});
    }
    downloadProgress() {
      const blob = new Blob([JSON.stringify({schemaVersion:'astar-progress-1', courseKey:this.key, ...this.progress},null,2)], {type:'application/json'});
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'astar-progress.json'; a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    }
    async importProgress(file) {
      try {
        if (file.size > 2e6) throw Error('Progress file is too large.');
        const data = JSON.parse(await file.text());
        const known = new Set(this.course.lessons.map(l => l.id));
        if (data.schemaVersion !== 'astar-progress-1' || data.courseKey !== this.key || !Array.isArray(data.completed) || data.completed.some(id => !known.has(id))) throw Error('This progress file belongs to a different book or course version.');
        this.progress.completed = [...new Set([...this.progress.completed,...data.completed])];
        if (known.has(data.lastLesson)) this.progress.lastLesson = data.lastLesson;
        this.save(); this.render();
      } catch (error) { alert(error.message || 'Could not import progress.'); }
    }
    questionHTML(q) {
      const label = q.type === 'mcq' ? 'MULTIPLE CHOICE' : 'WRITE IN YOUR NOTEBOOK';
      return `<div class="inline-question" data-question="${esc(q.id)}"><span class="label">${label} · ${q.origin === 'textbook' ? 'TEXTBOOK' : 'ADDED IN STUDIO'}</span><p>${esc(q.prompt)}</p>${q.type === 'mcq' ? `<div class="question-choices">${q.options.map((o,i) => `<button data-answer="${i}">${String.fromCharCode(65+i)}. ${esc(o)}</button>`).join('')}</div><div class="answer-feedback" aria-live="polite"></div>` : '<small>Answer on paper, then continue when you are ready.</small>'}</div>`;
    }
    lessonHTML() {
      const lesson = this.lesson;
      let content = '';
      const sessionNote = lesson.session ? `<p class="warning">Study session · ${esc(lesson.session.targetMinutes)} minute target. Read, work through the textbook activities, then review. This is an estimate; take the time you need.</p>` : '';
      if (this.mode === 'source') {
        content = '<p class="tiny">Original pages in black and white. A page may appear in adjoining lessons so every diagram and equation stays available.</p>';
        content += lesson.panels.map(p => `<figure class="source-page"><figcaption>PDF PAGE ${p.page} · ORIGINAL LAYOUT</figcaption><img src="${esc(this.asset(p.image))}" alt="Monochrome source page ${p.page}; diagrams, equations and original questions" loading="lazy"></figure>`).join('');
        content += lesson.questions.filter(q => q.placement === 'middle').map(q => this.questionHTML(q)).join('');
      } else if (lesson.presentation === 'layout') {
        content = '<p class="tiny">Layout preserved automatically so fractions, equations, and tables remain readable.</p>';
        content += lesson.panels.map(p=>`<figure class="source-page focused-page"><figcaption>LEARNING CONTENT · PDF PAGE ${p.page}</figcaption><img src="${esc(this.asset(p.focusImage||p.image))}" alt="Lesson content with original mathematical notation from PDF page ${p.page}" loading="lazy"></figure>`).join('');
        content += lesson.questions.filter(q=>q.placement==='middle').map(q=>this.questionHTML(q)).join('');
      } else {
        const middle = Math.max(0, Math.ceil(lesson.blocks.length/2)-1);
        content = '<div class="reading-content">';
        lesson.blocks.forEach((b,i) => {
          if (b.type === 'figure') content += `<figure class="lesson-figure"><img src="${esc(this.asset(b.image))}" alt="Learning diagram from PDF page ${b.page}" loading="lazy"><figcaption>Textbook diagram · PDF page ${b.page}</figcaption></figure>`;
          else if (b.type === 'source' && !b.text) content += `<figure class="source-page"><figcaption>Scanned learning page ${b.page} · reading text unavailable</figcaption><img src="${esc(this.asset(lesson.panels.find(p=>p.page===b.page)?.image))}" alt="Scanned learning page ${b.page}" loading="lazy"></figure>`;
          else if (b.role === 'heading') content += `<h2 class="lesson-subheading">${esc(b.text)}</h2>`;
          else if (b.type === 'question') content += `<div class="inline-question"><span class="label">TEXTBOOK PROMPT · ANSWER IN YOUR NOTEBOOK</span><p>${esc(b.text)}</p></div>`;
          else content += `<p class="reading-block">${esc(b.text)}</p>`;
          content += lesson.questions.filter(q => q.placement === 'middle' && (q.afterBlockId ? q.afterBlockId === b.id : i === middle)).map(q => this.questionHTML(q)).join('');
        });
        content += '</div><p class="tiny">Original pages remain available for the full source layout.</p>';
      }
      const ending = lesson.questions.filter(q => q.placement === 'end');
      if (ending.length) content += '<h2>End-of-lesson practice</h2>' + ending.map(q => this.questionHTML(q)).join('');
      return sessionNote + content;
    }
    render() {
      this.root.className = 'reader' + (this.device ? ' device' : '');
      this.root.style.setProperty('--reading-size', this.font + 'px');
      const completed = new Set(this.progress.completed);
      const last = this.course.lessons.find(l => l.id === this.progress.lastLesson);
      let html = `<div class="reader-top"><div class="actions">${this.onExit ? '<button data-action="exit">← Studio</button>' : ''}${this.view !== 'chapters' ? '<button data-action="back">← Back</button>' : ''}<span class="reader-brand">✳ ASTAR READER</span></div><button data-action="device">${this.device ? 'Full screen' : '3-button view'}</button></div>`;
      if (this.storageWarning) html += `<div class="warning">${esc(this.storageWarning)}</div>`;
      if (this.view === 'chapters') {
        html += `<div class="reader-heading"><p class="eyebrow">${esc(this.course.subject)} · OFFLINE COURSE</p><h1>${esc(this.course.title)}</h1><p>${completed.size} of ${this.course.lessons.length} lessons complete · Choose a chapter to begin.</p></div><div class="progress-track"><div style="width:${completed.size/this.course.lessons.length*100}%"></div></div>`;
        if (last) html += `<button class="primary" data-action="resume">Continue: ${esc(last.title)}</button>`;
        const attention=this.course.report?.quality?.attention||0;
        if (attention) html += `<p class="tiny">${attention} lessons have extraction issues flagged in the studio. Other lessons passed automatic checks.</p>`;
        html += '<div class="circle-grid">' + this.course.chapters.map((c,i) => {
          const lessons = this.course.lessons.filter(l => l.chapterId === c.id);
          return `<button class="circle-item" data-chapter="${esc(c.id)}" data-device-item><span class="circle">${i+1}</span><span>${esc(c.title)}<small>${lessons.length} lessons · ${lessons.filter(l => completed.has(l.id)).length} complete</small></span></button>`;
        }).join('') + '</div>';
        html += '<div class="reader-controls"><button data-action="export-progress">Export progress</button><label class="package-import tiny">Import progress<input type="file" accept=".json" id="progress-file"></label></div>';
      } else if (this.view === 'lessons') {
        const lessons = this.course.lessons.filter(l => l.chapterId === this.chapter.id);
        html += `<div class="reader-heading"><p class="eyebrow">${esc(this.course.title)}</p><h1>${esc(this.chapter.title)}</h1><p>Select a numbered lesson. Filled circles show completed lessons.</p></div><div class="circle-grid">`;
        html += lessons.map((l,i) => `<button class="circle-item" data-lesson="${esc(l.id)}" data-device-item><span class="circle ${completed.has(l.id) ? 'complete' : ''}">${i+1}</span><span>${esc(l.title)}<small>PDF ${l.pageStart === l.pageEnd ? 'page '+l.pageStart : 'pages '+l.pageStart+'–'+l.pageEnd}</small></span></button>`).join('') + '</div>';
      } else {
        const i = this.course.lessons.indexOf(this.lesson);
        html += `<div class="reader-heading"><p class="eyebrow">${esc(this.chapter.title)} · LESSON ${i+1} / ${this.course.lessons.length}</p><h1>${esc(this.lesson.title)}</h1><p>Read at your own pace. Use your notebook for written answers.</p></div><div class="reader-mode"><button data-mode="source" class="${this.mode === 'source' ? 'active' : ''}">Original pages + diagrams</button><button data-mode="text" class="${this.mode === 'text' ? 'active' : ''}">Reading text</button>${this.mode === 'text' ? '<button data-action="smaller" aria-label="Smaller text">A−</button><button data-action="larger" aria-label="Larger text">A+</button>' : ''}</div>`;
        html += this.lessonHTML();
        html += `<div class="reader-controls"><button data-action="previous" ${i === 0 ? 'disabled' : ''}>← Previous</button><button class="primary" data-action="complete">${completed.has(this.lesson.id) ? '✓ Completed · continue' : 'Mark complete & continue'}</button><button data-action="next" ${i === this.course.lessons.length-1 ? 'disabled' : ''}>Next →</button></div>`;
      }
      if (this.device) html += `<div class="device-buttons"><button data-device="up" aria-label="Up">▲</button><button data-device="down" aria-label="Down">▼</button><button data-device="ok">OK</button></div><p class="device-caption">Arrow keys + Enter also work. In a lesson: ▲ ▼ scroll; OK continues.</p>`;
      html += '<p class="footer-note">Stored locally. Keep a copy of your course and export progress for backup.</p>';
      this.root.innerHTML = html;
      this.root.querySelectorAll('[data-chapter]').forEach(b => b.onclick = () => { this.chapter = this.course.chapters.find(c => c.id === b.dataset.chapter); this.view = 'lessons'; this.selected = 0; this.render(); });
      this.root.querySelectorAll('[data-lesson]').forEach(b => b.onclick = () => this.openLesson(this.course.lessons.find(l => l.id === b.dataset.lesson)));
      this.root.querySelectorAll('[data-action]').forEach(b => b.onclick = () => this.action(b.dataset.action));
      this.root.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => { this.mode = b.dataset.mode; this.render(); });
      this.root.querySelectorAll('[data-device]').forEach(b => b.onclick = () => this.deviceAction(b.dataset.device));
      this.root.querySelectorAll('[data-question]').forEach(box => {
        const q = this.lesson.questions.find(q => q.id === box.dataset.question);
        box.querySelectorAll('[data-answer]').forEach(b => b.onclick = () => {
          const right = Number(b.dataset.answer) === q.answer;
          box.querySelectorAll('[data-answer]').forEach(x => { x.classList.remove('correct'); if (Number(x.dataset.answer) === q.answer) x.classList.add('correct'); });
          box.querySelector('.answer-feedback').textContent = right ? 'Correct.' : `Review the explanation in the lesson. The answer is ${String.fromCharCode(65+q.answer)}.`;
        });
      });
      const file = this.root.querySelector('#progress-file');
      if (file) file.onchange = () => file.files[0] && this.importProgress(file.files[0]);
      this.updateSelection();
    }
    updateSelection() {
      const items = [...this.root.querySelectorAll('[data-device-item]')];
      items.forEach((b,i) => b.classList.toggle('selected', this.device && i === this.selected));
    }
    deviceAction(action) {
      if (this.view === 'lesson') {
        if (action === 'ok') this.action('complete');
        else window.scrollBy({top:action === 'up' ? -240 : 240, behavior:'smooth'});
      } else {
        const items = [...this.root.querySelectorAll('[data-device-item]')];
        if (!items.length) return;
        if (action === 'ok') items[this.selected % items.length].click();
        else { this.selected = (this.selected + (action === 'up' ? -1 : 1) + items.length) % items.length; this.updateSelection(); items[this.selected].scrollIntoView({block:'nearest'}); }
      }
    }
    action(action) {
      if (action === 'exit') { this.destroy(); return this.onExit(); }
      if (action === 'device') this.device = !this.device;
      if (action === 'back') { this.view = this.view === 'lesson' ? 'lessons' : 'chapters'; this.selected = 0; }
      if (action === 'resume') return this.openLesson(this.course.lessons.find(l => l.id === this.progress.lastLesson));
      if (action === 'export-progress') return this.downloadProgress();
      if (action === 'larger') this.font = Math.min(28,this.font+2);
      if (action === 'smaller') this.font = Math.max(13,this.font-2);
      if (['previous','next','complete'].includes(action)) {
        const i = this.course.lessons.indexOf(this.lesson);
        if (action === 'complete') { this.progress.completed = [...new Set([...this.progress.completed,this.lesson.id])]; this.save(); }
        const next = this.course.lessons[i+(action === 'previous' ? -1 : 1)];
        if (next) return this.openLesson(next);
        this.view = 'lessons'; this.selected = 0;
      }
      this.render();
    }
  }
  window.AstarReader = AstarReader;
})();
