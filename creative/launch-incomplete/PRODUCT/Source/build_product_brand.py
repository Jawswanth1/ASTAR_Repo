from pathlib import Path
import json, shutil, html, math

ROOT=Path(__file__).resolve().parents[2]
INK='#0C0C0E'; IVORY='#F0ECE4'; PURPLE='#6852FF'; GRAY='#65636A'; LINE='#C9C6CE'
for p in ['PRODUCT/Renders','PRODUCT/Exploded-Views','PRODUCT/Architecture','PRODUCT/QA','BRAND/Logos','BRAND/Brand-Guidelines/Source','BRAND/Brand-Guidelines/QA','BRAND/Typography','BRAND/Colour-System','assets/design-references']:(ROOT/p).mkdir(parents=True,exist_ok=True)

def txt(x,y,t,size=20,color=INK,weight='400',anchor='start'):
 return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{html.escape(t)}</text>'
def rect(x,y,w,h,fill='none',stroke=INK,r=0,dash=''):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def line(x1,y1,x2,y2,color=INK,dash='',arrow=False):
 return f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}" stroke-width="2" fill="none"'+(f' stroke-dasharray="{dash}"' if dash else '')+(' marker-end="url(#arrow)"' if arrow else '')+'/>'
def circ(x,y,r,fill='none',stroke=INK):return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
def svg(body,w=1200,h=800,bg='#FFFFFF',title='ASTAR concept'):
 return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>{html.escape(title)}</title><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="{INK}"/></marker></defs>'+ (rect(0,0,w,h,bg,bg) if bg else '')+body+'</svg>'
def page(title,sub,body,foot='CONCEPT / NOT A MANUFACTURING OR WIRING DRAWING'):
 return svg(txt(50,48,'ASTAR / PRODUCT DEVELOPMENT',14,PURPLE,'700')+txt(50,110,title,40,INK,'700')+txt(50,148,sub,18,GRAY)+body+line(50,742,1150,742,LINE)+txt(50,772,foot,13,GRAY))
def save(rel,data):(ROOT/rel).write_text(data,encoding='utf-8')

# Explicitly new production variants; original identity remains unchanged alongside them.
shutil.copy2(r'C:\Users\ranji\Downloads\ASTAR Geometric Star Logo.png',ROOT/'BRAND/Logos/ASTAR-original.png')
star='M60 2 L76 43 L118 60 L76 76 L60 118 L44 76 L2 60 L44 44 Z M60 40 L53 53 L40 60 L53 67 L60 80 L67 67 L80 60 L67 53 Z'
def symbol(color,scale=1,x=0,y=0):return f'<g transform="translate({x},{y}) scale({scale})"><path d="{star}" fill="{color}" fill-rule="evenodd"/></g>'
for variant,color in [('black',INK),('white','#FFFFFF'),('monochrome','#000000'),('purple',PURPLE)]:
 save(f'BRAND/Logos/ASTAR-primary-{variant}.svg',svg(txt(20,119,'ASTAR',114,color,'900')+symbol(color,1,430,25),580,175,None,'ASTAR production primary logo'))
 save(f'BRAND/Logos/ASTAR-wordmark-{variant}.svg',svg(txt(14,117,'ASTAR',114,color,'900'),425,155,None,'ASTAR production wordmark'))
 save(f'BRAND/Logos/ASTAR-symbol-{variant}.svg',svg(symbol(color,1,10,10),140,140,None,'ASTAR four-point symbol'))
 save(f'BRAND/Logos/ASTAR-secondary-{variant}.svg',svg(symbol(color,1.1,84,10)+txt(150,220,'ASTAR',70,color,'900','middle'),300,250,None,'ASTAR stacked signature'))
save('BRAND/Logos/README.md', '''# ASTAR logo assets

ASTAR-original.png is the supplied logo, copied unchanged. The SVG family is a new production simplification: Arial Black-style wordmark and geometric four-point star, drawn as editable vector elements. It is not an exact tracing of the supplied custom lettering. Use one family consistently per application; the new black/white production family is the launch default.

Files named primary combine the wordmark and symbol. Secondary is stacked. Symbol is for small square uses; wordmark is for narrow spaces. Black, white, monochrome and purple variants are included. SVGs use live Arial text with weight 900; install/use Arial Black or convert to outlines in your design software before vendor handoff. The final PNGs are reference exports. Do not mix the old gradient symbol with the new plain wordmark.

Minimum width: primary 30 mm / 150 px; wordmark 25 mm / 125 px; secondary 22 mm / 110 px; symbol 6 mm / 24 px. Use one symbol-arm depth (one quarter of symbol height) clear space on every side. These are design recommendations, not tested legibility thresholds.
''')
tokens={'ink':INK,'paper':IVORY,'accent':PURPLE,'muted':GRAY,'line':LINE,'type':{'display':'Arial Black, Arial, sans-serif','body':'Arial, sans-serif'},'space':[4,8,12,16,24,32,48,64]}
save('BRAND/Colour-System/tokens.json',json.dumps(tokens,indent=2))
save('BRAND/Colour-System/tokens.css',f':root{{--astar-ink:{INK};--astar-paper:{IVORY};--astar-accent:{PURPLE};--astar-muted:{GRAY};--astar-line:{LINE};--astar-body:Arial,sans-serif;--astar-display:"Arial Black",Arial,sans-serif;}}\n')
save('BRAND/Typography/README.md','''# Typography

Display: Arial Black, with Arial Bold as fallback. Body: Arial. Both are installed Windows fonts, not redistributed in this package. Use system sans-serif fallback when unavailable. The supplied presentation referenced Montserrat Black and Garet; these are not required for this offline package.

Digital: heading 32-64 px, body 17-20 px, labels 12-14 px. Reader text is adjustable. Print: body 11-12 pt; small supporting labels no less than 8 pt. Deck: titles 32-44 pt, body 18-24 pt. Avoid compressed tracking and long all-caps paragraphs.
''')
save('DESIGN_SYSTEM.md', '''# ASTAR design system

The launch uses a restrained editorial identity built from existing ASTAR references. The supplied logo remains preserved; new production SVG variants simplify it for one-colour use. This system is a launch design, not a trademark registration or final industrial specification.

## Colour
Ink #0C0C0E, warm paper #F0ECE4, accent #6852FF, secondary text #65636A, rules #C9C6CE. Use black/white for learning content. Purple marks navigation context and limited brand emphasis; never use colour alone to convey an answer or state. Small purple text goes on white only; avoid purple body text on ivory.

## Type and spacing
Arial Black for short display headings; Arial for body and diagrams. Font binaries are not bundled. Use the 4/8/12/16/24/32/48/64 spacing scale, left-aligned text and one clear reading axis. Body line height 1.45-1.65; limit paragraphs to comfortable reading widths. Rules separate sections; avoid decorative card grids.

## Layout and components
Use one main idea per page or slide. Place identification at top, primary content in the centre, evidence/status near the bottom. Buttons have 44px minimum touch area, visible keyboard focus and text labels. Circle navigation is a real selectable control; completed circles include a check and text count. Avoid purely decorative circular controls.

## Navigation and responsive behaviour
Subject > chapter > lesson > section > question. Keep Home and Back visible. At narrow widths stack columns, preserve reading order and allow equations/tables to scroll inside their own region. Do not hide essential text on mobile. Reader and Forge are distinct modes; source review belongs in Forge.

## Icons and diagrams
Use simple 2px strokes at 24px icon size; do not rely on unfamiliar symbols without labels. Diagrams use labelled blocks, direct arrows and short captions. Solid paths mean current software or V0 architecture; dashed paths mean proposed integration or future energy subsystem. Never draw fake PCB traces. Dimensions in concept views are explicit assumptions.

## Accessibility
Use strong text contrast, semantic headings, input labels, keyboard controls, descriptive image text, visible focus and live feedback. Do not infer WCAG compliance from appearance alone. Progress must be visible in text as well as graphics. Motion is limited and nonessential.

## Imagery and claims
Use actual software captures, editable technical drawings and accurately labelled hardware concepts. Retain dignified agency when showing learners. No invented documentary scenes. Do not claim deployment, partnership, autonomy, tested hardware or learning outcomes. No numerical energy or runtime claim until measured. Use 'prototype' for browser software and 'concept' for unbuilt hardware.
''')

# Future industrial envelope. Geometry is deliberately simple and reproducible.
def device(x=0,y=0,scale=1,rear=False,transparent=False):
 s=rect(0,0,760,480,'#2A2B30',INK,26)+rect(10,10,740,460,'#3A3B40','#75767C',20)
 for cx,cy in [(22,22),(738,22),(22,458),(738,458)]:s+=circ(cx,cy,5,'#0C0C0E','#999AA0')
 if rear:
  s+=rect(55,45,650,390,'#313238','#707178',12)+rect(115,108,530,260,'#3A3B40','#85868C',8)
  s+=txt(380,218,'ASTAR',44,'#ECEAE6','900','middle')+txt(380,256,'FUTURE ENCLOSURE CONCEPT',16,'#CCC9C4','400','middle')
  s+=rect(280,402,200,12,'#17181C','#808186',4)
 else:
  s+=rect(38,42,545,365,'#17181C','#15161A',10)+rect(53,57,515,335,'#E7E6DF','#9B9B95',4)
  s+=txt(52,446,'ASTAR',22,'#DDDBD7','900')
  for cx,cy,label in [(662,130,'UP'),(662,226,'DOWN'),(614,178,'LEFT'),(710,178,'RIGHT'),(662,178,'OK'),(630,324,'BACK'),(694,324,'HOME')]:
   s+=circ(cx,cy,21,'#25262B','#999AA0')+txt(cx,cy+4,label,9,'#E8E6E1','700','middle')
  s+=rect(602,388,110,4,PURPLE,PURPLE,2)
 return f'<g transform="translate({x},{y}) scale({scale})">{s}</g>'
save('PRODUCT/Renders/ASTAR-device-front.svg',svg(device(20,20),800,520,None,'ASTAR future seven-button device front concept'))
save('PRODUCT/Renders/ASTAR-device-rear.svg',svg(device(20,20,rear=True),800,520,None,'ASTAR future device rear concept'))
front=device(130,220,.95)+line(130,200,852,200)+line(130,188,130,212)+line(852,188,852,212)+txt(490,185,'190 mm / concept envelope',17,GRAY,'400','middle')
front+=line(890,220,890,676)+line(878,220,902,220)+line(878,676,902,676)+txt(920,440,'120 mm',17,GRAY)
front+=txt(940,488,'Seven controls',19,INK,'700')+txt(940,520,'Directional pad',16,GRAY)+txt(940,546,'Select / Back / Home',16,GRAY)
save('PRODUCT/Renders/01-front-view.svg',page('Front / future enclosure','A larger learning display remains a design proposal. V0 uses a 2.13-inch bench module.',front))
rear=device(130,220,.95,rear=True)+txt(930,300,'Rear service cover',20,INK,'700')+txt(930,336,'Access concept only',16,GRAY)+txt(930,418,'18 mm depth target',18,INK)+txt(930,454,'No fit validation',16,GRAY)
save('PRODUCT/Renders/02-rear-view.svg',page('Rear / future enclosure','190 x 120 x 18 mm is an assumed design envelope, not a verified mechanical drawing.',rear))
expl=''
for yy,color,label,n in [(230,'#222329','Front bezel + controls','01'),(330,'#E3E2DB','E-paper module / final size TBD','02'),(430,'#C5C5C8','Electronics carrier / proposed','03'),(530,'#DFDCD4','Storage space / chemistry TBD','04'),(630,'#303137','Rear enclosure + service cover','05')]:
 expl+=f'<g transform="translate(160,{yy}) skewX(-22) scale(1,.30)">'+rect(0,0,540,150,color,INK,14)+'</g>'
 expl+=line(720,yy+25,830,yy+25,LINE)+txt(855,yy+32,n+'  '+label,18,INK,'700')
expl+=line(425,211,425,706,GRAY,'5 7')
save('PRODUCT/Exploded-Views/03-exploded-concept.svg',page('Exploded assembly / future concept','Layer order and assembly strategy. All internal envelopes require component selection and clearance checks.',expl))
layout=rect(90,220,650,420,'#FAFAF8',INK,20)+rect(120,250,355,180,'#ECEBE6',INK,6)+txt(145,298,'E-paper backplane',25,INK,'700')+txt(145,333,'Final display not selected',17,GRAY)
layout+=rect(505,250,195,110,'#ECEBE6',INK,6)+txt(523,288,'Controller',20,INK,'700')+txt(523,321,'ESP32-S3 class',16,GRAY)
layout+=rect(505,390,195,95,'#ECEBE6',INK,6)+txt(523,431,'microSD',23,INK,'700')+txt(523,459,'Accessible edge',16,GRAY)
layout+=rect(120,462,355,140,'#FFFFFF',GRAY,6,'8 5')+txt(145,505,'Future energy storage',22,INK,'700')+txt(145,538,'Protected cell / dimensions TBD',16,GRAY)+txt(145,572,'Not installed in V0',16,GRAY)
layout+=txt(805,280,'Schematic placement',22,INK,'700')+txt(805,323,'No custom PCB designed',18,GRAY)+txt(805,358,'Clearances not validated',18,GRAY)+txt(805,393,'Thermal design not validated',18,GRAY)+txt(805,470,'V0 uses loose modules',20,INK,'700')+txt(805,506,'on a breadboard.',18,GRAY)
save('PRODUCT/Architecture/04-component-layout.svg',page('Component layout / future enclosure','Placement study only. Module geometry is symbolic and does not represent a bill of materials.',layout))

def block(x,y,w,h,title,detail='',future=False):
 b=rect(x,y,w,h,'#FFFFFF',GRAY if future else INK,0,'7 5' if future else '')+txt(x+18,y+35,title,22,INK,'700')
 for i,t in enumerate(detail.split('|')):
  if t:b+=txt(x+18,y+65+i*23,t,16,GRAY)
 return b
hw=block(65,240,240,130,'USB','V0 power + programming')+block(405,240,330,130,'ESP32-S3-DevKitC-1','Module development board')+line(305,305,405,305,arrow=True)
hw+=block(865,190,280,105,'E-paper','2.13-inch / SPI')+block(865,350,280,105,'microSD','SPI / separate chip select')+block(865,510,280,130,'Seven buttons','Up / Down / Left / Right|Select / Back / Home')
hw+=line(735,275,865,240,arrow=True)+line(735,320,865,398,arrow=True)+line(735,345,865,560,arrow=True)+txt(765,250,'SPI',14,GRAY)+txt(770,365,'SPI',14,GRAY)+txt(765,478,'GPIO',14,GRAY)
hw+=txt(65,492,'V0 is a USB-powered bench prototype',25,INK,'700')+txt(65,533,'No battery, solar system or custom PCB in this stage.',19,GRAY)+txt(65,577,'Pin allocation is incomplete: SD MISO is not specified.',19,GRAY)+txt(65,612,'Select exact module revisions before drawing a schematic.',19,GRAY)
save('PRODUCT/Architecture/05-hardware-v0.svg',page('Hardware architecture / V0','A development plan from the supplied build guide. Physical assembly and firmware are not verified.',hw,'V0 SPECIFICATION / BLOCK DIAGRAM ONLY / NOT WIRING INSTRUCTIONS'))
sw=''
for i,(a,b) in enumerate([('Capsule','Stable content IDs'),('Reader','Circle navigation'),('Lesson engine','Text / diagrams'),('Rule engine','Explicit answers')]):
 x=60+i*285;sw+=block(x,260,225,115,a,b)
 if i<3:sw+=line(x+225,317,x+285,317,arrow=True)
sw+=block(350,495,340,130,'Progress engine','Local records + export/import')+line(1030,375,1030,555)+line(1030,555,690,555,arrow=True)
sw+=txt(60,205,'BROWSER SOFTWARE',17,PURPLE,'700')+txt(65,678,'Embedded renderer, storage limits and fonts remain a separate integration task.',20,GRAY)
save('PRODUCT/Architecture/06-software.svg',page('Software architecture','Educational structure and rules are independent of the presentation surface.',sw,'BROWSER PROTOTYPE / HARDWARE FIRMWARE IS FUTURE WORK'))
pw=txt(60,222,'V0 / CURRENT HARDWARE PLAN',17,PURPLE,'700')+block(60,260,260,110,'USB supply','Board input')+line(320,315,405,315,arrow=True)+block(405,260,310,110,'Board regulation','Required logic rails')+line(715,315,800,315,arrow=True)+block(800,260,340,110,'Electronics','Controller / display / storage')
pw+=txt(60,460,'FUTURE / AFTER MEASURING ENERGY DEMAND',17,PURPLE,'700')
for i,(a,b) in enumerate([('Solar panel','Rating TBD'),('Charge + power path','Controller / protection TBD'),('Storage','Chemistry / capacity TBD'),('Regulated rails','Voltage / peak load TBD')]):
 x=60+i*285;pw+=block(x,495,225,130,a,b,True)
 if i<3:pw+=line(x+225,560,x+285,560,GRAY,'5 5',True)
pw+=txt(60,684,'No solar autonomy, runtime, charging performance or energy budget has been validated.',19,GRAY)
save('PRODUCT/Architecture/07-power-flow.svg',page('Power architecture','USB-powered V0 first; solar and storage are a later engineering programme.',pw,'NOT AN ELECTRICAL SCHEMATIC / NO UNVERIFIED CHARGING CIRCUIT SHOULD BE BUILT'))
cf=''
items=[('Source','Rights + page references'),('Structure','Chapters / sections'),('Review','Text / figures / questions'),('Map','Lesson and question IDs'),('Validate','Warnings + answer keys'),('Export','Offline package')]
for i,(a,b) in enumerate(items):
 row=i//3;col=i%3;x=60+col*385;y=240+row*230;cf+=block(x,y,310,120,a,b)
 if col<2:cf+=line(x+310,y+60,x+385,y+60,arrow=True)
cf+=line(985,360,985,413)+line(985,413,215,413)+line(215,413,215,470,arrow=True)
cf+=txt(60,675,'Forge preserves source pages. Automatic detection is a review aid, not a content-accuracy guarantee.',19,GRAY)
save('PRODUCT/Architecture/08-content-flow.svg',page('Educational content flow','The human review step protects original wording, source placement and assessment integrity.',cf,'FORGE / CONTENT PREPARATION PROTOTYPE'))
dc=block(60,330,310,150,'Shared content package','Subject / chapter / lesson IDs|Sections / questions / rules|Source references + assets')+block(595,220,500,130,'Browser reader','Rich layout / localStorage / standalone HTML')+block(595,480,500,150,'Embedded reader / planned','microSD / compact assets / local nonvolatile storage|E-paper paging / physical buttons',True)
dc+=line(370,370,595,285,arrow=True)+line(370,430,595,550,GRAY,'6 6',True)+txt(64,672,'A shared identifier contract is the goal; binary compatibility and device decoding are not yet tested.',19,GRAY)
save('PRODUCT/Architecture/09-device-content.svg',page('One curriculum / two readers','The browser and future device share content meaning; their rendering and storage formats may differ.',dc,'SOLID = BROWSER / DASHED = PROPOSED EMBEDDED INTEGRATION'))
shutil.copy2(r'D:\My_Command_Center\ASTAR\PRODUCT\Device Renders\ASTAR-assembled-concept.png',ROOT/'assets/design-references/legacy-three-button-render.png')
shutil.copy2(r'D:\My_Command_Center\ASTAR\PRODUCT\Exploded View\ASTAR-reference-exploded.png',ROOT/'assets/design-references/legacy-exploded-reference.png')
save('PRODUCT/HARDWARE_STATUS.md','''# Hardware source of truth

Read in full: supplied ASTAR_V0.1_Software_and_Hardware_Build_Guide.docx and ASTAR.pdf. The build guide governs the next prototype: ESP32-S3-DevKitC-1, 2.13-inch 250x122-class SPI e-paper, microSD module/card, seven buttons, USB power, breadboard/modules. It expressly defers solar, battery and custom PCB design.

The earlier pitch's ESP32-C3, price estimates, large display, solar illustration and three-button imagery describe an older vision. They are not the V0 build specification. Legacy renders are retained only in design references.

The new industrial concept assumes a 190 x 120 x 18 mm envelope with seven buttons and a larger future display. These are visual design choices, not measured fit, purchase specifications or manufacturable CAD. The exploded view and component layout are schematic. Exact large display, battery, charger, protective circuit, PCB and enclosure material are undecided. No device assembly, firmware, battery runtime, solar autonomy, environmental protection or drop performance was tested.

The supplied GPIO table is incomplete: microSD MISO is omitted. No wiring chart is supplied here. The official Espressif DevKitC-1 v1.0 guide confirms module-board architecture, exposed GPIO, USB power and board regulation, but exact board revision and module voltages must be selected before wiring. The guide's display example is a Pico-oriented module, so the exact ESP32-compatible SPI breakout/revision remains a procurement decision.

Official references checked 2026-11-02:
- https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.0.html
- https://www.waveshare.com/wiki/Pico-ePaper-2.13 (access returned 403; module figures retained only as supplied-guide specifications, not independently verified measurements)

Required engineering work: choose exact modules, complete pin mapping and schematic, inspect voltage compatibility, test USB-powered subsystems, implement minimal capsule reader, measure use-cycle energy, then select solar/storage/charging components. The 1 W panel in the guide is an untested hypothesis and is not used as a launch claim.
''')
save('assets/design-references/REFERENCE_LIBRARY.md','''# Design reference library

The source library already contained useful references; this launch builds on them rather than copying another brand. These local references are user-provided project material. Original assets remain untouched.

| Category | Source | Design lesson |
|---|---|---|
| Circular navigation | ../../SOFTWARE/Screenshots/ (new tested captures as delivered) and legacy ASTAR/SOFTWARE/Screenshots/09-lesson-circles.png | Circles select real learning units; number, title and completion state belong together. |
| Monochrome education | Legacy ASTAR/SOFTWARE/Demo/ASTAR-offline-demo.html | Readable text, direct navigation, minimal colour. |
| Textbook reading | Existing ASTAR source README and screenshots/04-reader.png | Preserve page images, source references, equations and figures. |
| E-paper | Supplied V0.1 guide; Waveshare reference URL in HARDWARE_STATUS.md | Small V0 display is a subsystem test, not the final textbook display. |
| Scientific diagrams | Supplied build guide block diagram | Label every module; distinguish signals and future power assumptions. |
| Editorial typography | C:/Users/ranji/Downloads/ASTAR.pdf | Large short headings, thin rules, clear reading axis. |
| Industrial design | legacy-exploded-reference.png | Separate enclosure, screen, controls and electronics; don't imply validated fit. |
| Product photography | legacy-three-button-render.png | Light studio background, tactile materials, restrained shadows. Old controls are not reused in new concept. |
| Brand identity | ../../BRAND/Logos/ASTAR-original.png | Strong wordmark and four-point star; new monochrome variants preserve the idea with simpler construction. |
| Presentation | Legacy ASTAR/PRESENTATION/ASTAR-Pitch-Deck.pptx | Alternating dark and light pages, one main idea, prominent product imagery. |

No third-party brand identity or stock child imagery was used. Existing generated product references are concept art, not photographs of a built device.
''')
print('Created vector product views, architecture and brand foundations.')
