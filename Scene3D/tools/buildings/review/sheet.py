"""sheet.py <out.jpg> <title> <label=img> ... [--cw 1000 --ch 625] [--crop x,y,w,h for label]: a labelled row sheet."""
import sys
from PIL import Image, ImageDraw, ImageFont
args = sys.argv[1:]
cw, ch = 1000, 625
if '--cw' in args:
    i = args.index('--cw'); cw = int(args[i + 1]); del args[i:i + 2]
if '--ch' in args:
    i = args.index('--ch'); ch = int(args[i + 1]); del args[i:i + 2]
out, title, items = args[0], args[1], args[2:]
rows = [r.split('|') for r in items]          # a row: "label=img|label=img|..."
try:
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
except Exception:
    F = ImageFont.load_default()
ncol = max(len(r) for r in rows)
W = 12 + ncol * (cw + 12); H = 40 + len(rows) * (ch + 34)
sh = Image.new('RGB', (W, H), (22, 27, 34)); d = ImageDraw.Draw(sh)
d.text((12, 10), title, fill=(232, 237, 242), font=F)
for ri, r in enumerate(rows):
    for ci, it in enumerate(r):
        lab, path = it.split('=', 1)
        im = Image.open(path).convert('RGB')
        # cover-fit into the cell (keeps the 3:2 / 16:10 frames comparable)
        s = max(cw / im.width, ch / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        x0 = (im.width - cw) // 2; y0 = (im.height - ch) // 2
        im = im.crop((x0, y0, x0 + cw, y0 + ch))
        x = 12 + ci * (cw + 12); y = 40 + ri * (ch + 34)
        d.text((x, y + 6), lab, fill=(232, 237, 242), font=F)
        sh.paste(im, (x, y + 30))
sh.save(out, quality=88)
print(out, sh.size)
