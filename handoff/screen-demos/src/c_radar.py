import numpy as np, math, sys, colorsys
from PIL import Image, ImageDraw, ImageFont
from common import *
W = ROUND["w"]; N = int(sys.argv[1]) if len(sys.argv) > 1 else 300; L = N/FPS
REVS = 4; TREV = L/REVS
FIFTHS = ["C", "G", "D", "A", "E", "B", "F#", "C#", "G#", "D#", "A#", "F"]
CHORDS = [("Cmaj7", ["C3", "C4", "E4", "G4", "B4", "E5"]), ("Am9", ["A3", "A4", "C4", "E4", "G4", "B5"]),
          ("Fmaj7#11", ["F3", "F4", "A4", "C5", "E5", "B5"]), ("G13", ["G3", "G4", "B4", "D5", "F5", "E5"])]
RAD = {3: 0.34, 4: 0.56, 5: 0.78}
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 13)
fontb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
yy, xx = (np.mgrid[0:W, 0:W] + 0.5)/W*2 - 1
r = np.hypot(xx, yy); th = np.arctan2(xx, -yy) % (2*np.pi)   # 0 at top, clockwise
def gauss(cx, cy, s): return np.exp(-((xx-cx)**2 + (yy-cy)**2)/(2*s*s))
events = []  # (time, x, y, rgb, name)
for rev, (cname, notes) in enumerate(CHORDS):
    for nn in notes:
        pc, octv = nn[:-1], int(nn[-1]); k = FIFTHS.index(pc); a = k*2*np.pi/12 + 0.12*(octv-4)
        rr = RAD[octv]; x, y = rr*np.sin(a), -rr*np.cos(a)
        rgb = np.array(colorsys.hsv_to_rgb(k/12, 0.75, 1.0))
        events.append((rev*TREV + a/(2*np.pi)*TREV, x, y, rgb, nn))
BEAM = np.array([0.25, 1.0, 0.55])
# static graticule
grid = np.zeros((W, W))
for rr in RAD.values(): grid = np.maximum(grid, np.exp(-((r-rr)*W/2/0.8)**2)*0.12)
spoke = (np.cos(12*th) > 0.9997)*(r < 0.9)*(r > 0.12)*0.10; grid = np.maximum(grid, spoke)
grid = np.maximum(grid, np.exp(-((r-0.9)*W/2/0.8)**2)*0.25)
lab = Image.new("L", (W, W)); d = ImageDraw.Draw(lab)
for k, n in enumerate(FIFTHS):
    a = k*2*np.pi/12; d.text((W/2 + 0.955*W/2*np.sin(a), W/2 - 0.955*W/2*np.cos(a)), n, fill=110, font=font, anchor="mm")
grid = np.maximum(grid, np.asarray(lab)/255.0)
mask = round_mask(W); wr = Writer(f"{OUT}/round_c_fifths_radar.mp4", W, W)
for f in range(N):
    t = f/FPS; ba = (t % TREV)/TREV*2*np.pi
    dlt = (ba - th) % (2*np.pi)
    trail = np.exp(-dlt/0.9)*0.55 + np.exp(-dlt/0.05)*0.6       # phosphor afterglow + hot leading edge
    trail *= np.clip((0.9 - r)*40, 0, 1)*(0.35 + 0.65*r)
    img = grid[..., None]*np.array([0.35, 0.8, 0.5]) + trail[..., None]*BEAM
    txt = Image.new("RGB", (W, W)); dt = ImageDraw.Draw(txt)
    for (t0, x, y, rgb, nn) in events:
        age = (t - t0) % L
        if age > 2.2: continue
        dot = math.exp(-age/0.7)
        ring_r = 0.02 + age*0.12; ring = np.exp(-((np.hypot(xx-x, yy-y) - ring_r)*W/2/1.6)**2)*math.exp(-age/0.45)
        img += (gauss(x, y, 0.012)*dot*1.2 + gauss(x, y, 0.045)*dot*0.35 + ring*0.6)[..., None]*rgb
        a = int(255*min(1, dot*1.4)); col = tuple(int(c*a) for c in rgb)
        dt.text((W/2 + x*W/2, W/2 + y*W/2 - 18), nn, fill=col, font=font, anchor="mm")
    cname = CHORDS[int(t//TREV) % REVS][0]
    dt.text((W/2, W/2 + 4), cname, fill=(150, 230, 180), font=fontb, anchor="mm")
    img = np.maximum(img, np.asarray(txt)/255.0)
    img = img/(1 + 0.35*img)          # soft knee instead of hard clip (no blown-out primaries)
    wr.write(img**2.2*mask if False else np.clip(img, 0, 1)**2.2*mask)
    if f % 60 == 0: print("c", f, flush=True)
wr.close()
