"""A genuine 400 x 300, one-bit framebuffer shared by all demo screens.

PDF mathematics is preserved as readable, overlapping source tiles rather than
flattened into an unreliable plain-text transcription. No generated answer keys.
"""
from __future__ import annotations

import io
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 400, 300
BODY = (16, 58, 384, 262)
FONT_PATH = next((p for p in [Path('C:/Windows/Fonts/arial.ttf'),
    Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')] if p.exists()), None)
BOLD_PATH = next((p for p in [Path('C:/Windows/Fonts/arialbd.ttf'),
    Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')] if p.exists()), FONT_PATH)


def font(size=18, bold=False):
    path = BOLD_PATH if bold else FONT_PATH
    return ImageFont.truetype(str(path), size) if path else ImageFont.load_default(size=size)


class Framebuffer:
    """Render first, threshold once. Every saved framebuffer is Pillow mode 1."""
    def __init__(self):
        self.image = Image.new('L', (WIDTH, HEIGHT), 255)
        self.draw = ImageDraw.Draw(self.image)
        self.issues = []

    def label(self, xy, value, size=18, bold=False, max_width=None):
        f = font(size, bold)
        if max_width and self.draw.textlength(value, font=f) > max_width:
            raise ValueError(f'Text exceeds fixed screen bounds: {value!r}')
        self.draw.text(xy, value, fill=0, font=f)

    def chrome(self, title, source, footer):
        # Titles wrap into body screens when long; chrome must never truncate.
        if self.draw.textlength(title, font=font(15, True)) > 366:
            raise ValueError('Screen title is too long; use a shorter display title.')
        self.label((16, 10), title, 15, True, 368)
        self.label((16, 32), source, 12, max_width=368)
        self.draw.line((16, 50, 383, 50), fill=0)
        self.draw.line((16, 272, 383, 272), fill=0)
        self.label((16, 280), footer, 12, max_width=368)

    def save(self, path):
        result = self.image.point(lambda x: 255 if x >= 175 else 0, '1')
        result.save(path, format='PNG')
        return result

    def png(self):
        output = io.BytesIO()
        self.image.point(lambda x: 255 if x >= 175 else 0, '1').save(output, format='PNG')
        return output.getvalue()


def wrap_text(text, width=368, size=18):
    measure = ImageDraw.Draw(Image.new('L', (1, 1)))
    f = font(size)
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph:
            lines.append('')
            continue
        line = ''
        for word in paragraph.split():
            candidate = (line + ' ' + word).strip()
            if measure.textlength(candidate, font=f) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
                line = ''
            # Long tokens are split, never silently clipped.
            while measure.textlength(word, font=f) > width:
                count = 1
                while count < len(word) and measure.textlength(word[:count+1], font=f) <= width:
                    count += 1
                lines.append(word[:count])
                word = word[count:]
            line = word
        if line:
            lines.append(line)
    return lines


def text_frames(title, text, source='ASTAR explanation', footer='UP / DOWN: page   SELECT: actions'):
    lines = wrap_text(text)
    # 8 x 24px lines fit in the explicitly reserved 204px body.
    count = max(1, math.ceil(len(lines) / 8))
    result = []
    for index in range(count):
        frame = Framebuffer()
        frame.chrome(title, source, footer)
        for row, value in enumerate(lines[index*8:(index+1)*8]):
            frame.label((16, 59+row*24), value, max_width=368)
        result.append(frame)
    return result


def tile_starts(length, capacity, overlap=28):
    if length <= capacity:
        return [0]
    starts = list(range(0, length-capacity+1, capacity-overlap))
    if starts[-1] != length-capacity:
        starts.append(length-capacity)
    return starts


def source_frames(image, title, source):
    """Tile at native render scale; never shrink a full page into tiny type.

    Columns are read left-to-right for each row, with 28px overlap to recover
    words crossing a boundary. Coordinates and tile counts are made explicit.
    """
    image = image.convert('L')
    xs, ys = tile_starts(image.width, 368), tile_starts(image.height, 204)
    frames = []
    for row, y in enumerate(ys):
        for col, x in enumerate(xs):
            frame = Framebuffer()
            label = f'{source} | tile {row+1},{col+1} / {len(ys)},{len(xs)}'
            frame.chrome(title, label, 'DOWN: next tile   UP: back   SELECT: actions')
            crop = image.crop((x, y, min(x+368, image.width), min(y+204, image.height)))
            frame.image.paste(crop, (16, 58))
            frames.append((frame, dict(x=x, y=y, width=crop.width, height=crop.height,
                                      row=row+1, column=col+1, rows=len(ys), columns=len(xs))))
    return frames


def menu_frame(title, entries, selected=0, subtitle='ASTAR / Chapter 1'):
    if not entries or not 0 <= selected < len(entries):
        raise ValueError('Invalid menu selection.')
    frame = Framebuffer()
    frame.chrome(title, subtitle, 'UP / DOWN: choose   SELECT: open')
    start = max(0, min(selected-2, len(entries)-5))
    for row, value in enumerate(entries[start:start+5]):
        active = start+row == selected
        y = 62+row*39
        if active:
            frame.draw.rectangle((15, y-2, 384, y+31), fill=0)
        f = font(18)
        if frame.draw.textlength(value, font=f) > 340:
            raise ValueError('Menu entry is too long.')
        frame.draw.text((26, y+3), value, fill=255 if active else 0, font=f)
    return frame


def pack_frame(image):
    """15,000 bytes, row major, MSB first, 1=white, compatible with mode-1 PNG."""
    if image.size != (WIDTH, HEIGHT):
        raise ValueError('Expected a 400 x 300 framebuffer.')
    return image.convert('1').tobytes()


def number_line_frame(numerator=0, denominator=4):
    """ASTAR-authored investigation, not a redrawn textbook quotation."""
    if denominator != 4 or not -8 <= numerator <= 8:
        raise ValueError('The explorer supports quarter-steps from -2 to 2.')
    frame=Framebuffer()
    frame.chrome('Explore the number line','ASTAR investigation / based on section 1.4',
                 'UP: left   DOWN: right   SELECT: return')
    frame.label((16,64),'Move by one quarter each step.',18)
    x0,x1,y=35,365,158
    frame.draw.line((x0,y,x1,y),fill=0,width=2)
    for n in range(-8,9):
        x=round(x0+(n+8)*(x1-x0)/16)
        major=n%4==0
        frame.draw.line((x,y-8 if major else y-4,x,y+8 if major else y+4),fill=0)
        if major:frame.label((x-6,y+17),str(n//4),16)
    x=round(x0+(numerator+8)*(x1-x0)/16)
    frame.draw.polygon([(x,145),(x-7,132),(x+7,132)],fill=0)
    value=f'Position: {numerator}/{denominator} = {numerator/denominator:g}'
    frame.label((16,219),value,18,True,max_width=368)
    return frame
