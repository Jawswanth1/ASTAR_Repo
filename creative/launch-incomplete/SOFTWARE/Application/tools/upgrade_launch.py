from pathlib import Path

root=Path(__file__).resolve().parents[1]
p=root/'static/reader.js'
s=p.read_text(encoding='utf-8')
s=s.replace("this.progress = {completed: [], lastLesson: null};", "this.progress = {completed: [], lastLesson: null, answers: {}};")
s=s.replace("const known = new Set(course.lessons.map(l => l.id));", "this.progress.answers = this.progress.answers && typeof this.progress.answers === 'object' ? this.progress.answers : {};\n      const known = new Set(course.lessons.map(l => l.id));",1)
s=s.replace("this.progress.completed = [...new Set([...this.progress.completed,...data.completed])];", "this.progress.completed = [...new Set([...this.progress.completed,...data.completed])];\n        const questions = new Set(this.course.lessons.flatMap(l=>l.questions.map(q=>q.id)));\n        for (const [id, value] of Object.entries(data.answers || {})) if (questions.has(id) && value && typeof value.value === 'string' && value.value.length <= 10000) this.progress.answers[id] = {value:value.value, attempts:1};")
start=s.index('    questionHTML(q) {')
end=s.index('    lessonHTML() {',start)
s=s[:start]+'''    graded(q) { return q.type === 'mcq' || (q.type === 'numeric' && q.verified === true); }
    isCorrect(q, value) {
      if (q.type === 'mcq') return String(q.answer) === String(value);
      return q.type === 'numeric' && String(value).trim() !== '' && Number.isFinite(Number(value)) && Math.abs(Number(value)-q.answer) <= (q.tolerance || 0);
    }
    feedback(q) {
      const saved=this.progress.answers[q.id];
      if (!saved) return '';
      if (!this.graded(q)) return 'Response saved. This written response is not automatically graded.';
      return (this.isCorrect(q,saved.value) ? 'Correct.' : 'Try again. Read the explanation below.') + (q.explanation ? ' '+q.explanation : '');
    }
    score() {
      const qs=this.course.lessons.flatMap(l=>l.questions).filter(q=>this.graded(q));
      return {total:qs.length, answered:qs.filter(q=>this.progress.answers[q.id]).length, correct:qs.filter(q=>this.progress.answers[q.id]&&this.isCorrect(q,this.progress.answers[q.id].value)).length};
    }
    record(q,value) {
      this.progress.answers[q.id]={value:String(value).slice(0,10000),attempts:(this.progress.answers[q.id]?.attempts||0)+1};
      this.save();
      const box=[...this.root.querySelectorAll('[data-question]')].find(b=>b.dataset.question===q.id);
      box.querySelector('.answer-feedback').textContent=this.feedback(q);
      box.querySelectorAll('[data-answer]').forEach(b=>{b.classList.toggle('correct',this.isCorrect(q,b.dataset.answer));b.setAttribute('aria-pressed',String(b.dataset.answer===String(value)));});
      const score=this.score();
      const el=this.root.querySelector('[data-score]');if(el)el.textContent=`${score.correct} / ${score.total} correct · ${score.answered} answered`;
    }
    questionHTML(q) {
      const label = q.type === 'mcq' ? 'MULTIPLE CHOICE' : q.type === 'numeric' ? 'NUMBER ANSWER' : 'WRITTEN RESPONSE · UNGRADED';
      const saved=this.progress.answers[q.id];
      const response=q.type==='mcq' ? `<div class="question-choices">${q.options.map((o,i)=>`<button data-answer="${i}" aria-pressed="${saved?.value===String(i)}" class="${saved&&this.isCorrect(q,i)?'correct':''}">${String.fromCharCode(65+i)}. ${esc(o)}</button>`).join('')}</div>` : `<label class="response-label" for="response-${esc(q.id)}">Your answer${q.unit?' ('+esc(q.unit)+')':''}</label>${q.type==='numeric'?`<input id="response-${esc(q.id)}" class="response-input" type="text" inputmode="decimal" value="${esc(saved?.value||'')}" maxlength="40">`:`<textarea id="response-${esc(q.id)}" class="response-input" rows="3" maxlength="10000">${esc(saved?.value||'')}</textarea>`}<button data-submit>${q.type==='numeric'&&this.graded(q)?'Check answer':'Save response'}</button>`;
      return `<section class="inline-question" id="question-${esc(q.id)}" data-question="${esc(q.id)}"><span class="label">${label} · ${q.origin === 'textbook' ? 'SOURCE QUESTION' : 'ADDED IN STUDIO'}</span><p>${esc(q.prompt)}</p>${response}<div class="answer-feedback" role="status" aria-live="polite">${esc(this.feedback(q))}</div></section>`;
    }
''' + s[end:]
s=s.replace("<h2 class=\"lesson-subheading\">${esc(b.text)}</h2>","<h2 class=\"lesson-subheading\" id=\"section-${esc(b.id)}\" tabindex=\"-1\">${esc(b.text)}</h2>")
s=s.replace("<figcaption>Textbook diagram · PDF page ${b.page}</figcaption>","<figcaption>${esc(b.caption || 'Textbook diagram')} · PDF page ${b.page}</figcaption>")
s=s.replace("else content += `<p class=\"reading-block\">${esc(b.text)}</p>`;", "else content += b.format==='table' ? `<pre class=\"reading-table\">${esc(b.text)}</pre>` : `<p class=\"reading-block\">${esc(b.text)}</p>`;")
s=s.replace("<span class=\"reader-brand\">✳ ASTAR READER</span>","<span class=\"reader-brand\">ASTAR / LEARN</span>")
s=s.replace("${this.onExit ? '<button data-action=\"exit\">← Studio</button>' : ''}","${this.onExit ? '<button data-action=\"exit\">← Library</button>' : ''}")
s=s.replace("      const completed = new Set(this.progress.completed);", "      const completed = new Set(this.progress.completed);\n      const score = this.score();")
s=s.replace("<div class=\"progress-track\"><div style=\"width:${completed.size/this.course.lessons.length*100}%\"></div></div>","<div class=\"progress-track\" role=\"progressbar\" aria-label=\"Completed lessons\" aria-valuenow=\"${completed.size}\" aria-valuemin=\"0\" aria-valuemax=\"${this.course.lessons.length}\"><div style=\"width:${completed.size/this.course.lessons.length*100}%\"></div></div><p class=\"score-line\" data-score>${score.correct} / ${score.total} correct · ${score.answered} answered</p>")
s=s.replace("      this.root.className = 'reader'", "      this.root.className = 'reader'")
needle="        html += this.lessonHTML();"
s=s.replace(needle,"""        const sections=this.lesson.blocks.filter(b=>b.role==='heading');
        html += `<nav class="section-nav" aria-label="Lesson sections">${sections.map((b,i)=>`<button data-section="${esc(b.id)}"><span>${i+1}</span>${esc(b.text)}</button>`).join('')}<button data-practice>Practice →</button></nav>`;
        if(this.lesson.introduction) html += `<p class="lesson-introduction">${esc(this.lesson.introduction)}</p>`;
        html += `<p class="score-line" data-score>${score.correct} / ${score.total} correct · ${score.answered} answered</p>`;
        html += this.lessonHTML();""")
start=s.index("      this.root.querySelectorAll('[data-question]').forEach(box => {")
end=s.index("      const file = this.root.querySelector('#progress-file');",start)
s=s[:start]+'''      this.root.querySelectorAll('[data-section]').forEach(b=>b.onclick=()=>{this.mode='text';this.render();const target=this.root.querySelector('#section-'+b.dataset.section);target?.scrollIntoView({block:'start'});target?.focus({preventScroll:true});});
      const practice=this.root.querySelector('[data-practice]');if(practice)practice.onclick=()=>{const q=this.root.querySelector('[data-question]');q?.scrollIntoView({block:'center'});q?.querySelector('button,input,textarea')?.focus({preventScroll:true});};
      this.root.querySelectorAll('[data-question]').forEach(box => {
        const q = this.lesson.questions.find(q => q.id === box.dataset.question);
        box.querySelectorAll('[data-answer]').forEach(b => b.onclick = () => this.record(q,b.dataset.answer));
        const submit=box.querySelector('[data-submit]');
        if(submit)submit.onclick=()=>{const value=box.querySelector('.response-input').value;if(!value.trim()){box.querySelector('.answer-feedback').textContent='Enter an answer first.';return;}if(q.type==='numeric'&&!Number.isFinite(Number(value))){box.querySelector('.answer-feedback').textContent='Enter a number using a decimal point if needed.';return;}this.record(q,value);};
      });
''' + s[end:]
s=s.replace("      html += '<p class=\"footer-note\">Stored locally. Keep a copy of your course and export progress for backup.</p>';", "      html += `<p class=\"footer-note\">${esc(this.course.source.attribution || 'Source: '+this.course.source.filename)}<br>Stored in this browser. Export progress for backup. Completion records reading, not mastery. Browser prototype; hardware interface is proposed.</p>`;")
p.write_text(s,encoding='utf-8')

# Preserve old MCQ packages while adding explicitly checked numerical questions.
p=root/'astar_app/storage.py';s=p.read_text(encoding='utf-8')
s=s.replace('import json','import json\nimport math',1)
s=s.replace('("mcq", "notebook")','("mcq", "notebook", "numeric", "text")')
s=s.replace('            if question["type"] == "mcq":','''            if question["type"] == "numeric":
                answer=question.get("answer")
                tolerance=question.get("tolerance",0)
                if not isinstance(answer,(int,float)) or isinstance(answer,bool) or not math.isfinite(answer):
                    raise ValueError("Numeric questions need a finite answer.")
                if not isinstance(tolerance,(int,float)) or isinstance(tolerance,bool) or not math.isfinite(tolerance) or tolerance<0:
                    raise ValueError("Numeric questions need a finite nonnegative tolerance.")
                if question.get("verified") is not True:
                    raise ValueError("Confirm the numerical answer key before saving.")
            if question["type"] == "mcq":''')
p.write_text(s,encoding='utf-8')

p=root/'static/app.js';s=p.read_text(encoding='utf-8')
s=s.replace('<option value="notebook" ${q.type===\'notebook\'?\'selected\':\'\'}>Notebook answer</option>', '<option value="numeric" ${q.type===\'numeric\'?\'selected\':\'\'}>Numerical answer</option><option value="text" ${q.type===\'text\'?\'selected\':\'\'}>Written response (ungraded)</option><option value="notebook" ${q.type===\'notebook\'?\'selected\':\'\'}>Notebook answer</option>')
needle="<button class=\"link-button\" data-remove-q=\"${esc(q.id)}\">Remove question</button>"
s=s.replace(needle, '''${q.type==='numeric'?`<label class="field">Verified numerical answer<input type="number" step="any" data-numeric-answer value="${esc(q.answer??0)}"></label><label class="field">Absolute tolerance<input type="number" min="0" step="any" data-tolerance value="${esc(q.tolerance||0)}"></label><label class="check"><input type="checkbox" data-verified ${q.verified?'checked':''}>I checked this numerical key.</label>`:''}<label class="field">Explanation (shown after answering)<textarea data-prop="explanation">${esc(q.explanation||'')}</textarea></label>''' +needle)
s=s.replace("    $('[data-remove-q]',box).onclick", "    const numberKey=$('[data-numeric-answer]',box);if(numberKey)numberKey.oninput=()=>{q.answer=Number(numberKey.value);unreview(lesson);};\n    const tolerance=$('[data-tolerance]',box);if(tolerance)tolerance.oninput=()=>{q.tolerance=Number(tolerance.value);unreview(lesson);};\n    const verified=$('[data-verified]',box);if(verified)verified.onchange=()=>{q.verified=verified.checked;unreview(lesson);};\n    $('[data-remove-q]',box).onclick")
p.write_text(s,encoding='utf-8')
print('Launch reader and validator updated; original source untouched.')
