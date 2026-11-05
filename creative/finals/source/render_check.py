from pathlib import Path
import pymupdf as fitz
from PIL import Image,ImageOps,ImageDraw
root=Path(__file__).resolve().parents[1]
thumbs=[]
for f in sorted((root/'deliverables').glob('*.pdf')):
    doc=fitz.open(f)
    for i,p in enumerate(doc):
        path=root/'preview'/f'{f.stem}-{i+1}.png'
        pix=p.get_pixmap(matrix=fitz.Matrix(1.25,1.25));pix.save(path)
        im=Image.open(path).convert('RGB');im.thumbnail((297,421))
        tile=Image.new('RGB',(320,465),'#ddd');tile.paste(im,((320-im.width)//2,10));ImageDraw.Draw(tile).text((8,440),f.stem[:38],fill='black');thumbs.append(tile)
sheet=Image.new('RGB',(320*4,465*((len(thumbs)+3)//4)),'white')
for i,t in enumerate(thumbs):sheet.paste(t,((i%4)*320,(i//4)*465))
sheet.save(root/'preview'/'print-contact-sheet.png')
print('Rendered',len(thumbs),'pages')
