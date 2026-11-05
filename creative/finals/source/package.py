from pathlib import Path
from reportlab.pdfgen import canvas
from PIL import Image,ImageDraw
import zipfile,html,json
root=Path(__file__).resolve().parents[1];out=root/'deliverables'
c=canvas.Canvas(str(out/'12-ASTAR-pitch.pdf'),pagesize=(960,540));c.setTitle('ASTAR competition pitch')
slides=sorted((root/'preview').glob('slide-*.png'))
sheet=Image.new('RGB',(960,200*((len(slides)+2)//3)),'#E8E5ED')
for i,p in enumerate(slides):
    c.drawImage(str(p),0,0,960,540);c.showPage()
    im=Image.open(p).convert('RGB');im.thumbnail((312,176));sheet.paste(im,((i%3)*320+4,(i//3)*200+4));ImageDraw.Draw(sheet).text(((i%3)*320+8,(i//3)*200+182),str(i+1).zfill(2),fill='#181A27')
c.save();sheet.save(root/'preview'/'deck-contact-sheet.png')
readme='''# ASTAR finals package

Uses your supplied logo with black and purple, with A4 print sheets.

Start with deliverables/11-ASTAR-pitch.pptx for editable slides or 12-ASTAR-pitch.pdf for a portable presentation copy. The PDF slide copy uses reviewed slide images. Read 09-Presenter-and-production-guide.md before rehearsal.

01 Brand guide: colours, typography, logo use and writing.
02 A4 hero poster: display behind the product.
03 Product and company sheet: judge handout.
04 A4 sticker sheet: six cut-out stickers.
05 Merchandise and packaging: shirt placement and box-label reference.
06 Student quick start: one-page reader guide.
07 Technical architecture: content, software and proposed power system.
08 Contact cards and table sign: four cut-out cards and a table sign.
09 Presenter and production guide: introductions, pitch, demo, Q&A and printing.
10 Slide speaker notes: accessible text copy of the deck notes.
11 Editable pitch: 11 slides with speaker notes.
12 PDF pitch: portable slide copy.
ASTAR-offline-sample.html: previously generated standalone sample course from your project. Open in a browser and rehearse before the contest.

Print A4 at 100%. The sheets have white margins and no bleed. Merchandise and box graphics are placement references rather than manufacturing templates. The original logo and software screenshots are in assets/. Editable generation scripts are in source/. Website, launch video, photorealistic hardware renders and physical printing are not included in this package. No final URL was confirmed, so no QR code is included. Hardware is labelled proposed and prices are labelled founder targets.
'''
(root/'README.md').write_text(readme,encoding='utf-8')
items=[]
for f in sorted(out.iterdir()):
    items.append(f'<li><a href="deliverables/{html.escape(f.name)}">{html.escape(f.name)}</a></li>')
(root/'START-HERE.html').write_text('<!doctype html><meta charset="utf-8"><title>ASTAR finals package</title><style>body{font:18px Arial;max-width:920px;margin:50px auto;padding:25px;color:#181A27;background:#faf9fc}h1,a{color:#7041c6}li{padding:9px}img{max-width:100%}</style><h1>ASTAR finals package</h1><p>Your supplied identity. A4 materials. Editable pitch.</p><ul>'+''.join(items)+'</ul><p>Read README.md and the production guide before printing or presenting.</p><img src="preview/print-contact-sheet.png" alt="A4 print collection preview">',encoding='utf-8')
with zipfile.ZipFile(root.parent/'ASTAR-Finals-Package.zip','w',zipfile.ZIP_DEFLATED) as z:
    for folder in ['deliverables','assets']:
        for f in (root/folder).iterdir():
            if f.is_file():z.write(f,'ASTAR-Finals/'+str(f.relative_to(root)))
    for n in ['README.md','START-HERE.html']:z.write(root/n,'ASTAR-Finals/'+n)
    for n in ['print-contact-sheet.png','deck-contact-sheet.png']:z.write(root/'preview'/n,'ASTAR-Finals/preview/'+n)
    for f in (root/'source').iterdir():
        if f.suffix in ['.py','.mjs'] or f.name=='slides.json':z.write(f,'ASTAR-Finals/source/'+f.name)
print('Packaged',len(list(out.iterdir())),'deliverables')
