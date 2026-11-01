import numpy as np, numba, math, sys
from PIL import Image, ImageDraw, ImageFont
from common import *
W, H = RECT["w"], RECT["h"]; N = int(sys.argv[1]) if len(sys.argv) > 1 else 300; T = 30; PRE = 90
L = N/FPS; NP = 5000
rng = np.random.default_rng(3)
K = 7; kx = rng.normal(0, 1, K)*3.5; ky = rng.normal(0, 1, K)*3.5; ph = rng.random(K)*6.283; om = rng.integers(-2, 3, K).astype(float); amp = 1/np.hypot(kx, ky)
def joy(t):
    p = 2*math.pi*t/L
    return 0.5 + 0.36*math.sin(p) + 0.06*math.sin(3*p), 0.5 + 0.34*math.sin(2*p + 0.6)
@numba.njit(fastmath=True)
def vel(x, y, tt, jx, jy, kx, ky, ph, om, amp):
    # curl of sum of sinusoids, aspect-correct coordinates
    X = x*1.628; vx = 0.0; vy = 0.0
    for i in range(kx.size):
        s = math.cos(kx[i]*X + ky[i]*y + ph[i] + om[i]*tt)*amp[i]
        vx += 0.55*s*ky[i]; vy -= 0.55*s*kx[i]
    dx = (x - jx)*1.628; dy = y - jy; d2 = dx*dx + dy*dy + 0.004
    sw = 0.22/d2*math.exp(-d2/0.09)                   # joystick vortex
    vx += -dy*sw - dx*0.35*math.exp(-d2/0.05); vy += dx*sw - dy*0.35*math.exp(-d2/0.05)
    return vx*0.0042, vy*0.0042
@numba.njit(parallel=False, fastmath=True)
def step(P, life, buf, tt, jx, jy, kx, ky, ph, om, amp, rnd, W, H):
    for i in range(P.shape[0]):
        x, y = P[i, 0], P[i, 1]
        vx, vy = vel(x, y, tt, jx, jy, kx, ky, ph, om, amp)
        x += vx; y += vy; life[i] -= 1
        if life[i] <= 0 or x < 0 or x > 1 or y < 0 or y > 1:
            x = rnd[i, 0]; y = rnd[i, 1]; life[i] = 60 + rnd[i, 2]*120
        P[i, 0] = x; P[i, 1] = y
        sp = math.sqrt(vx*vx + vy*vy)*260
        a = math.atan2(vy, vx)
        q = min(1.0, sp*0.35)
        h = 0.5 + 0.5*math.cos(a)
        r = 0.15 + 0.85*q*q + 0.5*h*(1-q); g = 0.25 + 0.75*q; b = 1.0 - 0.3*q*q
        ddx = (x - jx)*1.628; ddy = y - jy; nr = math.exp(-(ddx*ddx + ddy*ddy)/0.05)
        r = r*(1-nr) + nr*1.0; g = g*(1-nr) + nr*(0.35 + 0.5*q); b = b*(1-nr) + nr*(0.55 - 0.4*q)
        e = min(1.0, 0.12 + sp*0.8)*min(1.0, life[i]/20.0)
        x0 = (x - vx)*W; y0 = (y - vy)*H; x1 = x*W; y1 = y*H
        ns = int(math.sqrt((x1-x0)**2 + (y1-y0)**2)) + 1
        for k in range(ns):
            u = (k + 0.5)/ns; px = x0 + (x1-x0)*u; py = y0 + (y1-y0)*u
            ix = int(px); iy = int(py); fx = px - ix; fy = py - iy
            for oy in range(2):
                for ox in range(2):
                    X = ix + ox; Y = iy + oy
                    if 0 <= X < W and 0 <= Y < H:
                        wgt = (fx if ox else 1-fx)*(fy if oy else 1-fy)*e*0.35
                        buf[Y, X, 0] += r*wgt; buf[Y, X, 1] += g*wgt; buf[Y, X, 2] += b*wgt
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
P = rng.random((NP, 2)); life = rng.random(NP)*180; buf = np.zeros((H, W, 3))
frames = []
yy, xx = np.mgrid[0:H, 0:W] + 0.5
for f in range(-PRE, N + T):
    t = f/FPS; tt = 2*math.pi*t/L; jx, jy = joy(t)
    buf *= 0.935
    step(P, life, buf, tt, jx, jy, kx, ky, ph, om, amp, rng.random((NP, 3)), W, H)
    if f < 0: continue
    img = 1 - np.exp(-buf*0.9)                    # filmic, no hard clipping
    # joystick puck
    d = np.hypot(xx - jx*W, yy - jy*H)
    img += (np.exp(-(d/3.0)**2)*0.9 + np.exp(-((d-11)/1.2)**2)*0.5)[..., None]*np.array([1, 1, 1])
    hud = Image.new("L", (W, H)); dr = ImageDraw.Draw(hud)
    dr.line([(jx*W, 0), (jx*W, H)], fill=28); dr.line([(0, jy*H), (W, jy*H)], fill=28)
    dr.text((8, H-18), f"CC1 X {int(jx*127):3d}   CC2 Y {int((1-jy)*127):3d}", fill=150, font=font)
    img = np.maximum(img, (np.asarray(hud)/255.0)[..., None])
    frames.append(np.clip(img, 0, 1).astype(np.float32))
    if f % 60 == 0: print("d", f, flush=True)
wr = Writer(f"{OUT}/joy_d_curl_flow.mp4", W, H)
for i in range(N):
    o = frames[i + T]
    if i >= N - T:
        w_ = (i - (N - T))/T; o = (1 - w_)*o + w_*frames[i + T - N]
    wr.write(o**2.2)
wr.close()
