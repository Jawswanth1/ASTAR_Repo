"""Regenerate derived learning images without changing the source PDF or lessons."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import pymupdf as pdf
from PIL import Image, ImageOps, ImageDraw
from astar_app.converter import learning_pixmap
from astar_app.storage import read_course,atomic_json


def refresh(directory):
    directory=Path(directory);course=read_course(directory)
    removed=[]
    with pdf.open(directory/'source.pdf') as doc:
        for i,page in enumerate(doc):
            if page.rotation:page.remove_rotation()
            scale=min(1.6,1400/max(page.rect.width,page.rect.height))
            pix,stamp=learning_pixmap(page,scale)
            image=ImageOps.autocontrast(Image.frombytes('L',(pix.width,pix.height),pix.samples)).convert('1')
            relative=f'assets/page-{i+1:04d}.png'
            temp=directory/(relative+'.tmp.png');image.save(temp,optimize=True);temp.replace(directory/relative)
            if stamp:removed.append(i+1)
            for lesson in course['lessons']:
                for panel in lesson['panels']:
                    if panel['page']!=i+1 or not panel.get('focusImage'):continue
                    bounds=panel.get('focusBounds')
                    boxes=[b['bbox'] for b in lesson['blocks'] if b['page']==i+1]
                    if bounds is None:
                        chapter=next(c['title'] for c in course['chapters'] if c['id']==lesson['chapterId'])
                        selected=[b['bbox'] for b in lesson['blocks'] if b['page']==i+1 and ' '.join(b['text'].split()).casefold()!=chapter.casefold()] or boxes
                        r=pdf.Rect(selected[0])
                        for b in selected[1:]:r|=pdf.Rect(b)
                        r=(r+(-8,-6,8,6))&page.rect
                        r=pdf.Rect(max(0,min(60,r.x0)),r.y0,min(page.rect.width,max(page.rect.width-45,r.x1)),min(page.rect.height,max(r.y1,page.rect.height*.885)))
                        bounds=list(r);panel['focusBounds']=bounds
                    clean=image.copy();draw=ImageDraw.Draw(clean);sx,sy=image.width/page.rect.width,image.height/page.rect.height
                    for entry in course['report'].get('analysis',{}).get('excluded',[]):
                        if entry['page']!=i+1 or 'watermark' in entry['reason'].lower():continue
                        er=pdf.Rect(entry['bbox'])
                        if not any((er & pdf.Rect(b)).get_area()>5 for b in boxes):
                            draw.rectangle((round(er.x0*sx),round(er.y0*sy),round(er.x1*sx),round(er.y1*sy)),fill=1)
                    r=pdf.Rect(bounds);crop=clean.crop((int(r.x0*sx),int(r.y0*sy),round(r.x1*sx),round(r.y1*sy)))
                    temp=directory/(panel['focusImage']+'.tmp.png');crop.save(temp,optimize=True);temp.replace(directory/panel['focusImage'])
            if (i+1)%25==0:print(f'Rendered {i+1}/{len(doc)} pages',flush=True)
    course['report']['rendering']={'version':'2.1','isolatedStampsHiddenOnPages':removed,'sourcePdfUnchanged':True}
    atomic_json(directory/'course.json',course)
    print(f'Complete. Isolated publisher stamps hidden on {len(removed)} pages.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('course_directory',type=Path)
    refresh(parser.parse_args().course_directory)
