"""Extract selectable prose, superscripts and vector text; never render PDF pages."""
import html
import re
from collections import Counter
import pymupdf as pdf

GANITA_HASH='5bff054e99d47c7ef525a5a038f8d7304c7342e7b396752839d832fe431c8b7d'

def automatic_scope(doc):
    """Use chapter bookmarks, body headings and solution-appendix boundaries."""
    found={};appendices=[]
    for level,title,page in doc.get_toc():
        if re.search(r'\b(solution|solutions|answers|answer key)\b',title,re.I):
            appendices.append(page);continue
        match=re.search(r'\b(?:ch(?:apter)?|unit)[\s_.-]*0*(\d+)\b',title,re.I)
        if match:found.setdefault(int(match[1]),(title,page))
    # Contents entries are not mistaken for body chapter starts.
    for i in range(min(len(doc),400)):
        text=doc[i].get_text()
        if re.search(r'\bcontents\b',text[:1000],re.I):continue
        for line in text.splitlines()[:18]:
            match=re.fullmatch(r'\s*(?:CHAPTER|UNIT)\s*[-:.]?\s*(\d+|ONE|TWO)\s*(?:[-:.].{0,90})?\s*',line,re.I)
            if match:
                token=match[1].lower();n={'one':1,'two':2}.get(token,int(token) if token.isdigit() else 0)
                found.setdefault(n,(f'Chapter {n}',i+1))
    first=found.get(1,('',None))[1]
    second=found.get(2,('',None))[1]
    if first is None:
        first_text=doc[0].get_text()
        # A short chapter PDF (including the user's chapter + solutions file).
        if len(doc)<=100 and len(first_text.strip())>100 and not re.search(r'\bcontents\b',first_text[:1200],re.I):
            first=1
        else:
            raise ValueError('ASTAR could not identify Chapter 1 automatically in this PDF. A chapter-only PDF or a PDF with readable chapter headings is supported; no page numbers are needed.')
    candidates=[p for p in [second,*appendices] if p and p>first]
    last=min(candidates)-1 if candidates else len(doc)
    if last-first>=100:raise ValueError('The first chapter could not be separated reliably from the rest of this textbook.')
    chapters=[dict(number=n,title=t[0]) for n,t in sorted(found.items())] or [dict(number=1,title='Chapter 1')]
    return first,last,chapters

def furniture(doc,first,last):
    counts=Counter()
    for n in range(first,last+1):
        p=doc[n-1]
        for b in p.get_text('dict')['blocks']:
            for line in b.get('lines',[]):
                if line['bbox'][1]<p.rect.height*.09 or line['bbox'][3]>p.rect.height*.93:
                    t=''.join(s['text'] for s in line['spans']).strip()
                    if t:counts[t]+=1
    return {t for t,c in counts.items() if c>=max(2,(last-first+1)//4)}

def strip_controls(text):
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\x84]','',text).replace('\ufffd','□')

def extract_blocks(page,number,assets,excluded=(),clip=None):
    flags=pdf.TEXTFLAGS_DICT if clip is None else pdf.TEXTFLAGS_DICT & ~pdf.TEXT_PRESERVE_IMAGES
    data=page.get_text('dict',sort=True,clip=clip,flags=flags);result=[];drawings=None
    def removable(line):
        t=''.join(s['text'] for s in line['spans']).strip()
        margin=line['bbox'][1]<page.rect.height*.09 or line['bbox'][3]>page.rect.height*.92
        return (margin and (t in excluded or re.fullmatch(r'\d+',t) or re.match(r'Reprint\s+\d',t))) or t.strip()=='SCERT  TELANGANA'
    for b in data['blocks']:
        if b['type']!=0:continue
        lines=[l for l in b['lines'] if not removable(l) and abs(l.get('dir',(1,0))[1])<.25]
        if not lines:continue
        text=' '.join(strip_controls(''.join(s['text'] for s in l['spans'])).strip() for l in lines).strip()
        if not text:continue
        spans=[s for line in lines for s in line['spans']]
        # Fractions split across PDF lines keep their native coordinates as SVG
        # text, not raster snapshots. Ordinary exponents remain HTML <sup>.
        short=sum(len(''.join(s['text'] for s in l['spans']).strip())<=5 for l in lines)
        complex_math=short>=3 and any(re.search(r'[=×÷±√∑⎛⎝]',s['text']) for s in spans)
        if complex_math:
            x0=min(l['bbox'][0] for l in lines)-2;y0=min(l['bbox'][1] for l in lines)-2
            x1=max(l['bbox'][2] for l in lines)+2;y1=max(l['bbox'][3] for l in lines)+2
            elements=[]
            for s in spans:
                raw=strip_controls(s['text'])
                elements.append(f'<text x="{s["origin"][0]-x0:.2f}" y="{s["origin"][1]-y0:.2f}" font-size="{s["size"]:.2f}" font-family="serif">{html.escape(raw)}</text>')
            # Fraction bars and radical strokes inside this formula region.
            rect=pdf.Rect(x0,y0,x1,y1)
            if drawings is None:drawings=page.get_drawings()
            for drawing in drawings:
                for item in drawing['items']:
                    if item[0]=='l' and rect.contains(item[1]) and rect.contains(item[2]):
                        a,c=item[1],item[2];elements.append(f'<line x1="{a.x-x0:.2f}" y1="{a.y-y0:.2f}" x2="{c.x-x0:.2f}" y2="{c.y-y0:.2f}" stroke="black" stroke-width=".7"/>')
            markup=f'<svg class="extracted-math" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {x1-x0:.2f} {y1-y0:.2f}" role="img" aria-label="Extracted mathematical text">'+''.join(elements)+'</svg>'
            kind='math'
        else:
            segments=[]
            for line in lines:
                pieces=[]
                for s in line['spans']:
                    value=html.escape(strip_controls(s['text']))
                    if s['flags']&1:value='<sup>'+value+'</sup>'
                    elif s['flags']&16:value='<strong>'+value+'</strong>'
                    pieces.append(value)
                segments.append(''.join(pieces).strip())
            markup=' '.join(segments)
            kind='heading' if len(text)<100 and max(s['size'] for s in spans)>=14 else 'text'
        result.append(dict(id=f'p{number}-b{len(result)+1}',page=number,kind=kind,html=markup,text=text,bbox=list(b['bbox'])))
    # Extract actual illustrations only, excluding full-page background artwork.
    if clip is None:
        for b in data['blocks']:
            if b['type']!=1:continue
            rect=pdf.Rect(b['bbox'])
            if rect.width<35 or rect.height<35 or rect.get_area()>page.rect.get_area()*.30:continue
            if rect.width>page.rect.width*.85 and (rect.x0<3 or rect.y0<page.rect.height*.09 or rect.y1>page.rect.height*.92):continue
            if number==1 and rect.y1<page.rect.height*.30:continue
            if rect.y1<page.rect.height*.09 or rect.y0>page.rect.height*.92:continue
            import io
            from PIL import Image
            path=f'diagram-{number}-{len(result)}.png'
            Image.open(io.BytesIO(b['image'])).convert('L').convert('1').save(assets/path)
            result.append(dict(id=f'p{number}-figure{len(result)}',page=number,kind='figure',image=f'assets/{path}',text='',bbox=list(rect)))
    result.sort(key=lambda b:(b['bbox'][1],b['bbox'][0]))
    return result
