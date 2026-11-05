from pathlib import Path
import json, shutil, math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables'; AS=ROOT/'assets'
OUT.mkdir(exist_ok=True); AS.mkdir(exist_ok=True)
shutil.copy2(r'C:\Users\ranji\Downloads\ASTAR Geometric Star Logo.png',AS/'ASTAR-original-logo.png')
PROJECT=Path(r'D:\My_Command_Center\02 - Projects\astar')
for f in ['09-lesson-circles.png','14-real-maths-lesson.png','10-triage.png','07-offline.png']:
    shutil.copy2(PROJECT/'test-results'/f,AS/f)
shutil.copy2(PROJECT/'test-results'/'astar-reader.html',OUT/'ASTAR-offline-sample.html')
for n,f in [('Regular','arial.ttf'),('Bold','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(n,str(Path('C:/Windows/Fonts')/f)))
INK='#181A27'; PURPLE='#7041C6'; PALE='#F0EAF9'; GRAY='#5D6070'; PAPER='#FAF9FC'
A4=(595.276,841.89)

def rect(c,x,y,w,h,fill,stroke=None):
    c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(stroke or fill)); c.rect(x,y,w,h,fill=1,stroke=bool(stroke))
def text(c,t,x,y,size=12,color=INK,bold=False):
    c.setFillColor(HexColor(color)); c.setFont('Bold' if bold else 'Regular',size); c.drawString(x,y,t)
def para(c,t,x,y,w,size=11,color=GRAY,leading=None):
    leading=leading or size*1.45
    for line in simpleSplit(t,'Regular',size,w): text(c,line,x,y,size,color); y-=leading
    return y
def logo(c,x,y,w):
    # Original raster preserved. White surround is part of supplied artwork.
    c.drawImage(str(AS/'ASTAR-original-logo.png'),x,y,width=w,height=w*725/2170,mask='auto')
def base(name,title,kicker='ASTAR / FINALS COLLECTION',size=A4):
    c=canvas.Canvas(str(OUT/name),pagesize=size); c.setTitle('ASTAR - '+title); c.setAuthor('ASTAR')
    w,h=size; rect(c,0,0,w,h,'#FFFFFF'); rect(c,32,h-40,26,4,PURPLE)
    text(c,kicker,70,h-41,8,GRAY,True)
    text(c,title,32,h-96,26,INK,True)
    return c
def foot(c,note='ASTAR / Autonomous Solar Tutoring and Resource System'):
    text(c,note,32,24,7,GRAY)
def block(c,n,title,body,y):
    text(c,n,32,y,11,PURPLE,True); text(c,title,65,y,15,INK,True)
    return para(c,body,65,y-23,490,11)-27
def device(c,x,y,w=260,h=300):
    c.setFillColor(HexColor(INK)); c.roundRect(x,y,w,h,20,fill=1,stroke=0)
    rect(c,x+18,y+62,w-36,h-88,'#F5F3F8')
    text(c,'ASTAR',x+30,y+h-49,13,INK,True)
    text(c,'01  SCIENCE',x+30,y+h-77,9,PURPLE,True)
    text(c,'Light and life',x+30,y+h-105,16,INK,True)
    para(c,'Plants use light to make food. Study the lesson, then try a question.',x+30,y+h-130,w-60,10)
    c.setStrokeColor(HexColor(PURPLE)); c.setLineWidth(1.5)
    c.line(x+70,y+93,x+70,y+139); c.ellipse(x+50,y+125,x+70,y+140); c.ellipse(x+70,y+110,x+92,y+127)
    for i in range(3):
        c.setFillColor(HexColor(PURPLE if i==1 else '#656174')); c.circle(x+w/2+(i-1)*49,y+30,10,fill=1,stroke=0)
def arrow(c,x,y,x2,y2):
    c.setStrokeColor(HexColor(PURPLE)); c.setLineWidth(1.5); c.line(x,y,x2,y2)
    a=math.atan2(y2-y,x2-x)
    for d in [-.5,.5]:c.line(x2,y2,x2-8*math.cos(a+d),y2-8*math.sin(a+d))

# 01. A4 brand reference
c=base('01-Brand-guide.pdf','A clear identity for resilient learning')
logo(c,28,592,535)
text(c,'Learning should not stop',32,570,23,INK,True); text(c,'when the lights go out.',32,540,23,PURPLE,True)
para(c,'Use the supplied wordmark as the primary signature. Preserve its proportions, gradient and clear space. Place it on white for reliable contrast.',32,502,520)
for x,col,label in [(32,INK,'INK  #181A27'),(210,PURPLE,'PURPLE  #7041C6'),(388,PALE,'PALE  #F0EAF9')]:
    rect(c,x,386,155,61,col); text(c,label,x,369,9,GRAY,True)
y=329
y=block(c,'01','Typography','Arial Bold for headlines. Arial for body text. Use short sentences, generous margins and large, readable diagrams.',y)
y=block(c,'02','Layout','A4 print: 15 mm safe margin. White backgrounds, black text, purple rules and circular navigation cues. Use purple sparingly.',y)
y=block(c,'03','Voice','Explain what students can do. Distinguish working software, proposed hardware and future validation. Describe organisations as prospective partners.',y)
foot(c,'Brand reference / Supplied logo retained / Accent selected to coordinate with logo'); c.save()

# 02. poster
c=base('02-A4-hero-poster.pdf','',kicker='ASTAR / LEARNING CONTINUITY')
logo(c,22,642,550)
text(c,'Learning should',32,607,39,INK,True); text(c,'not stop when',32,561,39,INK,True); text(c,'the lights go out.',32,515,39,PURPLE,True)
device(c,315,157,238,292)
text(c,'Learn offline.',32,431,24,INK,True)
para(c,'Structured lessons. Practice questions. Progress kept locally.',32,397,244,15)
para(c,'An offline learning platform with a proposed solar-powered educational device.',32,298,235,12)
text(c,'Explore the demonstration',32,156,13,PURPLE,True)
text(c,'astarco0@gmail.com',32,131,11,INK)
text(c,'Device illustration: design concept',315,141,8,GRAY)
para(c,'Autonomous Solar Tutoring and Resource System',32,83,500,10)
foot(c,'Software prototype / Solar hardware under development'); c.save()

# 03. product / company handout
c=base('03-Product-and-company-sheet.pdf','Learning beyond the network')
logo(c,380,44,180)
para(c,'ASTAR is an offline-first education initiative combining a learning platform, content-preparation tools and proposed solar-powered hardware.',32,705,520,15,INK)
y=620
y=block(c,'01','ASTAR learning platform','Students navigate chapters and lessons, read text and monochrome diagrams, practise with teacher-authored questions and resume locally saved progress.',y)
y=block(c,'02','ASTAR Forge / content preparation','The existing textbook studio extracts and organises PDF content, flags conversion issues for review, and exports portable learning packages and standalone HTML readers.',y)
y=block(c,'03','Proposed ASTAR device','A compact device with an e-paper display, physical controls, local content storage, rechargeable battery and solar charging. Components, power budget and enclosure remain to be validated.',y)
y=block(c,'04','Intended deployment','Students aged 10-18 in disrupted or underserved learning settings. The proposed route is through education organisations, humanitarian teams and institutional pilots.',y)
rect(c,32,139,531,90,PALE)
text(c,'Development and commercial targets',48,207,13,PURPLE,True)
para(c,'Software prototype exists. Hardware is proposed. Founder estimates: INR 3,700 unit cost and INR 4,700 institutional selling price. These are unvalidated targets, not supplier quotes or final prices.',48,184,498,10)
text(c,'Seeking technical mentors and pilot-design collaborators',32,103,12,INK,True)
text(c,'astarco0@gmail.com',32,78,11,PURPLE)
foot(c,'Based on the supplied ASTAR brief, existing project documentation and founder presentation'); c.save()

# 04. sticker sheet: white-background logo tiles, safe borders
c=base('04-A4-sticker-sheet.pdf','Carry the idea forward')
for row in range(3):
    for col in range(2):
        x=32+col*272; y=510-row*174
        c.setStrokeColor(HexColor('#CBC6D4')); c.setDash(3,3); c.roundRect(x,y,258,150,10,fill=0,stroke=1);c.setDash()
        logo(c,x+7,y+65,244)
        text(c,['LEARN OFFLINE','LEARNING, ANYWHERE.','KEEP LEARNING'][row],x+17,y+45,13,PURPLE,True)
        text(c,'Autonomous Solar Tutoring',x+17,y+25,8,GRAY)
        text(c,'and Resource System',x+17,y+13,8,GRAY)
foot(c,'A4 / Print at 100% / Dashed lines are manual trim guides / No bleed');c.save()

# 05. merch production placement + cards
c=base('05-Merchandise-and-packaging.pdf','A coordinated team presence')
text(c,'TEAM T-SHIRT / PRODUCTION PLACEMENT',32,702,11,PURPLE,True)
rect(c,32,484,249,191,PAPER);rect(c,301,484,262,191,PAPER)
logo(c,51,581,116);text(c,'FRONT',48,505,9,GRAY,True)
text(c,'LEARNING',320,622,23,INK,True);text(c,'SHOULD NOT STOP.',320,592,17,PURPLE,True)
text(c,'ASTAR',320,549,12,INK,True);text(c,'BACK',320,505,9,GRAY,True)
para(c,'White shirt: supplied full-colour logo, 90 mm wide at left chest. Back: 240 mm wide headline. Black shirt: use a white logo patch or ask a designer for an approved reverse master. Do not print the white rectangle accidentally.',32,458,530,11)
text(c,'BOX SLEEVE / FRONT LABEL',32,362,11,PURPLE,True)
rect(c,32,214,531,128,'#FFFFFF','#CBC6D4');logo(c,42,247,255)
text(c,'Learning, anywhere.',309,285,17,PURPLE,True)
text(c,'PROTOTYPE / HANDLE WITH CARE',309,257,8,GRAY,True)
para(c,'Label size: 187 x 45 mm at 100%. Fit a sleeve to your actual box after measuring it. This sheet is a placement reference, not a structural box dieline.',32,188,530,10)
text(c,'PRINT HANDOFF',32,113,11,PURPLE,True)
para(c,'Supply the original logo PNG and this placement sheet to the printer. Request a physical proof for logo sharpness, purple colour and fabric contrast before the full run.',32,90,530,10)
foot(c,'Production reference / Actual garment and packaging dimensions must be confirmed');c.save()

# 06. quick start, four sections on one A4
c=base('06-Student-quick-start.pdf','Your next lesson starts here')
text(c,'ASTAR / OFFLINE READER',32,706,11,PURPLE,True)
y=653
for n,t,b in [('01','Open your course','Open the offline HTML course on your computer. Keep a copy of the course file somewhere safe.'),('02','Choose a lesson','Choose a chapter, then a numbered lesson. Read the text and diagrams. Adjust text size if needed.'),('03','Try a question','Use interactive options where provided. For notebook questions, write or draw your answer on paper. Feedback depends on the question type.'),('04','Save your progress','Mark a lesson complete and resume in the same browser profile. Use Export progress for a backup. Browser data can be cleared, so keep that backup.')]:
    y=block(c,n,t,b,y)-16
rect(c,32,112,531,84,PALE);text(c,'For teachers and facilitators',48,173,13,PURPLE,True)
para(c,'Review course accuracy before use. Original textbook prompts may require teacher feedback. Support students with unfamiliar language, navigation or concepts.',48,151,495,10)
foot(c,'Guide for the existing computer reader / Hardware controls may change');c.save()

# 07 architecture
c=base('07-Technical-architecture.pdf','One learning system, three layers')
for y,label,body in [(620,'PREPARE / ASTAR FORGE','Source PDF > extraction and page images > lesson review > export'),(442,'DELIVER / OFFLINE SOFTWARE','Local course package > chapters and lessons > practice > local progress'),(264,'POWER / PROPOSED HARDWARE','Solar panel > charge controller > rechargeable battery > device electronics')]:
    rect(c,32,y,531,102,PALE if y!=264 else PAPER)
    text(c,label,48,y+76,13,PURPLE,True);para(c,body,48,y+48,493,12,INK)
arrow(c,297,620,297,557);arrow(c,297,442,297,379)
para(c,'Target device blocks: controller, local storage, e-paper display and physical controls. Firmware and hardware package format remain to be specified.',32,226,531,11)
para(c,'Validation required: daily energy use, charging performance, battery safety, display refresh, memory use, durability, repairability and learner usability.',32,155,531,11)
foot(c,'Conceptual architecture / No component compatibility, runtime or safety certification implied');c.save()

# 08 A4 cut cards and tent
c=base('08-Contact-cards-and-table-sign.pdf','Meet ASTAR')
for x in [32,307]:
    for y in [500,650]:
        rect(c,x,y,255,128,'#FFFFFF','#CBC6D4');logo(c,x+6,y+47,242)
        text(c,'LEARNING, ANYWHERE.',x+15,y+35,10,PURPLE,True)
        text(c,'astarco0@gmail.com',x+15,y+15,10,INK)
rect(c,32,139,531,286,'#FFFFFF','#CBC6D4');logo(c,52,252,491)
text(c,'TRY A LESSON. ASK A QUESTION.',61,233,22,PURPLE,True)
para(c,'Explore the offline software demonstration. Ask the team about the proposed solar device and our next development milestones.',61,194,470,12)
foot(c,'A4 / Print at 100% / Cut along grey outlines / Contact copied from supplied ASTAR.pdf');c.save()

# Shared slide content used by editable deck and rehearsal guide
slides=[
dict(title='Learning should not stop\nwhen the lights go out',body='ASTAR\nAutonomous Solar Tutoring and Resource System',kind='cover',notes='Open with the mission. ASTAR is an offline-first learning initiative. The software exists as a local prototype, while the solar device is proposed.'),
dict(title='Learning needs a dependable fallback',body='When power, connectivity or access to schools is interrupted, students can lose access to digital lessons.\n\nASTAR is designed to keep structured learning materials within reach.',kind='statement',notes='Explain the design problem without quoting unverified statistics. ASTAR complements teachers and schools. It does not claim to replace them.'),
dict(title='Three parts, one learning experience',body='ASTAR device\nProposed solar-powered educational hardware\n\nASTAR software\nOffline lessons, practice and local progress\n\nASTAR Forge\nContent preparation, review and export',kind='system',notes='Forge is the proposed name for the content-preparation role fulfilled by the current textbook studio. Hardware integration is future work.'),
dict(title='Choose a lesson. Keep learning.',body='Numbered chapters and lessons\nMonochrome reading and diagrams\nLocal completion and resume state',kind='image',image='09-lesson-circles.png',notes='Existing saved software screenshot from the workspace test-results folder. Demonstrate the current reader rather than describing a future interface.'),
dict(title='Preserve the detail that learning needs',body='Textbook reading with diagrams\nPage references and original prompts\nTeacher-authored interactive practice',kind='image',image='14-real-maths-lesson.png',notes='Existing mathematics-reader screenshot. Complex notation is preserved as image regions. Original textbook MCQs are not reliably parsed into interactive options. Long answers are written on paper.'),
dict(title='Prepare content with review built in',body='Import a textbook PDF\nInspect flagged conversion issues\nExport a standalone offline reader',kind='image',image='10-triage.png',notes='Existing saved textbook-studio screenshot. Conversion uses heuristics. Automatic checks are not a guarantee of educational accuracy. Human content review remains necessary.'),
dict(title='The solar device is the next step',body='E-paper display and physical controls\nLocal lessons and storage\nSolar charging with battery storage\n\nNext: validate components, power use and firmware',kind='hardware',notes='The device illustration is a concept, not a photograph or manufacturing specification. Battery runtime, controller selection, dimensions and costs are not validated.'),
dict(title='Start with an education partner',body='Intended learners\nStudents aged 10-18 in disrupted and underserved settings\n\nProposed route\nPartner-led pilot, facilitator support and local content review',kind='statement',notes='Education NGOs and humanitarian organisations are prospective deployment partners. No partnership, signed procurement or field deployment is claimed.'),
dict(title='An institutional model to validate',body='INR 3,700\nFounder target unit cost\n\nINR 4,700\nFounder target institutional selling price',kind='pricing',notes='Targets copied from supplied ASTAR.pdf, not supplier quotes. The implied INR 1,000 difference must cover costs not yet established. Validate battery, charging, testing, shipping, tax, support and content costs before claiming a margin.'),
dict(title='Make the next milestone measurable',body='1  Validate the hardware energy budget\n2  Review a small curriculum package\n3  Test reading and navigation with learners\n4  Refine cost and partner-led pilot design',kind='statement',notes='Measure task completion, reading usability, content errors and device energy use. These are proposed tests. No learning-outcome improvement or field results are claimed.'),
dict(title='Help us make learning more resilient',body='Seeking technical mentors and education collaborators\n\nastarco0@gmail.com',kind='close',notes='Close with a focused invitation to technical mentors and organisations who can help design a responsible pilot. Mission: access to learning should not depend on access to infrastructure.')
]
(ROOT/'source'/'slides.json').write_text(json.dumps(slides,indent=2),encoding='utf-8')

guide='''# ASTAR finals: presenter and production guide

## 30-second introduction
ASTAR stands for Autonomous Solar Tutoring and Resource System. We are building a way for students to keep learning when electricity and internet access are unreliable. Our existing software prepares textbooks for offline reading, practice and local progress tracking. Our next step is a compact solar-powered learning device, developed with educational and technical input.

## 90-second demonstration
Before the pitch, open ASTAR-offline-sample.html in the presentation browser. Check it works and export a progress backup. The sample contains original test content, not a complete curriculum.
1. Disconnect the network and show the already downloaded course.
2. Choose a chapter and a numbered lesson.
3. Show the reading content and diagram. This demonstrates the existing computer reader.
4. Show a question if available. Explain which responses use paper and which have authored answer keys.
5. Mark the lesson complete. Return to navigation and show the completion state.
6. Close and reopen in the same browser profile to check resume. If local-file storage is blocked, explain the limitation and use the progress export/import controls.
7. Finish with the proposed hardware diagram. Do not claim that computer software is already device firmware.

## Three-minute pitch
Imagine trying to keep studying when your connection disappears and charging a device becomes difficult. Education needs a dependable fallback.

We are building ASTAR, the Autonomous Solar Tutoring and Resource System. Our principle is simple: access to learning should not depend on access to infrastructure.

ASTAR has three connected parts. The learning software provides structured lessons, diagrams and practice, with progress stored locally. ASTAR Forge describes our content-preparation system: it turns source textbooks into organised learning packages, with review tools to catch conversion problems. The proposed hardware brings that experience to a compact solar-powered device with an e-paper display and physical controls.

Here is what exists today. Our local textbook studio can prepare PDF content and export a standalone HTML reader. The reader can run without an internet connection after the course is transferred. Students can select lessons, view learning material and keep local progress. Teacher-authored practice can provide checked feedback, while notebook questions still need a student or teacher to review them.

Our intended users are students in underserved or disrupted learning settings. We aim to work through organisations already supporting education in those communities. A pilot would help us learn which content, languages and support arrangements are useful in practice.

The solar hardware remains a development goal. We need to validate the display, charging system, battery, firmware and real energy use. Our initial cost and selling-price targets are estimates that need a complete bill of materials and supplier quotations.

Our next milestone is a tested hardware prototype paired with a small reviewed learning package. We are seeking technical mentors and education collaborators to help us reach it. Learning should not stop when the lights go out.

## Questions judges may ask
- Is the device built? The software prototype exists. State the actual hardware assembly status on contest day; the supplied materials treat it as proposed.
- Is there an offline AI tutor? No working general-purpose offline AI tutor was established from the inspected project. Show authored lessons and practice.
- Does it replace teachers? It complements teachers and facilitators.
- How long does the battery last? Runtime must be measured on the selected hardware; no validated figure is available.
- How is content checked? Conversion flags and source-page views support review. Educational review and permissions are still required before deployment.
- Why not a tablet? Explain the intended tradeoff: simple controls, low power and focused offline learning. Comparative cost and durability need testing.
- Who are your partners? Describe prospective partner types. Do not name organisations as confirmed partners without agreements.
- Is INR 4,700 final? It is a founder target. Battery, charging, testing, logistics, tax, repair and support costs need to be established.

## Printing and assembly
- Print the PDFs on A4 at 100%, with no fit-to-page scaling for cut sheets.
- Poster and handout: use matte stock. Sticker sheet: use A4 self-adhesive stock and cut on the guides.
- PDFs use RGB artwork with white margins and no bleed. Ask the local printer for a colour proof; these are office-print masters, not press-certified CMYK files.
- Merchandise sheet shows placement. It is not a garment pattern or box dieline. Check logo quality at final print size with the printer.
- Contact email is copied from the supplied ASTAR.pdf. No QR is included because a final destination has not been confirmed.
- The logo PNG is supplied unchanged. Arial is used for readable editable text. Purple accent: #7041C6. Ink: #181A27.

## Final-day checklist
Open the deck on the actual presentation computer. Check the font and projector contrast. Rehearse to the contest time limit. Keep the offline sample, a progress backup, the PDF deck and a locally recorded demo video on two storage devices. Charge the laptop. Pack adapters, device, table sign, handouts and tape. Disable notifications before presenting.

## Asset provenance and limits
Logo and founder cost targets/contact: user-supplied ASTAR logo and ASTAR.pdf. Product narrative: supplied ASTAR brief. Software screenshots and sample HTML: existing ASTAR/test-results. Screenshots are saved development evidence and were not recaptured during this asset build. No external statistics, partner endorsements or manufactured product photos are used. The illustration is a schematic concept. The software sample was created earlier in the project; run the demonstration rehearsal before contest use.
'''
(OUT/'09-Presenter-and-production-guide.md').write_text(guide,encoding='utf-8')
(OUT/'10-Slide-speaker-notes.md').write_text('\n\n'.join(f"## {i+1}. {s['title'].replace(chr(10),' ')}\n{s['notes']}" for i,s in enumerate(slides)),encoding='utf-8')
print('Print collection and speaker content created')
