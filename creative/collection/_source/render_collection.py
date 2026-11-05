from pathlib import Path
import pymupdf as fitz
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];pre=R/'_preview';pre.mkdir(exist_ok=True)
groups={}
for f in R.rglob('*.pdf'):
 if '_source' in f.parts or '_preview' in f.parts:continue
 doc=fitz.open(f);pages=[]
 for i,p in enumerate(doc):
  key=f.stem+f'-{i+1:02}';target=pre/(key+'.png')
  scale=min(1.4,1440/p.rect.width)
  p.get_pixmap(matrix=fitz.Matrix(scale,scale)).save(target);pages.append(target)
  if 'Social Media' in str(f):p.get_pixmap(matrix=fitz.Matrix(1,1)).save(f.with_suffix('.png'))
 groups[str(f.relative_to(R))]=[str(a.relative_to(R)) for a in pages]
import json
(pre/'render-index.json').write_text(json.dumps(groups,indent=2))
prints=[v[0] for k,v in groups.items() if k.startswith(('BRAND','PRODUCT','MERCHANDISE','DOCUMENTATION','MARKETING/Poster'))]
def sheet(paths,name,cols=3,w=330,h=475):
 out=Image.new('RGB',(cols*w,((len(paths)+cols-1)//cols)*h),'#d4cfd7')
 for i,f in enumerate(paths):
  im=Image.open(R/f).convert('RGB');im.thumbnail((w-16,h-35));x=(i%cols)*w;y=(i//cols)*h
  out.paste(im,(x+(w-im.width)//2,y+8));ImageDraw.Draw(out).text((x+8,y+h-22),Path(f).stem[:40],fill='#141215')
 out.save(pre/name)
sheet(prints,'print-overview.png')
sheet([str(p.relative_to(R)) for p in sorted(pre.glob('slide-*.png'))],'pitch-overview.png',3,480,290)
sheet([v[0] for k,v in groups.items() if 'Social Media' in k],'social-overview.png',3,360,385)
print('Rendered',sum(map(len,groups.values())),'pages')
