import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
H = os.path.dirname(os.path.abspath(__file__))
S = 1024
GOLD = (232, 196, 92); YEL = (252, 235, 45); DARK = (8, 12, 22)

def bg():
    im = Image.new("RGB", (S, S), (0, 0, 0))
    g = Image.new("L", (S, S), 0); d = ImageDraw.Draw(g)
    for r in range(S, 0, -8):
        d.ellipse([S/2-r, S*0.42-r, S/2+r, S*0.42+r], fill=int(255*max(0, 1-r/(S*0.75))**1.6))
    navy = Image.new("RGB", (S, S), (22, 34, 62))
    return Image.composite(navy, im, g)

def shield_path(cx, top, w, h):
    def bez(p0, p1, p2, n=40):
        return [((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0], (1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]) for t in (i/n for i in range(n+1))]
    L, R, mid, bot = cx-w/2, cx+w/2, top+h*0.42, top+h
    return [(L, top), (R, top)] + bez((R, mid), (R, top+h*0.82), (cx, bot)) + bez((cx, bot), (L, top+h*0.82), (L, mid))

def icon_kcd():
    im = bg(); d = ImageDraw.Draw(im)
    cx = S/2; top = S*0.25; w = S*0.56; h = S*0.62
    p = shield_path(cx, top, w, h)
    glow = Image.new("RGBA", (S, S), (0,0,0,0)); ImageDraw.Draw(glow).polygon(p, fill=GOLD+(120,))
    im.paste(glow.filter(ImageFilter.GaussianBlur(40)), (0,0), glow.filter(ImageFilter.GaussianBlur(40)))
    d.polygon(p, fill=GOLD)
    inner = shield_path(cx, top+22, w-44, h-44); d.polygon(inner, fill=DARK)
    # sword
    bw = S*0.034
    d.polygon([(cx-bw, top+150), (cx+bw, top+150), (cx+bw, top+h-150), (cx, top+h-95), (cx-bw, top+h-150)], fill=YEL)
    d.rectangle([cx-S*0.15, top+150, cx+S*0.15, top+150+S*0.03], fill=YEL)
    d.rectangle([cx-bw*0.7, top+72, cx+bw*0.7, top+150], fill=GOLD)
    d.ellipse([cx-S*0.03, top+44, cx+S*0.03, top+44+S*0.06], fill=YEL)
    # crown
    cy = top - S*0.075; cw = S*0.30
    crown = [(cx-cw/2, cy+S*0.07), (cx-cw/2, cy-S*0.02), (cx-cw/4, cy+S*0.03), (cx, cy-S*0.06),
             (cx+cw/4, cy+S*0.03), (cx+cw/2, cy-S*0.02), (cx+cw/2, cy+S*0.07)]
    d.polygon(crown, fill=YEL)
    for x, y in [(cx-cw/2, cy-S*0.02), (cx, cy-S*0.06), (cx+cw/2, cy-S*0.02)]:
        d.ellipse([x-S*0.022, y-S*0.044, x+S*0.022, y], fill=YEL)
    # year
    f = ImageFont.truetype(os.path.join(H, "fonts", "Unifraktur.ttf"), int(S*0.085))
    for txt, x in (("14", cx-S*0.13), ("03", cx+S*0.13)):
        b = d.textbbox((0,0), txt, font=f); d.text((x-(b[2]-b[0])/2-b[0], top+S*0.24), txt, font=f, fill=GOLD)
    return im

def icon_hub():
    im = bg(); d = ImageDraw.Draw(im)
    # closed book with bookmark
    x0, y0, x1, y1 = S*0.27, S*0.2, S*0.73, S*0.8
    d.rounded_rectangle([x0, y0, x1, y1], radius=S*0.03, fill=GOLD)
    d.rounded_rectangle([x0+S*0.045, y0+S*0.035, x1-S*0.035, y1-S*0.035], radius=S*0.02, fill=DARK)
    d.rectangle([x0+S*0.06, y0, x0+S*0.075, y1], fill=GOLD)
    d.polygon([(x1-S*0.14, y0), (x1-S*0.08, y0), (x1-S*0.08, y0+S*0.24), (x1-S*0.11, y0+S*0.2), (x1-S*0.14, y0+S*0.24)], fill=YEL)
    f = ImageFont.truetype(os.path.join(H, "fonts", "Unifraktur.ttf"), int(S*0.30))
    b = d.textbbox((0,0), "F", font=f); cx = (x0+S*0.075+x1)/2
    d.text((cx-(b[2]-b[0])/2-b[0], S*0.5-(b[3]-b[1])/2-b[1]+S*0.02), "F", font=f, fill=YEL)
    return im

def save(im, dest, sizes):
    os.makedirs(dest, exist_ok=True)
    for name, sz in sizes:
        im.resize((sz, sz), Image.LANCZOS).save(os.path.join(dest, name), optimize=True)

SIZES = [("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512), ("favicon-32.png", 32)]
if __name__ == "__main__":
    save(icon_kcd(), os.path.join(H, "kcd1", "pwa"), SIZES)
    save(icon_hub(), os.path.join(H, "hub"), SIZES)
    print("icons ok")
