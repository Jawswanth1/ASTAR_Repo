from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
R=Path(__file__).resolve().parents[1]
for n,f in [('H','ariblk.ttf'),('R','arial.ttf')]:pdfmetrics.registerFont(TTFont(n,'C:/Windows/Fonts/'+f))
ink='#0C0C0E';paper='#F0ECE4';purple='#6852FF'
def txt(c,t,x,y,size,color,font='H'):c.setFillColor(HexColor(color));c.setFont(font,size);c.drawString(x,y,t)
def bg(c,col):c.setFillColor(HexColor(col));c.rect(0,0,1440,810,fill=1,stroke=0)
c=canvas.Canvas(str(R/'MARKETING/Advertisement/ASTAR-ad-storyboard.pdf'),pagesize=(1440,810))
scenes=[('WHEN THE','NETWORK STOPS.','Learning still matters.'),('A WHOLE','TEXTBOOK.','Prepared as chapters and lessons.'),('READ. TRY.','KEEP LEARNING.','Offline software. Local progress.'),('POWERED BY','A BIGGER IDEA.','A proposed solar-powered learning device.'),('LEARNING WHEN','INFRASTRUCTURE FAILS.','ASTAR / Autonomous Solar Tutoring and Resource System'),('BUILD THE','NEXT CHAPTER.','Explore ASTAR. astarco0@gmail.com')]
for i,(a,b,cap) in enumerate(scenes):
 bg(c,paper if i==3 else ink);fg=ink if i==3 else paper
 txt(c,'ASTAR',65,748,22,purple)
 if i==3:
  c.drawImage(str(R/'PRODUCT/Device Renders/ASTAR-assembled-concept.png'),545,135,830,553,preserveAspectRatio=True,anchor='c')
  txt(c,'SOLAR',65,510,72,ink);txt(c,'LEARNING',65,424,60,purple);txt(c,'CONCEPT',65,348,60,purple)
  txt(c,'Hardware visualization / design concept',65,80,20,ink,'R')
 elif i in [1,2]:
  txt(c,a,65,624,65,fg);txt(c,b,65,545,65,purple)
  fp=R/'SOFTWARE/Screenshots'/('01-library.png' if i==1 else '09-lesson-circles.png')
  c.drawImage(str(fp),65,123,1310,390,preserveAspectRatio=True,anchor='c')
 else:
  txt(c,a,65,474,72,fg);txt(c,b,65,383,72,purple)
 txt(c,cap,65,55,23,fg,'R');c.showPage()
c.save()
print('Advertisement storyboard ready')
