import fs from 'node:fs/promises';
import { constants } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from 'file:///C:/Users/ranji/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

// Native editable slide objects. The screenshots and product views are images.
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../..');
const out=path.join(root,'PRESENTATION/Exports');
const preview=path.join(here,'preview');
const build=path.join(here,'.build');
for(const d of [out,preview,build]) await fs.mkdir(d,{recursive:true});
process.env.RUNTIME_NODE_MODULES='C:/Users/ranji/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const p=Presentation.create({slideSize:{width:1440,height:810}});
const C={ink:'#0C0C0E',paper:'#F0ECE4',purple:'#6852FF',light:'#C9C4CC',dark:'#5A575E',line:'#BBB6B0'};
const screenshot=n=>path.join(root,'SOFTWARE/Screenshots',n);
const old=path.resolve(root,'../ASTAR');
const originalLogo=path.join(old,'BRAND/Logo/ASTAR-original.png');
const futureHero=path.join(old,'PRODUCT/Device Renders/ASTAR-assembled-concept.png');
const nativeText=[];
function rect(s,x,y,w,h,fill,line='none',width=0){return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:line,width}});}
function text(s,str,x,y,w,h,size=28,color=C.ink,bold=false,head=false){
 const z=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 z.text=str;z.text.style={typeface:head?'Arial Black':'Arial',fontSize:size,color,bold};z.text.insets=0;
 nativeText.push({slide:p.slides.items.length,text:str});return z;
}
function rule(s,x,y,w,color=C.line){rect(s,x,y,w,1,color);}
async function image(s,fp,x,y,w,h,alt){
 const b=await fs.readFile(fp);s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/png',position:{left:x,top:y,width:w,height:h},fit:'contain',alt});
}
function slide(title,dark=false,sub=''){
 const s=p.slides.add();s.background.fill=dark?C.ink:C.paper;
 s._fg=dark?C.paper:C.ink;s._muted=dark?C.light:C.dark;
 text(s,'ASTAR',64,31,250,28,17,dark?C.paper:C.ink,true);
 text(s,String(p.slides.items.length).padStart(2,'0'),1310,31,66,28,17,s._muted);
 if(title)text(s,title,64,110,1300,134,56,s._fg,true,true);
 if(sub)text(s,sub,66,245,1280,78,26,s._muted);
 return s;
}
function note(s,str){s.speakerNotes.text=str;}
function label(s,str,x,y,w=450){text(s,str,x,y,w,32,18,C.purple,true);}
function row(s,n,title,body,y){
 rule(s,66,y-15,1308,s._fg===C.paper?'#49464E':C.line);
 text(s,n,66,y+5,72,50,24,C.purple,true);
 text(s,title,160,y,380,65,32,s._fg,true);
 text(s,body,585,y,760,85,28,s._muted);
}
function node(s,title,body,x,y,w,h=130,dark=false){
 rect(s,x,y,w,h,'none',dark?'#79757E':'#8C878A',1.5);
 text(s,title,x+22,y+18,w-44,40,25,dark?C.paper:C.ink,true);
 text(s,body,x+22,y+62,w-44,h-68,21,dark?C.light:C.dark);
}
function arrow(s,x,y,w,color=C.purple){rect(s,x,y,w-12,2,color);text(s,'›',x+w-22,y-23,28,50,40,color);}

// 01: identity and mission, without an invented hardware claim.
{
 const s=slide('');
 await image(s,originalLogo,62,130,580,194,'Original ASTAR wordmark and star symbol');
 text(s,'Learning should not\ndepend on infrastructure.',64,365,1260,220,68,C.ink,true,true);
 text(s,'Autonomous Solar Tutoring and Resource System',68,668,1250,50,26,C.dark);
 note(s,'Mission and expanded name from the launch brief. Original user-supplied ASTAR Geometric Star Logo.png preserved unchanged. Product development initiative: software prototype; hardware remains under development.');
}
// 02: problem, without unsourced statistics.
{
 const s=slide('Learning needs continuity',true,'A textbook, a teacher and time to practise still matter when infrastructure is unreliable.');
 row(s,'01','Electricity','Charging can become uncertain.',365);
 row(s,'02','Connectivity','Online-only lessons become difficult to reach.',492);
 row(s,'03','Access to support','Students need a way to keep studying between teaching sessions.',619);
 note(s,'Problem framing from the user brief. No prevalence, field-study or measured impact claim is made. ASTAR is intended to complement teachers and schools.');
}
// 03: design constraints.
{
 const s=slide('Design for the missing connection');
 label(s,'WHEN LEARNING DEPENDS ON',66,290,520);label(s,'ASTAR\'S DESIGN RESPONSE',722,290,600);
 const pairs=[['A live connection','Carry reviewed content locally.'],['A general-purpose device','Focus the interface on reading and practice.'],['A one-time download','Keep lessons structured and progress portable.']];
 pairs.forEach(([a,b],i)=>{const y=365+i*119;rule(s,66,y-24,1308);text(s,a,66,y,580,74,30,C.ink,true);text(s,b,722,y,620,85,30,C.dark);});
 note(s,'These are design choices, not comparative performance findings. The browser reader already exports a standalone HTML course; the proposed device needs separate firmware and measured power testing.');
}
// 04: system and exploratory industrial concept.
{
 const s=slide('One learning system');
 await image(s,futureHero,608,260,768,512,'Exploratory solar device concept; not the V0 prototype');
 label(s,'PREPARE',66,285);text(s,'Forge structures source material\nfor review and export.',66,324,510,100,29,C.ink);
 label(s,'LEARN',66,453);text(s,'The offline reader keeps the\ntextbook at the centre.',66,492,510,100,29,C.ink);
 label(s,'DEVELOP',66,620);text(s,'A dedicated device follows\nmeasured hardware testing.',66,659,510,95,29,C.ink);
 text(s,'Exploratory future form. Display and controls differ from V0.',644,743,730,40,17,C.dark);
 note(s,'Sources: current Python/vanilla JavaScript textbook studio; ASTAR V0.1 Software and Hardware Build Guide; original ASTAR concept render. Render is an exploratory future industrial concept, not a photograph of built hardware, not a V0 representation, and not evidence of solar autonomy.');
}
// 05: canonical V0 boundary with editable native component relationships.
{
 const s=slide('The first hardware milestone',true,'V0 is a USB-powered test assembly. Prove the reading loop before adding solar charging.');
 node(s,'ESP32-S3-DevKitC-1','Controller and USB power',530,372,360,144,true);
 node(s,'2.13-inch e-paper','250 × 122 class · SPI',66,372,370,144,true);
 node(s,'microSD','16–32 GB · local content',983,372,390,144,true);
 arrow(s,436,440,94);arrow(s,890,440,93);
 node(s,'Seven physical buttons','Up / Down / Left / Right / Select / Back / Home',370,598,700,112,true);
 rect(s,709,516,2,82,C.purple);
 text(s,'Modules and breadboard first. No battery, solar circuit or custom PCB in V0.',66,745,1300,32,20,C.light);
 note(s,'Canonical source: ASTAR_V0.1_Software_and_Hardware_Build_Guide.docx, hardware list and non-goals. The guide specifies a USB-powered ESP32-S3-DevKitC-1, 2.13-inch 250x122-class SPI e-paper, SPI microSD 16–32GB, and seven buttons. Native diagram describes the proposed assembly. No board, wiring or physical firmware test is claimed.');
}
// 06: screenshot from current runnable demonstration.
{
 const s=slide('A clear route into a lesson',true);
 text(s,'Choose a subject.\nOpen a chapter.\nFollow the numbered lessons.',66,290,420,210,31,C.paper);
 text(s,'Completion and resume state\nstay in this browser.',66,590,420,100,25,C.light);
 await image(s,screenshot('01-subject-home.png'),520,262,854,480,'Actual ASTAR subject home screenshot');
 note(s,'Source: launch browser demonstration, freshly captured in SOFTWARE/Screenshots/01-subject-home.png. The sample content is original authored demonstration material, not a full curriculum. Local progress can be lost if browser data is cleared; export backups.');
}
// 07: actual reader and assessment screenshots.
{
 const s=slide('Read the textbook. Work the question.');
 await image(s,screenshot('02-lesson-reader.png'),65,272,644,402,'Actual lesson with text, example and diagram');
 await image(s,screenshot('03-assessment.png'),735,272,640,402,'Actual assessment and feedback');
 text(s,'Text, examples and diagrams\nkeep their place in the lesson.',66,700,630,72,26,C.ink);
 text(s,'Checked answers receive feedback.\nOpen responses stay ungraded.',735,700,640,72,26,C.ink);
 note(s,'Sources: launch reader screenshots, original ASTAR demonstration textbook and explicit assessment answer keys. Existing source-PDF imports preserve original page views; automatic extraction is imperfect. No original textbook question is invented or falsely attributed. Open responses are not treated as authoritative automated grades.');
}
// 08: Forge.
{
 const s=slide('Forge prepares content for review',true);
 text(s,'Source → structure → review\n→ mapping → validation → export',66,269,1270,66,28,C.paper);
 await image(s,screenshot('04-forge-review.png'),66,354,850,400,'Actual ASTAR Forge review screen');
 text(s,'Inspect the source.\nCorrect the structure.\nCheck figures and questions.',970,372,400,200,29,C.paper);
 text(s,'Warnings prioritise review.\nThey do not certify\nteaching accuracy.',970,628,400,116,24,C.light);
 note(s,'Source: canonical ASTAR textbook studio under 02 - Projects/astar and preserved launch application. It provides PDF extraction, source page imagery, manual editing, triage, and package/HTML export. Heuristics and OCR are not guaranteed; permissions and educational review remain necessary. Screenshot is a fresh launch capture.');
}
// 09: structured educational content and two runtimes.
{
 const s=slide('Shared content, separate runtimes');
 node(s,'Reviewed educational package','Stable chapter, lesson and question identifiers',420,274,600,133);
 rect(s,719,407,2,70,C.purple);rect(s,312,477,815,2,C.purple);rect(s,312,477,2,55,C.purple);rect(s,1125,477,2,55,C.purple);
 node(s,'Browser reader','Implemented: reading, practice, local progress',66,532,600,145);
 node(s,'Device adapter + firmware','Planned: paged content and physical controls',774,532,600,145);
 text(s,'A portable content model does not make browser HTML into microcontroller firmware.',66,730,1308,45,25,C.dark);
 note(s,'Architecture proposal based on current course JSON identifiers and the V0.1 guide content-pack direction. Browser and firmware can share source identifiers; device rendering, pagination, memory limits, fonts and filesystem packaging require a separate adapter and verification. The current standalone HTML is a browser artifact.');
}
// 10: power architecture, no numerical runtime speculation.
{
 const s=slide('Solar is a later engineering milestone',true);
 label(s,'CURRENT V0 TARGET',66,279,620);text(s,'USB → ESP32-S3 + display + storage',66,324,1240,60,33,C.paper,true);
 label(s,'PROPOSED LATER POWER PATH',66,460,700);
 node(s,'Solar panel','Selected after measurements',66,513,280,129,true);arrow(s,346,578,55);
 node(s,'Charge + protection','Compatible power management',401,513,300,129,true);arrow(s,701,578,55);
 node(s,'Battery','Chemistry and capacity TBD',756,513,280,129,true);arrow(s,1036,578,55);
 node(s,'Regulated load','Controller, display, storage',1091,513,284,129,true);
 text(s,'Measure sleep current, refresh energy and charging losses before claiming autonomy.',66,718,1308,62,26,C.light);
 note(s,'The V0.1 guide explicitly excludes battery and solar from V0. Later path is a functional concept, not a schematic or approved component design. No battery chemistry, capacity, charge IC, panel rating, daily energy budget or runtime has been validated. Charger design must match the selected battery and panel; power path/protection and charging limits need engineering review.');
}
// 11: intended use model.
{
 const s=slide('Designed to support teaching');
 row(s,'01','Learners','Students who need structured study when power or connectivity is unreliable.',300);
 row(s,'02','Facilitators','Teachers who select content, explain difficult ideas and review open responses.',450);
 row(s,'03','Potential collaborators','Education organisations and NGOs that could help design and evaluate a pilot.',600);
 text(s,'Intended users and prospective partner types. No partnerships or deployments are claimed.',66,752,1308,30,18,C.dark);
 note(s,'Intended users and potential deployment channels come from the brief. There are no confirmed partnerships, learner trials, deployment statistics, measured learning outcomes, funding or certification claims in this deck.');
}
// 12: development milestones, not dated commitments.
{
 const s=slide('The development sequence',true);
 const steps=[['01','Complete the software loop','Review a small course and test offline reading, practice and progress.'],['02','Validate V0 hardware','Load one content pack, navigate with seven buttons and measure power.'],['03','Develop the power system','Choose charging components and enclosure using measured requirements.'],['04','Design a supervised pilot','Agree content, safeguarding, support and evaluation with educators.']];
 steps.forEach(([n,h,b],i)=>row(s,n,h,b,292+i*115));
 note(s,'Proposed development gates, not completed milestones or contractual dates. Five-day asset production is tracked separately in the launch master plan. Hardware, curriculum validation and real-world deployment cannot be asserted from producing a presentation package.');
}
// 13: direct disclosure of maturity.
{
 const s=slide('What exists, and what comes next');
 label(s,'WORKING SOFTWARE PROTOTYPE',66,280,650);label(s,'DESIGNED / NOT YET VALIDATED',751,280,650);
 text(s,'Local content preparation\nOffline browser learning\nAuthored practice and saved progress\nEditable launch assets',66,342,610,260,31,C.ink);
 text(s,'V0 hardware assembly and firmware\nSolar charging and battery runtime\nField durability and learner trials\nPartnerships and deployment model',751,342,620,260,31,C.ink);
 rule(s,66,660,1308);
 text(s,'A focused prototype demonstrates the experience. It does not establish learning outcomes or device autonomy.',66,695,1275,80,29,C.dark);
 note(s,'Implementation and software validation evidence are recorded in the launch SOFTWARE QA files and VALIDATION_REPORT.md. See those reports for actual tests and limits. No hardware implementation, solar autonomy, field deployment or measured educational impact is claimed.');
}
// 14: close.
{
 const s=slide('',true);
 text(s,'The next lesson\nshould remain\nwithin reach.',64,165,1290,354,90,C.paper,true,true);
 text(s,'ASTAR',66,583,1280,72,56,C.purple,true,true);
 text(s,'Explore the prototype. Help shape the first tested device.',68,698,1280,56,30,C.light);
 note(s,'Closing invitation for technical and educational collaboration. No contact details or destination URL is invented. Present the local offline demonstration alongside the deck.');
}

// Both the PPTX and PDF originate from the same live presentation object.
for(const [i,s] of p.slides.items.entries()){
 const png=await p.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(preview,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
await fs.writeFile(path.join(here,'slide-text.json'),JSON.stringify(nativeText,null,2));
await fs.writeFile(path.join(here,'speaker-notes.md'),p.slides.items.map((s,i)=>`## ${String(i+1).padStart(2,'0')}\n\n${s.speakerNotes.text}`).join('\n\n'));
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
const skill='C:/Users/ranji/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
const final=path.join(out,'ASTAR-Company-Presentation.pptx');
try{
 const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:'C:/Users/ranji/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','13716000,7715250','--validate-heading-fit'],explicitTotalSlideCount:14,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:['Arial','Arial Black']},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
 console.log(result);
}catch(e){
 if(e.code==='EPERM'&&e.syscall==='link'){
  await fs.copyFile(candidate,final,constants.COPYFILE_EXCL);
  await fs.writeFile(path.join(build,'copy-note.txt'),'Validation and reimport completed; Windows rejected final hardlink. Candidate copied unchanged using exclusive copy.\n');
 }else throw e;
}
// PDF runtime export is attempted first. The source also supports an image-PDF fallback.
try{
 const pdf=await p.export({format:'pdf'});
 await fs.writeFile(path.join(out,'ASTAR-Company-Presentation.pdf'),new Uint8Array(await pdf.arrayBuffer()));
}catch(e){console.log('PDF export unavailable; use build_pdf.py:',e.message);}
console.log('14 slides rendered and editable PPTX exported.');
