from pathlib import Path
import shutil,json,math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit,ImageReader
ROOT=Path(__file__).resolve().parents[1]; OLD=ROOT.parent/'ASTAR-Finals'; PROJECT=ROOT.parent/'02 - Projects'/'astar'
folders=['BRAND/Logo','BRAND/Brand Guidelines','BRAND/Typography & Colours','PRODUCT/Device Renders','PRODUCT/Exploded View','PRODUCT/Architecture','SOFTWARE/Demo','SOFTWARE/Screenshots','PRESENTATION','MARKETING/Advertisement','MARKETING/Poster','MARKETING/Social Media','MERCHANDISE/Stickers','MERCHANDISE/Packaging','DOCUMENTATION/Student Quick Start Guide']
for f in folders:(ROOT/f).mkdir(parents=True,exist_ok=True)
shutil.copy2(r'C:\Users\ranji\Downloads\ASTAR Geometric Star Logo.png',ROOT/'BRAND/Logo/ASTAR-original.png')
for name,font in [('H','ariblk.ttf'),('B','arialbd.ttf'),('R','arial.ttf')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+font))
INK='#0C0C0E'; PAPER='#F0ECE4'; PURPLE='#6852FF'; MUTED='#AAA5AE'; LINE='#4B4850'
LOGO=ROOT/'BRAND/Logo/ASTAR-original.png'; HERO=ROOT/'PRODUCT/Device Renders/ASTAR-assembled-concept.png'; EXP=ROOT/'PRODUCT/Exploded View/ASTAR-reference-exploded.png'
def box(c,x,y,w,h,col):c.setFillColor(HexColor(col));c.rect(x,y,w,h,fill=1,stroke=0)
def text(c,t,x,y,size=12,col=INK,font='R'):
 c.setFillColor(HexColor(col));c.setFont(font,size);c.drawString(x,y,t)
def para(c,t,x,y,w,size=12,col=INK):
 for l in simpleSplit(t,'R',size,w):text(c,l,x,y,size,col);y-=size*1.45
 return y
def line(c,x,y,w,col=LINE):c.setStrokeColor(HexColor(col));c.setLineWidth(.6);c.line(x,y,x+w,y)
def image(c,p,x,y,w,h):c.drawImage(str(p),x,y,w,h,preserveAspectRatio=True,anchor='c',mask='auto')
def base(file,title,sub=None,dark=False):
 c=canvas.Canvas(str(ROOT/file),pagesize=(595.276,841.89));c.setTitle('ASTAR / '+title);c.setAuthor('ASTAR')
 box(c,0,0,596,842,INK if dark else PAPER);col=PAPER if dark else INK
 text(c,'ASTAR / 2026',35,804,8,PURPLE,'B');text(c,'LEARNING CONTINUITY',368,804,8,MUTED if dark else '#736E72')
 y=746
 for i,t in enumerate(title.split('\n')):text(c,t,35,y-i*38,34,PURPLE if i else col,'H')
 if sub:para(c,sub,35,y-len(title.split('\n'))*38-8,525,11,MUTED if dark else '#615A61')
 line(c,35,41,525);text(c,'AUTONOMOUS SOLAR TUTORING AND RESOURCE SYSTEM',35,25,6.6,MUTED if dark else '#736E72')
 return c
def entry(c,n,title,body,y,dark=False):
 col=PAPER if dark else INK
 line(c,35,y+20,525,LINE if dark else '#BAB4AF');text(c,n,35,y,9,PURPLE,'B');text(c,title,85,y,15,col,'B')
 return para(c,body,85,y-25,465,11,MUTED if dark else '#615A61')-40

c=base('BRAND/Brand Guidelines/ASTAR-brand-guide.pdf','LEARNING WHEN\nINFRASTRUCTURE FAILS',dark=True)
text(c,'THE ASTAR DESIGN SYSTEM',35,613,10,MUTED,'B')
y=563
for n,t,b in [('01','Make the idea unmistakable','Oversized uppercase headings. Short explanations. Strong contrast. One purple emphasis per message.'),('02','Build on the supplied presentation','Alternate near-black and warm ivory. Use fine rules, numbered sections and bold type. Keep product imagery large.'),('03','Keep the logo intact','Use the supplied logo on a white field. Preserve the gradient, proportions and whitespace. Do not redraw or stretch the mark.'),('04','Show the actual development stage','Use real software screens. Label hardware renders as concepts. Present cost targets as estimates and partners as prospective.')]:y=entry(c,n,t,b,y,True)
text(c,'PRIMARY SIGNATURE',35,130,9,MUTED,'B');image(c,LOGO,35,55,280,90);c.save()
c=base('BRAND/Typography & Colours/ASTAR-typography-colours.pdf','TYPE WITH\nPURPOSE')
text(c,'LEARNING',35,577,55,INK,'H');text(c,'CONTINUES.',35,517,55,PURPLE,'H')
para(c,'Reference fonts: Montserrat Black and Garet. These local editable files use Arial Black and Arial as available substitutes. Match the original fonts in Canva when available.',35,467,520,12)
for x,col,label in [(35,INK,'BLACK / #0C0C0E'),(215,PAPER,'IVORY / #F0ECE4'),(395,PURPLE,'PURPLE / #6852FF')]:
 box(c,x,295,165,100,col);line(c,x,295,165,'#AAA5AE');text(c,label,x,276,9,INK,'B')
para(c,'Headlines: 30-54 pt on A4. Body: 11-14 pt. Keep text inside a 12 mm safe area. Monochrome learning content stays black and white. Black and purple belong to the company and preparation interface.',35,213,520,12)
c.save()

c=base('MARKETING/Poster/ASTAR-A4-poster.pdf','LEARNING WHEN\nINFRASTRUCTURE FAILS',dark=True)
text(c,'OFFLINE LESSONS. A SOLAR-POWERED VISION.',35,639,10,MUTED,'B')
image(c,HERO,0,219,595,397)
text(c,'LEARN.',35,180,38,PAPER,'H');text(c,'WHEREVER YOU ARE.',35,136,30,PURPLE,'H')
para(c,'Explore the working offline software and proposed solar device.',35,100,520,12,PAPER)
text(c,'astarco0@gmail.com',35,61,10,PAPER);text(c,'Hardware visualization: concept',373,61,8,MUTED);c.save()

c=base('PRODUCT/Exploded View/ASTAR-exploded-view-A4.pdf','BUILT AROUND\nCONTINUITY')
image(c,EXP,16,260,563,376)
para(c,'Concept architecture from the supplied ASTAR presentation. The image describes intended modules and assembly, not validated dimensions or a manufacturing specification.',35,208,520,12)
para(c,'Solar charging. Rechargeable storage. E-paper display. Local content. Physical controls. Final electronics, energy budget, firmware and enclosure require prototype validation.',35,127,520,11)
c.save()

c=base('PRODUCT/Architecture/ASTAR-architecture.pdf','ONE SYSTEM.\nTHREE LAYERS.',dark=True)
for i,(title,body) in enumerate([('PREPARE / FORGE','Source textbook > document analysis > ranked review > learning package'),('LEARN / SOFTWARE','Local package > chapter and lesson circles > reading > practice > local progress'),('POWER / HARDWARE CONCEPT','Solar panel > charge controller > battery > controller, display and storage')]):
 y=529-i*151;box(c,35,y-53,525,105,'#201E24');text(c,str(i+1).zfill(2),50,y+27,9,PURPLE,'B');text(c,title,50,y,16,PAPER,'B');para(c,body,50,y-25,491,11,MUTED)
para(c,'The desktop reader and proposed device firmware are separate development stages. Hardware compatibility and energy use must be measured.',35,104,525,11,MUTED);c.save()

c=base('MERCHANDISE/Stickers/ASTAR-A4-stickers.pdf','LEARNING,\nANYWHERE.')
for row in range(3):
 for col in range(2):
  x=35+270*col;y=474-row*155
  box(c,x,y,255,138,INK if row!=1 else '#FFFFFF');image(c,LOGO,x+8,y+54,239,80)
  text(c,['LEARN OFFLINE','KNOWLEDGE WITHIN REACH','KEEP LEARNING'][row],x+14,y+29,12,PURPLE,'B')
  text(c,'ASTAR / LEARNING CONTINUITY',x+14,y+13,6.6,PAPER if row!=1 else INK)
text(c,'A4 / 100% scale / Cut at tile edges / No bleed',35,68,9,INK);c.save()

c=base('MERCHANDISE/Packaging/ASTAR-A4-box-labels.pdf','READY FOR\nTHE NEXT LESSON')
box(c,35,369,525,248,INK);image(c,LOGO,55,494,250,83)
text(c,'LEARNING WHEN',55,470,23,PAPER,'H');text(c,'INFRASTRUCTURE FAILS',55,441,23,PURPLE,'H')
text(c,'ASTAR / PROTOTYPE',55,391,9,MUTED,'B')
box(c,35,201,525,137,'#FFFFFF');text(c,'START HERE',52,307,20,INK,'H')
para(c,'Open the course. Choose a lesson. Read and practise. Back up your progress. Keep the quick-start guide with your device or computer.',52,279,489,12)
para(c,'Cut labels: front 185 x 87 mm; instruction label 185 x 48 mm. Print at 100%. Measure the actual box before making a sleeve. These are printable labels, not a box dieline.',35,155,520,11)
c.save()

c=base('DOCUMENTATION/Student Quick Start Guide/ASTAR-quick-start.pdf','YOUR NEXT\nLESSON STARTS HERE')
y=597
for n,t,b in [('01','Open your course','Open the offline HTML course in a browser on your computer. Keep the course file so you can return to it.'),('02','Choose and read','Choose a chapter, then a numbered lesson. Read the text and monochrome diagrams. Adjust text size if needed.'),('03','Try the questions','Choose answers for interactive practice where provided. Write longer answers in a notebook. Ask a teacher or facilitator for help.'),('04','Keep your progress','Mark lessons complete. Resume using the same browser profile. Export a progress backup regularly, because browser storage can be cleared.')]:y=entry(c,n,t,b,y)
para(c,'For facilitators: check content and language before use. This guide describes the existing computer reader. Physical device controls remain under development.',35,102,520,10)
c.save()

# Social campaign. All original editable compositions are PDFs, exported to PNG later.
social=[('01-introduction','LEARNING WHEN','INFRASTRUCTURE FAILS','ASTAR combines offline software with a proposed solar-powered learning device.'),('02-software','ONE TEXTBOOK.','MANY NEXT STEPS.','Prepare chapters and lessons. Preserve explanations, diagrams and questions.'),('03-hardware','LOW POWER.','HIGH AMBITION.','An e-paper learning device with local storage and solar charging. Hardware concept.'),('04-forge','PREPARE. REVIEW.','TAKE IT OFFLINE.','ASTAR Forge highlights likely conversion problems for targeted review.'),('05-mission','KNOWLEDGE','WITHIN REACH.','Access to learning should not depend on access to infrastructure.'),('06-invitation','BUILD THE','NEXT CHAPTER.','Seeking technical mentors and education collaborators. astarco0@gmail.com')]
for idx,(name,a,b,body) in enumerate(social):
 c=canvas.Canvas(str(ROOT/'MARKETING/Social Media'/f'{name}.pdf'),pagesize=(1080,1080));dark=idx%2==0
 bg=INK if dark else PAPER;fg=PAPER if dark else INK;box(c,0,0,1080,1080,bg)
 text(c,'ASTAR / 2026',66,1004,19,PURPLE,'B');text(c,a,66,862,57,fg,'H');text(c,b,66,792,57,PURPLE,'H')
 if idx in [0,2]:image(c,HERO,0,215,1080,555)
 else:
  line(c,66,655,948,'#655E70');text(c,'0'+str(idx+1),66,390,180,fg,'H');text(c,'LEARNING CONTINUITY',70,330,24,PURPLE,'B')
 para(c,body,66,159,948,28,fg);text(c,'ASTAR / AUTONOMOUS SOLAR TUTORING AND RESOURCE SYSTEM',66,46,12,fg)
 c.save()

# Slide scenes. Pixel coordinates are shared between the PDF and editable PPTX.
scenes=[]
def scene(title,accent='',dark=True,kind='text',body='',image_path=None,cols=None,notes=''):
 scenes.append(dict(title=title,accent=accent,dark=dark,kind=kind,body=body,image=str(image_path) if image_path else None,cols=cols,notes=notes))
scene('ASTAR','LEARNING WHEN\nINFRASTRUCTURE FAILS',kind='cover',notes='Introduce ASTAR as an offline-first learning initiative. Software is available as a prototype; the solar device is a concept.')
scene('WHEN INFRASTRUCTURE','FAILS',cols=[('01 / POWER','Charging becomes uncertain'),('02 / CONNECTIVITY','Online lessons become harder to reach'),('03 / CONTINUITY','Students need a dependable fallback')],body='ASTAR is designed to complement teachers and education services when access is disrupted.')
scene('INTRODUCING','ASTAR',cols=[('DEVICE','Proposed low-power solar hardware'),('SOFTWARE','Offline reading, practice and progress'),('FORGE','Content preparation, review and export')],notes='Forge is the name used here for the existing textbook studio and its content-preparation role.')
scene('THE PRODUCT','CONCEPT',False,'image','E-paper reading. Physical controls. Local storage. Solar charging.',HERO,notes='Generated assembled visualization based on the supplied exploded view. Component compatibility, dimensions and runtime remain to be validated.')
scene('DESIGNED AS','A SYSTEM',False,'image','An intended modular architecture for learning continuity.',EXP,notes='Exploded reference image extracted unchanged from user-supplied ASTAR.pdf. Illustration is not a verified engineering drawing.')
scene('A WHOLE TEXTBOOK.','ONE LESSON AT A TIME.',True,'image','Prepare material locally, then export an offline course.',ROOT/'SOFTWARE/Screenshots/01-library.png',notes='Screenshot captured from the current software build.')
scene('REVIEW WHAT','NEEDS ATTENTION',False,'image','Ranked conversion checks. Source-page comparison. An exclusion log.',ROOT/'SOFTWARE/Screenshots/10-triage.png',notes='Automatic checks help prioritise likely extraction issues. They are not a guarantee of teaching accuracy.')
scene('READ. PRACTISE.','KEEP LEARNING.',True,'image','Numbered navigation, monochrome lessons and locally saved progress.',ROOT/'SOFTWARE/Screenshots/09-lesson-circles.png',notes='Existing software. Teacher-authored MCQs use explicit answer keys. Long answers use notebooks. Hardware firmware is future work.')
scene('WHO IS','ASTAR FOR?',False,cols=[('LEARNERS','Students aged 10-18 in disrupted or underserved settings'),('DEPLOYMENT','Education organisations and institutional pilots'),('SUPPORT','Facilitators, reviewed content and local updates')],notes='These are intended users and prospective partner types, not signed partnerships.')
scene('A TARGET PRICE','TO VALIDATE',cols=[('INR 3,700','Founder target unit cost'),('INR 4,700','Founder target selling price')],body='Unvalidated estimates. Confirm components, battery, charging, testing, logistics and support costs.',notes='Targets from ASTAR.pdf, not current supplier quotations. No margin claim is made.')
scene('THE NEXT','MILESTONE',False,cols=[('01 / HARDWARE','Measure power use and charging performance'),('02 / CONTENT','Review a small teaching package'),('03 / PILOT','Test with learners and refine deployment')])
scene('LEARNING SHOULD','CONTINUE.',True,'close','Seeking technical mentors and education collaborators.\nastarco0@gmail.com',notes='End with the specific collaboration request and invite a demo.')
(ROOT/'_source/scenes.json').write_text(json.dumps(scenes,indent=2),encoding='utf-8')
def draw_scene(c,s,i):
 dark=s['dark'];fg=PAPER if dark else INK;muted=MUTED if dark else '#625D63';box(c,0,0,1440,810,INK if dark else PAPER)
 text(c,'ASTAR / AUTONOMOUS SOLAR TUTORING AND RESOURCE SYSTEM',65,765,11,PURPLE,'B');text(c,'ASTAR / 2026',1230,765,11,muted)
 if s['kind']=='cover':
  text(c,'ASTAR',64,395,210,fg,'H');text(c,'LEARNING WHEN',70,300,65,fg,'H');text(c,'INFRASTRUCTURE FAILS',70,221,65,PURPLE,'H')
 else:
  text(c,s['title'],65,665,49,fg,'H');text(c,s['accent'],65,607,49,PURPLE,'H')
  if s['kind']=='image':
   image(c,Path(s['image']),560,125,815,440);para(c,s['body'],65,485,430,28,muted)
   if i in [3,4]:text(c,'DESIGN CONCEPT / SUBJECT TO VALIDATION',560,101,13,muted,'B')
  elif s.get('cols'):
   n=len(s['cols']);cw=1310/n
   for j,(a,b) in enumerate(s['cols']):
    x=65+j*cw;line(c,x,490,cw-28,LINE if dark else '#B8B1AC');text(c,a,x,440,22,PURPLE,'B');para(c,b,x,378,cw-38,30,fg)
   if s['body']:para(c,s['body'],65,174,1280,23,muted)
  elif s['kind']=='close':
   para(c,s['body'].replace('\n',' '),65,406,1010,34,fg);image(c,LOGO,65,116,550,184)
 line(c,65,61,1310,LINE if dark else '#B8B1AC');text(c,f'{i+1:02} / {len(scenes):02}',65,35,12,muted)
c=canvas.Canvas(str(ROOT/'PRESENTATION/ASTAR-Pitch-Deck.pdf'),pagesize=(1440,810))
for i,s in enumerate(scenes):draw_scene(c,s,i);c.showPage()
c.save()
print('Collection authored')
