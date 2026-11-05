import * as T from 'three';
import {RoundedBoxGeometry} from './vendor/RoundedBoxGeometry.js';
import {parts} from './parts.js';

export function buildDevice() {
  const root = new T.Group(); root.name='ASTAR engineering concept (millimetres)';
  const groups = new Map();
  const materials={
    shell:new T.MeshStandardMaterial({color:0x1d211f,roughness:.37,metalness:.22}),
    dark:new T.MeshStandardMaterial({color:0x222129,roughness:.65}),
    rubber:new T.MeshStandardMaterial({color:0x242724,roughness:.88}),
    pcb:new T.MeshStandardMaterial({color:0x142c25,roughness:.48,metalness:.16}),
    blue:new T.MeshStandardMaterial({color:0x15251f,roughness:.58,metalness:.1}),
    metal:new T.MeshStandardMaterial({color:0xa5acb6,metalness:.88,roughness:.27}),
    foil:new T.MeshStandardMaterial({color:0xb9bac0,metalness:.72,roughness:.43}),
    gold:new T.MeshStandardMaterial({color:0xb89b57,metalness:.78,roughness:.3}),
    ink:new T.MeshStandardMaterial({color:0x10121a,roughness:.58}),
    purple:new T.MeshStandardMaterial({color:0x9474c1,roughness:.6}),
    red:new T.MeshStandardMaterial({color:0x8a4b4d,roughness:.65}),
    insulation:new T.MeshStandardMaterial({color:0x9d8253,roughness:.85}),
    solar:new T.MeshPhysicalMaterial({color:0x182432,metalness:.35,roughness:.2,clearcoat:.65}),
  };
  function part(id,p=[0,0,0],e=[0,0,0]){const g=new T.Group();g.name=parts.find(x=>x.id===id).name;g.userData={partId:id};g.position.fromArray(p);g.userData.base=p;g.userData.explode=e;groups.set(id,g);root.add(g);return g;}
  function mesh(g,geo,mat,p=[0,0,0]){const m=new T.Mesh(geo,mat.clone());m.position.fromArray(p);m.name=g.name;m.userData.partId=g.userData.partId;m.castShadow=true;m.receiveShadow=true;g.add(m);return m;}
  function box(g,w,h,d,mat,p=[0,0,0],r=.4){return mesh(g,new RoundedBoxGeometry(w,h,d,2,Math.min(r,w/3,h/3,d/3)),mat,p);}
  function cylinder(g,r,h,mat,p,inner=0){if(inner){const s=new T.Shape();s.absarc(0,0,r,0,Math.PI*2,false);const hole=new T.Path();hole.absarc(0,0,inner,0,Math.PI*2,true);s.holes.push(hole);const geo=new T.ExtrudeGeometry(s,{depth:h,bevelEnabled:false,curveSegments:16});geo.translate(0,0,-h/2);return mesh(g,geo,mat,p);}const m=mesh(g,new T.CylinderGeometry(r,r,h,24),mat,p);m.rotation.x=Math.PI/2;return m;}
  function roundedPath(w,h,r,x=0,y=0,Path=T.Shape){const s=new Path(),l=x-w/2,b=y-h/2;r=Math.min(r,w/2,h/2);s.moveTo(l+r,b);s.lineTo(l+w-r,b);s.quadraticCurveTo(l+w,b,l+w,b+r);s.lineTo(l+w,b+h-r);s.quadraticCurveTo(l+w,b+h,l+w-r,b+h);s.lineTo(l+r,b+h);s.quadraticCurveTo(l,b+h,l,b+h-r);s.lineTo(l,b+r);s.quadraticCurveTo(l,b,l+r,b);return s;}
  function frame(g,w,h,iw,ih,d,mat,p=[0,0,0],r=5,innerY=0,holes=[]){const s=roundedPath(w,h,r);s.holes.push(roundedPath(iw,ih,Math.min(3,r),0,innerY,T.Path));for(const [x,y,rad] of holes){const hole=new T.Path();hole.absarc(x,y,rad,0,Math.PI*2,true);s.holes.push(hole);}const geo=new T.ExtrudeGeometry(s,{depth:d,bevelEnabled:true,bevelThickness:.15,bevelSize:.15,bevelSegments:2,curveSegments:12});geo.translate(0,0,-d/2);return mesh(g,geo,mat,p);}
  function wire(g,points,mat,r=.35){return mesh(g,new T.TubeGeometry(new T.CatmullRomCurve3(points.map(p=>new T.Vector3(...p))),24,r,7,false),mat);}
  function label(g,text,w,h,p,{bg='#dddce0',fg='#323039',size=40,back=false}={}){const c=document.createElement('canvas');c.width=512;c.height=Math.max(64,Math.round(512*h/w));const ctx=c.getContext('2d');ctx.fillStyle=bg;ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle=fg;ctx.font=`600 ${size}px Arial`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,256,c.height/2,480);const tex=new T.CanvasTexture(c);tex.colorSpace=T.SRGBColorSpace;tex.anisotropy=4;const m=mesh(g,new T.PlaneGeometry(w,h),new T.MeshStandardMaterial({map:tex,roughness:.8}),p);if(back)m.rotation.y=Math.PI;return m;}
  function chip(g,w,h,p){box(g,w,h,.8,materials.ink,p,.2);for(let i=0;i<Math.floor(h/1.6);i++)for(const x of [-1,1])box(g,.7,.35,.25,materials.metal,[p[0]+x*(w/2+.25),p[1]-h/2+.7+i*1.6,p[2]-.15],.08);}
  function pcb(g,w,h){box(g,w,h,1.3,materials.pcb,[0,0,0],.5);for(const x of [-w/2+2,w/2-2])for(const y of [-h/2+2,h/2-2])cylinder(g,1,.15,materials.gold,[x,y,.73],.52);}
  const front=part('front',[0,0,10],[0,12,94]);
  frame(front,124,90,96.8,74.8,2,materials.shell,[0,0,0],6,4,[[-15,-39,3],[0,-39,3],[15,-39,3],[49,-38,1.7]]);
  frame(front,124,90,120,86,8.4,materials.shell,[0,0,-5.4],6);
  label(front,'ASTAR',17,3.2,[-42,-39,1.19],{bg:'#353936',fg:'#b8bdb8',size:65});
  label(front,'RESET',6,1.4,[49,-42,1.19],{bg:'#353936',fg:'#b8bdb8',size:55});
  for(const x of [-56,56])for(const y of [-38,38]){cylinder(front,1.8,.2,materials.metal,[x,y,1.15],.8);box(front,5,8,2,materials.dark,[x+(x<0?-2:2),y,0],.8);}
  for(const x of [-59,59])for(const y of [-40,40]){box(front,7,8,7,materials.dark,[x,y,-3],1);cylinder(front,1.65,.25,materials.metal,[x,y,.7],.85);}
  for(const x of [-61.7,61.7])for(const y of [-27,-9,9,27])box(front,1,4,7,materials.rubber,[x,y,-4],.3);
  const rear=part('rear',[0,0,-11],[0,-7,-67]);
  const trayShape=roundedPath(124,90,6);const trayGeometry=new T.ExtrudeGeometry(trayShape,{depth:2,bevelEnabled:true,bevelSize:.35,bevelThickness:.2,bevelSegments:2,curveSegments:14});trayGeometry.translate(0,0,-1);mesh(rear,trayGeometry,materials.shell);
  // Tray walls leave two bottom USB clearances and one side switch clearance.
  box(rear,120,2,9,materials.shell,[0,44,5.5]);box(rear,2,86,9,materials.shell,[-61,0,5.5]);
  box(rear,2,47,9,materials.shell,[61,-19.5,5.5]);box(rear,2,22,9,materials.shell,[61,33,5.5]);
  for(const [x,w] of [[-48,24],[-8,30],[40,40]])box(rear,w,2,9,materials.shell,[x,-44,5.5]);
  for(const x of [-54,54])box(rear,1.5,65,4,materials.shell,[x,0,3]);
  for(const x of [-56,56])for(const y of [-38,38])cylinder(rear,3,4,materials.shell,[x,y,3],1);
  const bumper=part('bumper',[0,0,.5],[0,0,1]);frame(bumper,127,93,124,90,3.5,materials.rubber,[0,0,0],7);
  const bezel=part('bezel',[0,4,9.5],[0,8,76]);frame(bezel,96,74,84.8,63.6,1.5,materials.dark,[0,0,0],2.5);
  const panel=part('panel',[0,4,7.7],[0,5,55]);box(panel,91,69.8,1.2,materials.foil);
  const screen=document.createElement('canvas');screen.width=800;screen.height=600;
  const ctx=screen.getContext('2d');ctx.fillStyle='#dbddd2';ctx.fillRect(0,0,800,600);ctx.fillStyle='#313630';ctx.font='600 25px Arial';ctx.fillText('ASTAR',42,52);ctx.font='18px Arial';ctx.fillText('MATHEMATICS  /  UNIT 02',430,52);ctx.fillRect(42,77,716,2);ctx.font='20px Arial';ctx.fillText('LESSON 03     ·     30 MINUTES',42,123);ctx.font='bold 49px Georgia';ctx.fillText('A different angle.',42,194);ctx.font='24px Georgia';ctx.fillText('Explore the relationships within a triangle.',42,241);ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(272,438);ctx.lineTo(434,286);ctx.lineTo(568,438);ctx.closePath();ctx.strokeStyle='#313630';ctx.stroke();ctx.font='23px Georgia';ctx.fillText('A',251,468);ctx.fillText('B',429,273);ctx.fillText('C',574,468);ctx.font='20px Arial';ctx.fillText('Think. What do the three angles add up to?',42,523);ctx.fillRect(42,549,716,1);ctx.font='17px Arial';ctx.fillText('OFFLINE LESSON LIBRARY',42,579);ctx.fillText('03 / 12',690,579);
  const screenTex=new T.CanvasTexture(screen);screenTex.colorSpace=T.SRGBColorSpace;screenTex.anisotropy=8;
  mesh(panel,new T.PlaneGeometry(84.8,63.6),new T.MeshStandardMaterial({map:screenTex,roughness:.95}),[0,0,.63]);
  // Flex tail folds behind the screen, inside the board outline.
  wire(panel,[[-41,-22,-.4],[-45,-24,-1],[-47,-22,-2.3],[-44,-18,-2.3]],materials.insulation,1.4);
  const display=part('display-board',[0,2,4.7],[0,1,32]);pcb(display,103,78.5);chip(display,10,6,[38,-30,-1.15]);
  label(display,'WAVESHARE  4.2 E-PAPER',54,4,[0,-31,-.77],{bg:'#164842',fg:'#c7d2c4',size:29,back:true});
  for(let i=0;i<8;i++)box(display,.55,2,3,materials.gold,[-11+i*2.54,34,-2]);
  const esp=part('esp32',[-27,3,-4.3],[-24,9,10]);pcb(esp,25,55);
  box(esp,18,18,2.7,materials.metal,[0,10,2],.7);label(esp,'ESP32-S3',15,4,[0,10,3.39],{bg:'#a5acb6',fg:'#333c43',size:44});
  box(esp,18,8,1,materials.ink,[0,23,1.3]);for(let j=0;j<5;j++)box(esp,12,.22,.12,materials.gold,[0,20.2+j,1.86],.03);
  chip(esp,6,6,[0,-7,1.2]);chip(esp,4,4,[2,-17,1.2]);
  for(let side of [-1,1]){box(esp,2.4,48,2.5,materials.ink,[side*11,0,-1.9]);for(let j=0;j<19;j++)box(esp,.55,.55,5,materials.gold,[side*11,-22.86+j*2.54,-1.8],.06);}
  const battery=part('battery',[28,8,-5],[24,13,7]);box(battery,28,36,4.8,materials.foil,[0,0,0],1.3);box(battery,25,2,.7,materials.insulation,[0,18,.8]);
  label(battery,'Li-Po  3.7 V',23,6,[0,7,2.43],{bg:'#c7c6cc',fg:'#4c4b53',size:48});label(battery,'480 mAh · CONCEPT',23,4,[0,-2,2.43],{bg:'#c7c6cc',fg:'#64616a',size:35});
  const sd=part('sd-reader',[28,-22,-5.8],[32,-6,12]);pcb(sd,20,16);box(sd,14,12,1.5,materials.metal,[0,1,1.5]);box(sd,12,1.1,.6,materials.ink,[0,-5.1,1.4]);
  const card=part('sd-card',[28,-22.5,-3.6],[56,-12,18]);box(card,11,15,1,materials.ink);label(card,'32 GB',8,4,[0,2,.54],{bg:'#20212a',fg:'#c9c7d2',size:70});for(let j=0;j<8;j++)box(card,.75,3,.08,materials.gold,[-3.9+j*1.1,5.5,-.54],.03);
  const navs=[['up','cap-up',-15,'▲'],['select','cap-select',0,'●'],['down','cap-down',15,'▼']];
  for(const [id,capId,x,mark] of navs){const sw=part(id,[x,-39,6],[x*.6,-10,42]);box(sw,6,6,2,materials.metal);cylinder(sw,1.7,1.1,materials.ink,[0,0,1.4]);for(const xx of [-3.4,3.4])box(sw,.8,4,.5,materials.gold,[xx,0,-.6]);const cap=part(capId,[x,-39,10.5],[x*.6,-13,109]);cylinder(cap,2.7,2.4,materials.dark,[0,0,0]);label(cap,mark,3.4,3.4,[0,0,1.22],{bg:'#222129',fg:'#d4ccd9',size:210});}
  const reset=part('reset',[49,-38,8.1],[17,-9,70]);box(reset,4,4,2,materials.metal);cylinder(reset,1.25,2.9,materials.dark,[0,0,1.9]);
  function port(id,x,explosion){const g=part(id,[x,-43,-5.5],explosion);box(g,10,7,1.2,materials.blue,[0,2,-1.5]);const outer=box(g,8.5,6,3.5,materials.metal,[0,0,0],.6);box(g,6.8,.16,2.2,materials.ink,[0,-3.08,0],.2);box(g,5.3,.25,.5,materials.dark,[0,-3.2,0],.1);for(let j=0;j<8;j++)box(g,.3,.2,.12,materials.gold,[-2.1+j*.6,-3.35,.3],.03);return g;}
  port('usb-data',-29,[-36,-25,0]);port('usb-charge',12,[35,-25,-12]);
  function powerModule(id,p,e,w,h){const g=part(id,p,e);pcb(g,w,h);chip(g,w*.35,h*.35,[0,1,1.1]);for(let i=0;i<3;i++)box(g,1.4,2,.7,materials.insulation,[-w/2+2+i*2.8,-h/2+3,1.1]);return g;}
  powerModule('protection',[5,23,-5.8],[22,32,-8],12,8);
  powerModule('charger',[3,7,-5.8],[19,6,-3],15,14);
  powerModule('power-path',[3,-9,-5.8],[17,-8,-7],13,11);
  const regulator=powerModule('regulator',[3,-23,-5.8],[17,-23,-12],14,12);box(regulator,4,4,2,materials.dark,[3,1,2]);
  const plug=part('battery-plug',[19,31,-5],[30,29,4]);box(plug,7,4,3,materials.shell);for(const x of [-1.2,1.2])box(plug,.6,1,2,materials.gold,[x,-2.3,0]);
  const ps=part('power-switch',[60,12,-5],[32,0,-5]);box(ps,4,12,5,materials.metal);box(ps,4,4,3,materials.ink,[3,1,0]);
  const carrier=part('carrier',[0,0,-8.7],[0,0,-27]);box(carrier,100,68,1.6,materials.pcb);
  // Sparse solder pads show a plausible carrier without inventing a detailed netlist.
  for(let x=-43;x<45;x+=5)for(let y=-27;y<30;y+=5)cylinder(carrier,.55,.08,materials.gold,[x,y,.85],.24);
  label(carrier,'ASTAR / CONCEPT CARRIER',50,4,[0,0,-.84],{bg:'#164842',fg:'#bacdc4',size:30,back:true});
  const insulation=part('insulation',[0,0,-9.8],[0,0,-43]);box(insulation,105,74,.4,materials.insulation,[0,0,0],.1);
  const posts=part('posts',[0,0,0],[0,0,-12]);for(const x of [-56,56])for(const y of [-38,38])cylinder(posts,2.5,18,materials.shell,[x,y,-1],.9);for(const x of [-48,48])for(const y of [-33,36])cylinder(posts,1.8,9,materials.shell,[x,y,-.8],.8);
  const screws=part('screws',[0,0,0],[0,0,-114]);for(const x of [-56,56])for(const y of [-38,38]){cylinder(screws,.8,12,materials.metal,[x,y,-4]);cylinder(screws,1.7,.7,materials.metal,[x,y,-10.4]);box(screws,2.2,.35,.05,materials.ink,[x,y,-10.78],.04);box(screws,.35,2.2,.05,materials.ink,[x,y,-10.78],.04);}
  const mount=part('solar-mount',[0,1,-12.1],[0,-7,-86]);frame(mount,111,71,105.5,65.5,1.1,materials.dark,[0,0,0],2.5);
  const solar=part('solar',[0,1,-12.7],[0,-7,-107]);box(solar,105,65,1.1,materials.dark,[0,0,0],.3);
  for(let col=0;col<5;col++)for(let row=0;row<2;row++){const x=-40.8+col*20.4,y=-15.6+row*31.2;box(solar,19.6,30.3,.12,materials.solar,[x,y,-.62],.03);for(let line=0;line<15;line++)box(solar,18.8,.08,.02,materials.metal,[x,y-14+line*2,-.7],.005);box(solar,.24,29.8,.03,materials.metal,[x,y,-.72],.01);}
  const adhesive=part('adhesive',[0,0,0],[0,0,-54]);for(const x of [20,36])box(adhesive,6,30,.45,materials.rubber,[x,8,-7.7],.1);for(const y of [-27,29])box(adhesive,99,3,.25,materials.rubber,[0,y,-12.1],.1);
  const wires=part('wires',[0,0,0],[0,0,8]);for(let j=0;j<4;j++)wire(wires,[[-40+j,22,-3],[-44+j,29,-2],[-42+j,37,0],[-12+j*2.54,36,1.6]],j%2?materials.dark:materials.purple,.32);
  for(let j=0;j<2;j++)wire(wires,[[26+j*3,26,-4],[27+j*3,32,-4],[20+j*2,34,-4],[7+j*2,27,-5]],j?materials.dark:materials.red,.45);
  wire(wires,[[-27,-23,-4],[-27,-32,-5],[-29,-39,-5]],materials.dark,.8);
  wire(wires,[[31,-26,-4],[39,-31,-3],[43,-16,-2],[41,33,-1],[-36,33,-2],[-39,21,-3]],materials.purple,.4);
  wire(wires,[[9,-27,-5],[14,-33,-6],[12,-39,-6]],materials.red,.45);
  wire(wires,[[7,13,-5],[10,24,-7],[9,39,-8],[9,40,-12]],materials.dark,.6);
  const solder=part('solder',[0,0,0],[-8,0,-18]);for(let i=0;i<12;i++)cylinder(solder,.7,.5,materials.metal,[-44+i*3.2,-29,-7.5]);
  const heat=part('heat-shrink',[0,0,0],[0,0,18]);for(let i=0;i<2;i++)wire(heat,[[27+i*3,29,-4],[26+i*3,32,-4]],materials.dark,.74);
  const connectors=part('connectors',[0,0,0],[-5,0,23]);for(const [x,y]of [[-9,33],[-9,-31]]){box(connectors,18,3,2,materials.ink,[x,y,-5]);for(let i=0;i<7;i++)box(connectors,.5,.5,2,materials.gold,[x-7.62+i*2.54,y,-3.4],.05);}
  const clips=part('cable-clips',[0,0,0],[0,0,-4]);for(const [x,y] of [[43,18],[43,-13],[-43,30]]){box(clips,3,5,1.5,materials.shell,[x,y,-1.5]);box(clips,4,1,2,materials.shell,[x,y-2,-1.3]);}
  root.updateMatrixWorld(true);
  return {root,groups};
}
