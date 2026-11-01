import numpy as np, math, sys
from scipy.ndimage import zoom, map_coordinates, gaussian_filter
from common import *
W = ROUND["w"]; N = int(sys.argv[1]) if len(sys.argv) > 1 else 330
rng = np.random.default_rng(7)
def fbm(n, oct=6, base=4, seed=0, pers=0.55):
    r = np.random.default_rng(seed); acc = np.zeros((n, n)); a = 1; tot = 0
    for o in range(oct):
        g = base*2**o
        acc += a*zoom(r.random((g+3, g+3)), n/g, order=3)[n//g:n//g+n, n//g:n//g+n][:n, :n]; tot += a; a *= pers
    acc /= tot; return (acc - acc.min())/(acc.max() - acc.min())
yy, xx = (np.mgrid[0:W, 0:W] + 0.5)/W*2 - 1
r = np.hypot(xx, yy); th = np.arctan2(yy, xx)
def lerp(a, b, t): return a + (b - a)*t[..., None]
C = lambda *v: np.array(v, float)

# 1. Nebula: domain-warped fBm, gas in teal/magenta, dust lanes, stars
n1, n2, n3 = fbm(W, seed=1), fbm(W, seed=2), fbm(W, seed=3)
q = map_coordinates(n3, [np.clip((yy*0.5+0.5)*W + 120*(n1-0.5), 0, W-1), np.clip((xx*0.5+0.5)*W + 120*(n2-0.5), 0, W-1)], order=1)
gas = np.clip((q - 0.35)*2.2, 0, 1)**1.6
neb = lerp(C(0.02, 0.0, 0.05), C(0.55, 0.08, 0.45), gas) + (np.clip((n1-0.55)*4, 0, 1)**2)[..., None]*C(0.05, 0.45, 0.5)
neb *= (1 - 0.8*np.clip((n2-0.6)*4, 0, 1))[..., None]
stars = (rng.random((W, W)) > 0.9975)*rng.random((W, W)); stars = gaussian_filter(stars, 0.7)*6
neb = neb + stars[..., None]*C(1, 0.95, 0.9)

# 2. Iris: radial fibres, amber collarette, limbal ring, pupil, catch-light
fib = fbm(W, seed=4, base=6); fib = map_coordinates(fib, [np.clip(r*W*0.9, 0, W-1), (th/np.pi*0.5+0.5)*(W-1)*1.0], order=1)
ang = np.random.default_rng(11).random(361); ang[-1] = ang[0]
angn = np.interp(((th + 0.08*(fib-0.5))/(2*np.pi) % 1)*360, np.arange(361), ang)
fibres = 0.45 + 0.55*angn**1.5*(0.6 + 0.4*fib)
iris = lerp(C(0.05, 0.25, 0.32), C(0.12, 0.45, 0.4), fib)*fibres[..., None]
iris = lerp(iris, C(0.65, 0.38, 0.08), np.clip(1 - (r-0.32)/0.12, 0, 1)*fib)
iris *= np.clip((0.95 - r)/0.06, 0, 1)[..., None]*(0.4 + 0.6*np.clip((0.95-r)/0.25, 0, 1))[..., None]
iris = iris*(r > 0.24)[..., None] + C(0.75, 0.7, 0.65)*np.clip((r-0.95)/0.05, 0, 1)[..., None]*0.35
hl = np.exp(-((xx+0.28)**2 + (yy+0.3)**2)/0.004); iris += hl[..., None]*0.9

# 3. Flower: 3 layers of petals with veins, yellow stamen centre
fl = np.zeros((W, W, 3))
for k, rot, size, col in [(8, 0.2, 0.98, C(0.75, 0.18, 0.38)), (8, 0.2+np.pi/8, 0.78, C(0.92, 0.42, 0.55)), (6, 0.5, 0.5, C(0.98, 0.78, 0.82))]:
    pet = size*(0.55 + 0.45*np.abs(np.cos(k*(th-rot)/2))**0.6)
    inside = np.clip((pet - r)/0.015, 0, 1)
    vein = 0.92 + 0.08*np.cos(k*(th-rot)*7)
    shade = (0.45 + 0.55*(r/pet))*vein
    fl = fl*(1-inside[..., None]) + (col*shade[..., None])*inside[..., None]
cen = np.clip((0.17 - r)/0.01, 0, 1); dots = 0.6 + 0.4*np.cos(r*120)*np.cos(th*21)
fl = fl*(1-cen[..., None]) + (C(0.95, 0.7, 0.08)*dots[..., None])*cen[..., None]
fl = lerp(C(0.0, 0.03, 0.0), fl, np.clip((1.0 - r)*60, 0, 1)*(fl.sum(-1) > 0))

# 4. Earth: orthographic sphere, fBm continents, ice caps, clouds, atmosphere, terminator
R0 = 0.86; inside = r < R0; z = np.sqrt(np.clip(R0**2 - r**2, 0, None))/R0
lat = np.arcsin(np.clip(yy/R0, -1, 1)); lon = np.arctan2(xx/R0, z)
def sph(field, s=1.0): return map_coordinates(field, [np.clip((lat/np.pi+0.5)*(W-1), 0, W-1), ((lon*s/np.pi*0.5+0.5)%1)*(W-1)], order=1)
land = sph(fbm(W, seed=5, base=3)); cl = sph(fbm(W, seed=6, base=5, pers=0.6))
ocean = lerp(C(0.01, 0.05, 0.18), C(0.03, 0.18, 0.4), z)
ground = lerp(C(0.12, 0.3, 0.08), C(0.45, 0.38, 0.2), np.clip((land-0.66)*5, 0, 1))
earth = np.where((land > 0.6)[..., None], ground, ocean)
earth = lerp(earth, C(0.9, 0.92, 0.95), np.clip((np.abs(lat) - 1.15)*6, 0, 1))
earth = lerp(earth, C(0.95, 0.95, 0.97), np.clip((cl - 0.55)*3, 0, 1))
light = np.clip(0.15 + (-xx*0.55 - yy*0.35 + z*0.75)/R0, 0, 1)
earth = earth*light[..., None]*inside[..., None]
atm = np.exp(-((r - R0)/0.03)**2)*np.clip(0.3 + light*1.2 + (r > R0)*0.3, 0, 1)
earth += atm[..., None]*C(0.25, 0.5, 1.0)*0.7 + stars[..., None]*C(1, 1, 1)*(r > R0+0.05)[..., None]*0.5

imgs = [np.clip(i, 0, 1)**2.2 for i in (neb, iris, fl, earth)]   # author in sRGB-ish, convert to linear
# flow field (divergence-free: curl of a scalar noise) that loops with phase
P1, P2 = gaussian_filter(fbm(W, seed=8, base=3), 6), gaussian_filter(fbm(W, seed=9, base=3), 6)
def curl(P): gy, gx = np.gradient(P); return gx, -gy
c1, c2 = curl(P1), curl(P2); norm = max(np.abs(np.stack(c1+c2)).max(), 1e-9)
gy0, gx0 = np.mgrid[0:W, 0:W].astype(float)
def warp(img, dx, dy): return np.stack([map_coordinates(img[..., k], [np.clip(gy0+dy, 0, W-1), np.clip(gx0+dx, 0, W-1)], order=1) for k in range(3)], -1)
from PIL import Image
if N<50:
    Image.fromarray(np.concatenate([amoled(i) for i in imgs],1)).save("/tmp/b_imgs.png")
mask = round_mask(W); seg = N//4; tr = int(seg*0.45)
w = Writer(f"{OUT}/round_b_liquid_morph.mp4", W, W)
for f in range(N):
    ph = 2*np.pi*f/N; i = f//seg; a, b = imgs[i % 4], imgs[(i+1) % 4]
    loc = f - i*seg; m = np.clip((loc - (seg - tr))/tr, 0, 1); m = m*m*(3-2*m)
    fx = (np.cos(ph)*c1[0] + np.sin(ph)*c2[0])/norm; fy = (np.cos(ph)*c1[1] + np.sin(ph)*c2[1])/norm
    amp = 4 + 170*np.sin(np.pi*m)
    A = warp(a, fx*amp*(0.3+m), fy*amp*(0.3+m)); img = A
    if m > 0:
        B = warp(b, -fx*amp*(1.3-m), -fy*amp*(1.3-m)); mb = np.clip((m-0.35)/0.3, 0, 1); mb = mb*mb*(3-2*mb); img = A*(1-mb) + B*mb
    w.write(img*mask)
w.close(); print("b done")
