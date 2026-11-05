import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from 'file:///C:/Users/ranji/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const root='D:/My_Command_Center/ASTAR-Finals';
process.env.RUNTIME_NODE_MODULES='C:/Users/ranji/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const slides=JSON.parse(await fs.readFile(path.join(root,'source/slides.json'),'utf8'));
const p=Presentation.create({slideSize:{width:1280,height:720}});
const ink='#181A27',purple='#7041C6',gray='#5D6070',pale='#F0EAF9';
function shape(s,x,y,w,h,fill,geometry='rect',stroke='none') {return s.shapes.add({geometry,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:stroke==='none'?0:1}})}
function txt(s,t,x,y,w,h,size=28,color=ink,bold=false){let a=shape(s,x,y,w,h,'none','textbox');a.text=t;a.text.style={typeface:'Arial',fontSize:size,color,bold};a.text.insets=0;return a;}
async function img(s,name,x,y,w,h){const b=await fs.readFile(path.join(root,'assets',name));s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/png',position:{left:x,top:y,width:w,height:h},fit:'contain',alt:name});}
for(let i=0;i<slides.length;i++){
 const d=slides[i],s=p.slides.add();s.background.fill='#FFFFFF';s.speakerNotes.text=d.notes+'\nSource: user-supplied ASTAR brief and ASTAR.pdf. Software evidence: local ASTAR README.md and test-results screenshots. Hardware illustration is conceptual.';
 shape(s,64,52,44,5,purple);txt(s,'ASTAR',116,42,150,28,18,gray,true);txt(s,String(i+1).padStart(2,'0'),1150,657,60,24,16,gray);
 if(d.kind==='cover'){
   await img(s,'ASTAR-original-logo.png',52,95,680,227);
   txt(s,d.title,64,340,1130,185,65,ink,true);
   txt(s,'Autonomous Solar Tutoring and Resource System',68,567,1060,45,25,purple);
 }else if(d.kind==='close'){
   txt(s,d.title,64,150,1080,170,66,ink,true);shape(s,64,352,300,6,purple);
   txt(s,d.body,64,405,1090,150,30,purple);await img(s,'ASTAR-original-logo.png',850,570,350,117);
 }else{
   txt(s,d.title,64,111,1140,110,48,ink,true);
   if(d.kind==='image'){
     txt(s,d.body,64,250,360,260,27,gray);await img(s,d.image,454,240,750,390);
     txt(s,'Existing software / saved development screenshot',454,639,740,25,15,gray);
   }else if(d.kind==='system'){
     const items=[['01','ASTAR device','Proposed solar-powered\neducational hardware'],['02','ASTAR software','Offline lessons, practice\nand local progress'],['03','ASTAR Forge','Content preparation,\nreview and export']];
     items.forEach((a,j)=>{let x=64+j*390;shape(s,x,263,62,62,pale,'ellipse');txt(s,a[0],x+15,277,46,40,27,purple,true);txt(s,a[1],x,362,355,60,30,ink,true);txt(s,a[2],x,442,355,140,27,gray);});
   }else if(d.kind==='hardware'){
     txt(s,d.body,64,259,695,300,30,gray);
     shape(s,845,247,285,344,ink,'roundRect');shape(s,864,270,247,245,'#F5F3F8');txt(s,'ASTAR',885,290,210,40,25,purple,true);txt(s,'01  SCIENCE\n\nLight and life\n\nRead. Try. Learn.',885,345,205,150,22,ink);
     for(let j=0;j<3;j++)shape(s,908+j*62,544,25,25,purple,'ellipse');
     txt(s,'Device design concept',846,616,330,30,17,gray);
   }else if(d.kind==='pricing'){
     [['INR 3,700','Founder target unit cost'],['INR 4,700','Founder target institutional price']].forEach((a,j)=>{let x=64+j*600;txt(s,a[0],x,288,550,105,74,purple,true);txt(s,a[1],x,418,550,70,28,ink);});
     txt(s,'Unvalidated estimates. Full component, logistics and support costs remain to be established.',64,570,1140,70,23,gray);
   }else txt(s,d.body,64,263,1090,330,34,gray);
 }
}
for(let i=0;i<p.slides.items.length;i++){
 const png=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(root,'preview',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const draft=path.join(root,'source/candidate.pptx');await(await PresentationFile.exportPptx(p)).save(draft);
const skill='C:/Users/ranji/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({workspaceDir:root,candidatePath:draft,finalPath:path.join(root,'deliverables/11-ASTAR-pitch.pptx'),pythonExecutable:'C:/Users/ranji/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(root,'source/deck-validation.json')});
console.log(JSON.stringify(result));
