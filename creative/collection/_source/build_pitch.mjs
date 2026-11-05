import fs from 'node:fs/promises';
import {constants} from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from 'file:///C:/Users/ranji/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const root='D:/My_Command_Center/ASTAR';
process.env.RUNTIME_NODE_MODULES='C:/Users/ranji/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const data=JSON.parse(await fs.readFile(root+'/_source/scenes.json','utf8'));
const p=Presentation.create({slideSize:{width:1440,height:810}});
const ink='#0C0C0E',paper='#F0ECE4',purple='#6852FF';
function box(s,x,y,w,h,c){return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill:c,line:{fill:'none',width:0}})}
function t(s,txt,x,y,w,h,size,col,bold=false,head=false){const z=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});z.text=txt;z.text.style={typeface:head?'Arial Black':'Arial',fontSize:size,color:col,bold};z.text.insets=0;}
async function im(s,fp,x,y,w,h){const b=await fs.readFile(fp);s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/png',position:{left:x,top:y,width:w,height:h},fit:'contain',alt:'ASTAR '+path.basename(fp)});}
for(const [i,d] of data.entries()){
const s=p.slides.add();s.background.fill=d.dark?ink:paper;const fg=d.dark?paper:ink,mu=d.dark?'#AAA5AE':'#625D63';
t(s,'ASTAR / AUTONOMOUS SOLAR TUTORING AND RESOURCE SYSTEM',65,32,1050,25,11,purple,true);t(s,'ASTAR / 2026',1230,32,150,25,11,mu);
if(d.kind==='cover'){
 t(s,'ASTAR',64,212,1280,250,210,fg,true,true);t(s,'LEARNING WHEN',70,455,1280,88,65,fg,true,true);t(s,'INFRASTRUCTURE FAILS',70,536,1300,88,65,purple,true,true);
}else{
 t(s,d.title,65,96,1320,72,49,fg,true,true);t(s,d.accent,65,155,1320,72,49,purple,true,true);
 if(d.kind==='image'){
  await im(s,d.image,560,245,815,440);t(s,d.body,65,294,430,300,28,mu);
  if([3,4].includes(i))t(s,'DESIGN CONCEPT / SUBJECT TO VALIDATION',560,700,820,25,13,mu,true);
 }else if(d.cols){
  const cw=1310/d.cols.length;
  d.cols.forEach(([a,b],j)=>{let x=65+j*cw;box(s,x,320,cw-28,1,d.dark?'#4B4850':'#B8B1AC');t(s,a,x,345,cw-30,50,22,purple,true);t(s,b,x,407,cw-38,165,30,fg);});
  if(d.body)t(s,d.body,65,605,1280,90,23,mu);
 }else if(d.kind==='close'){
  t(s,d.body,65,363,1070,170,34,fg);await im(s,root+'/BRAND/Logo/ASTAR-original.png',65,510,550,184);
 }
}
box(s,65,749,1310,1,d.dark?'#4B4850':'#B8B1AC');t(s,`${String(i+1).padStart(2,'0')} / ${data.length}`,65,762,150,25,12,mu);
s.speakerNotes.text=(d.notes||'Explain the intended product and development stage.')+'\nSources: user-supplied ASTAR.pdf and brief; local ASTAR software and tests. Generated hardware image is a design concept. Fonts substituted with Arial Black and Arial for local editability.';
}
for(let i=0;i<p.slides.items.length;i++){const b=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(root+`/_preview/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await b.arrayBuffer()));}
const candidate=root+'/_source/candidate.pptx',final=root+'/PRESENTATION/ASTAR-Pitch-Deck.pptx';await(await PresentationFile.exportPptx(p)).save(candidate);
const skill='C:/Users/ranji/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
try{
const r=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:'C:/Users/ranji/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','13716000,7715250','--validate-heading-fit'],fontPolicy:{basis:'design',families:['Arial','Arial Black']},verifyArtifactToolImport:true,receiptPath:root+'/_source/pitch-validation.json'});console.log(r);
}catch(e){if(e.code==='EPERM'&&e.syscall==='link'){await fs.copyFile(candidate,final,constants.COPYFILE_EXCL);await fs.writeFile(root+'/_source/pitch-validation.txt','Finalizer completed validation and import checks, then Windows denied its final hardlink. Copied the validated candidate unchanged.\n');console.log('Validated file copied after Windows hardlink limitation.');}else throw e;}
