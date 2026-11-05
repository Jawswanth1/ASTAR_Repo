from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
def edit(name, old, new):
    p = ROOT/name
    s = p.read_text(encoding='utf-8')
    assert old in s, (name, old[:80])
    p.write_text(s.replace(old,new),encoding='utf-8')

edit('astar_app/converter.py', 'from .analysis import', 'from .sessions import session_settings, plan_sessions\nfrom .analysis import')
edit('astar_app/converter.py', '    output, source = Path(output), Path(source)', "    timing = session_settings(options)\n    output, source = Path(output), Path(source)")
edit('astar_app/converter.py', '    # At least ~45 words', "    if timing['planningMode'] == 'sessions':\n        word_limit = (timing['sessionMinutes'] - timing['practiceMinutes']) * timing['readingWpm']\n        minimum = 1\n    # At least ~45 words")
edit('astar_app/converter.py', '    # Use cropped source layout', "    if timing['planningMode'] == 'sessions':\n        lessons = plan_sessions(lessons, timing)\n    # Use cropped source layout")
edit('astar_app/converter.py', '    warnings = []\n    if len(lessons)', "    warnings = []\n    if timing['planningMode'] == 'sessions':\n        warnings.append('Session duration is a planning estimate, not a measured learning time. Reading pace, equations, diagrams and textbook exercises need review. Short unit endings are not padded.')\n    if timing['expectedUnits'] and timing['expectedUnits'] != len(chapters):\n        warnings.append(f\"UNIT COUNT MISMATCH: expected {timing['expectedUnits']}, found {len(chapters)}. Check the unit boundaries and re-import with a manual chapter plan.\")\n    if len(lessons)")
edit('astar_app/converter.py', '"settings": {"wordsPerLesson": word_limit, "minLessons": minimum}', '"settings": {**timing, "wordsPerLesson": word_limit, "minLessons": minimum, "chapterPlan": options.get("chapterPlan", ""), "imageMode": options.get("imageMode", "dither"), "ocr": options.get("ocr", True)}')
edit('astar_app/server.py', 'from .converter import', 'from .sessions import session_settings\nfrom .converter import')
edit('astar_app/server.py', '                word_limit, minimum = int(query.get', '                timing = session_settings(query)\n                query.update(timing)\n                word_limit, minimum = int(query.get')
# Session mode uses its own validated reading budget; legacy word mode remains supported.
edit('astar_app/server.py', '                if not 80 <= word_limit <= 1200 or not 1 <= minimum <= 2000:', '                if timing["planningMode"] == "words" and (not 80 <= word_limit <= 1200 or not 1 <= minimum <= 2000):')
p=ROOT/'static/app.js'; s=p.read_text(encoding='utf-8')
old=s[s.index('    <div class="field-row"><label class="field">Words per lesson'):s.index('    <label class="field">Monochrome images')]
new='''    <label class="field">Organise lessons<select name="planningMode" id="planning-mode"><option value="sessions">30-minute study sessions within each unit</option><option value="words">Custom word-based lessons</option></select></label>
    <div id="session-settings"><div class="field-row"><label class="field">Session minutes<input name="sessionMinutes" type="number" value="30" min="10" max="90" required></label><label class="field">Minutes for textbook practice and review<input name="practiceMinutes" type="number" value="15" min="0" max="89" required></label></div><div class="field-row"><label class="field">Reading pace (words/minute)<input name="readingWpm" type="number" value="120" min="40" max="300" required></label><label class="field">Number of units in the textbook (optional)<input name="expectedUnits" type="number" value="0" min="0" max="2000"><small>0 = detect automatically. A mismatch is flagged; no units are invented.</small></label></div><p class="tiny">A 30-minute target defaults to 15 minutes reading and 15 minutes for the textbook's activities. Timing is an estimate. Short units remain short; exercises stay in their original place.</p></div>
    <div id="word-settings" class="hidden"><div class="field-row"><label class="field">Words per lesson<input name="wordsPerLesson" type="number" value="220" min="80" max="1200" required></label><label class="field">Target minimum lessons<input name="minLessons" type="number" value="1" min="1" max="2000" required></label></div></div>
'''
s=s.replace(old,new)
s=s.replace("  $('#pdf-file').onchange", "  $('#planning-mode').onchange=e=>{const sessions=e.target.value==='sessions';$('#session-settings').classList.toggle('hidden',!sessions);$('#word-settings').classList.toggle('hidden',sessions);};\n  $('#pdf-file').onchange")
s=s.replace("    const values=new FormData(form)", "    if(Number(form.elements.practiceMinutes.value)>=Number(form.elements.sessionMinutes.value))return fail(Error('Practice time must be shorter than the whole session.'));\n    const values=new FormData(form)")
s=s.replace('Set chapter boundaries manually (optional)','Set unit / chapter boundaries manually (optional)')
s=s.replace('Only likely problems need attention','Check the source when uncertain')
s=s.replace('Original prompts stay in context. Add checked MCQs between text blocks and written questions at the end.','Original textbook questions stay word for word, in source order. Answers are not invented. Optional author-added practice is labelled separately.')
s=s.replace("${toolbar(c,'triage')}","${toolbar(c,'triage')}${c.report.warnings.map(w=>`<div class=\"warning\">${esc(w)}</div>`).join('')}")
p.write_text(s,encoding='utf-8')
edit('static/reader.js', "      let content = '';", "      let content = '';\n      const sessionNote = lesson.session ? `<p class=\"warning\">Study session · ${esc(lesson.session.targetMinutes)} minute target. Read, work through the textbook activities, then review. This is an estimate; take the time you need.</p>` : '';" )
edit('static/reader.js', '      return content;', '      return sessionNote + content;')
# Neutralise all existing CSS colours, including exported readers, while preserving contrast.
for name in ['style.css','quality.css','brand.css']:
    p=ROOT/'static'/name; s=p.read_text(encoding='utf-8')
    def gray(m):
        h=m.group()[1:]
        if len(h) in (3,4): h=''.join(c*2 for c in h)
        rgb=[int(h[i:i+2],16) for i in (0,2,4)]
        v=round(sum(a*b for a,b in zip(rgb,(.2126,.7152,.0722))))
        return '#'+f'{v:02x}'*3+h[6:]
    s=re.sub(r'#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{4}\b|#[0-9a-fA-F]{3}\b',gray,s)
    p.write_text(s,encoding='utf-8')
p=ROOT/'static/brand.css'
with p.open('a',encoding='utf-8') as f:f.write('\n.brand img{filter:grayscale(1)}\nbutton,input,select{min-height:44px}\n.page-heading{background:#181818}\n')
print('Session planning and monochrome UI installed.')
