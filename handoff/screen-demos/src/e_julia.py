import numpy as np, numba, math, sys
from PIL import Image, ImageDraw, ImageFont
from common import *
W, H = RECT["w"], RECT["h"]; N = int(sys.argv[1]) if len(sys.argv) > 1 else 300; SS = 2
@numba.njit(parallel=True, fastmath=True)
def julia(W, H, SS, cr, ci, span, maxit, shift, out):
    for j in numba.prange(H*SS):
        for i in range(W*SS):
            x = ((i + 0.5)/(W*SS) - 0.5)*span; y = ((j + 0.5)/(H*SS) - 0.5)*span*H/W
            k = 0; mn = 1e9
            while k < maxit and x*x + y*y < 256.0:
                x, y = x*x - y*y + cr, 2*x*y + ci; k += 1
                m = x*x + y*y
                if m < mn: mn = m
            if k >= maxit:   # interior: faint orbit-trap glow, mostly true black
                v = math.sqrt(mn)
                r = 0.10*v; g = 0.02*v; b = 0.18*v
            else:
                nu = k + 1 - math.log(math.log(math.sqrt(x*x + y*y)))/math.log(2.0)
                t = math.log(nu)*0.6 + shift
                r = 0.5 + 0.5*math.cos(6.2832*(t + 0.55)); g = 0.5 + 0.5*math.cos(6.2832*(t + 0.75)); b = 0.5 + 0.5*math.cos(6.2832*(t + 0.95))
                e = min(1.0, nu/10.0)**1.5
                r *= e; g *= e; b *= e
            out[j//SS, i//SS, 0] += r*r; out[j//SS, i//SS, 1] += g*g; out[j//SS, i//SS, 2] += b*b
@numba.njit(parallel=True)
def mandel_map(w, h, out):
    for j in numba.prange(h):
        for i in range(w):
            x0 = -2.2 + 3.0*i/w; y0 = (j/h - 0.5)*3.0*h/w; x = 0.0; y = 0.0; k = 0
            while k < 60 and x*x + y*y < 4: x, y = x*x - y*y + x0, 2*x*y + y0; k += 1
            out[j, i] = 0.0 if k == 60 else min(1.0, k/25.0)
mw, mh = 96, 64; mm = np.zeros((mh, mw)); mandel_map(mw, mh, mm)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
def cpath(t):
    th = 2*math.pi*t; s = 1.06 + 0.045*math.sin(3*th)   # hug the main cardioid edge
    zr, zi = math.cos(th)/2 - math.cos(2*th)/4, math.sin(th)/2 - math.sin(2*th)/4
    return 0.25 + (zr - 0.25)*s, zi*s
wr = Writer(f"{OUT}/joy_e_julia_stick.mp4", W, H)
for f in range(N):
    t = f/N; cr, ci = cpath(t)
    out = np.zeros((H, W, 3)); julia(W, H, SS, cr, ci, 3.3, 320, t*2, out)
    img = out/(SS*SS)
    # minimap inset: where the stick is in the c-plane
    hud = Image.new("RGB", (W, H)); d = ImageDraw.Draw(hud)
    ox, oy = W - mw - 8, 8
    mmi = (np.stack([mm*0.25, mm*0.35, mm*0.45], -1)*255 + 6).astype(np.uint8)
    hud.paste(Image.fromarray(mmi), (ox, oy)); d.rectangle([ox-1, oy-1, ox+mw, oy+mh], outline=(70, 70, 80))
    px, py = ox + (cr + 2.2)/3.0*mw, oy + (ci/(3.0*mh/mw) + 0.5)*mh
    d.ellipse([px-3, py-3, px+3, py+3], fill=(255, 210, 120))
    d.text((8, H-17), f"c = {cr:+.3f} {ci:+.3f}i", fill=(170, 170, 180), font=font)
    hv = np.asarray(hud)/255.0; a = hv.max(-1, keepdims=True) > 0
    img = np.where(a, hv**2.2, img)
    wr.write(img)
    if f % 60 == 0: print("e", f, flush=True)
wr.close()
