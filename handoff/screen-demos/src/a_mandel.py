import numpy as np, numba, math, sys
from PIL import Image, ImageDraw, ImageFont
from common import *
W = ROUND["w"]; SS = 2; N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
CX, CY = -0.7436438870371587, 0.1318259042053120

@numba.njit(parallel=True, fastmath=True)
def render(W, SS, cx, cy, scale, ang, maxit, shift, out):
    ca, sa = math.cos(ang), math.sin(ang)
    n = W*SS
    for j in numba.prange(n):
        for i in range(n):
            u = (i + 0.5)/n - 0.5; v = (j + 0.5)/n - 0.5
            x0 = cx + scale*(u*ca - v*sa); y0 = cy + scale*(u*sa + v*ca)
            x = 0.0; y = 0.0; k = 0
            while k < maxit and x*x + y*y < 256.0:
                x, y = x*x - y*y + x0, 2*x*y + y0; k += 1
            if k >= maxit:
                r = g = b = 0.0
            else:
                nu = k + 1 - math.log(math.log(math.sqrt(x*x+y*y)))/math.log(2.0)
                t = math.log(nu)*0.55 + shift
                # deep-ocean -> gold -> magenta palette (kept within sRGB)
                r = 0.5 + 0.5*math.cos(6.2832*(t + 0.00)); g = 0.5 + 0.5*math.cos(6.2832*(t*1.0 + 0.15)); b = 0.5 + 0.5*math.cos(6.2832*(t + 0.35))
                e = min(1.0, nu/12.0)   # fade outer halo to black
                r *= e; g *= e; b *= e
            out[j//SS, i//SS, 0] += r*r; out[j//SS, i//SS, 1] += g*g; out[j//SS, i//SS, 2] += b*b

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
mask = round_mask(W)
yy, xx = np.mgrid[0:W, 0:W] + 0.5
rr = np.hypot(xx-W/2, yy-W/2); th = np.arctan2(yy-W/2, xx-W/2)
w = Writer(f"{OUT}/round_a_mandelbrot_knob_zoom.mp4", W, W)
for f in range(N):
    t = f/N
    zf = (1 - math.cos(2*math.pi*t))/2             # 0 -> 1 -> 0, seamless
    scale = 3.2 * math.exp(math.log(4e-6/3.2)*zf)
    ang = 2*math.pi*t                               # one knob turn per loop
    maxit = int(250 + 260*math.log10(3.2/scale))
    out = np.zeros((W, W, 3)); render(W, SS, CX, CY, scale, ang, maxit, t*2, out)
    img = out/(SS*SS)
    # knob detent ring: 24 ticks that turn with the image
    tick = ((np.cos(24*(th - ang)) > 0.985) & (rr > W/2-14) & (rr < W/2-4)).astype(float)
    img = np.maximum(img, tick[..., None]*np.array([0.55, 0.55, 0.6]))
    hud = Image.new("L", (W, W)); d = ImageDraw.Draw(hud)
    txt = f"x{3.2/scale:,.0f}"; d.text((W/2, W-48), txt, fill=255, font=font, anchor="mm")
    img = np.maximum(img, (np.asarray(hud)/255.0)[..., None]*0.6)
    w.write(img*mask)
    if f % 30 == 0: print("a", f, flush=True)
w.close()
