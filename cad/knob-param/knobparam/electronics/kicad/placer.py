"""A small simulated-annealing placer for the step-2 boards (6 Nov 2026), written for the two jack power boards: too many parts to place
by hand line by line, and KiCad 7 has no auto-placer.

Parts are rectangles (their courtyards) with pads at fixed offsets, for each allowed (side, rotation). The cost is
  sum over nets of weight x half-perimeter of the net's pads (both faces count the same: vias are cheap on 4 layers)
  + overlap area of courtyards on the same face (plus a margin), weighted up as the run cools
  + courtyard area outside the allowed rectangles of its face.
Moves: shift (a Gaussian step that shrinks as it cools), swap two parts, turn 90°, change face. Then a legalising pass pushes any
remaining overlaps apart along the shorter axis. Pure numpy; the geometry is measured with pcbnew by the caller."""
import math, random
import numpy as np


class Placer:
    def __init__(self, items, regions, nets, margin=0.1, seed=1):
        """items: [dict(ref, geoms={(side, rot): (x0, y0, x1, y1, {pad: (dx, dy)})}, fixed=None or (x, y, side, rot))]
        regions: {side: [(x0, y0, x1, y1), ...]} allowed areas (a courtyard must sit inside one of them)
        nets: [(weight, [(ref, pad), ...])]  (pads on parts without that pad are ignored)"""
        self.items = items; self.n = len(items); self.margin = margin
        self.mi = [it.get("margin", margin) for it in items]   # per-part spacing (ICs and connectors get room to escape)
        self.mscale = 1.0                                       # 0 = courtyards may touch (the last repair)
        self.rng = random.Random(seed)
        self.idx = {it["ref"]: i for i, it in enumerate(items)}
        self.regions = regions
        self.opts = [sorted(it["geoms"]) for it in items]
        self.fixed = [it.get("fixed") is not None for it in items]
        self.x = np.zeros(self.n); self.y = np.zeros(self.n); self.o = [None] * self.n   # o = (side, rot)
        for i, it in enumerate(items):
            if it.get("fixed"):
                fx, fy, fs, fr = it["fixed"]; self.x[i], self.y[i], self.o[i] = fx, fy, (fs, fr)
        self.nets = []
        self.part_nets = [[] for _ in range(self.n)]
        for w, pins in nets:
            pl = [(self.idx[r], p) for r, p in pins if r in self.idx]
            if len(pl) < 2 or w <= 0:
                continue
            k = len(self.nets); self.nets.append((w, pl))
            for i in {a for a, _ in pl}:
                self.part_nets[i].append(k)
        self.lam = 1.0

    # ---- geometry
    def rect(self, i, x=None, y=None, o=None):
        x = self.x[i] if x is None else x; y = self.y[i] if y is None else y; o = self.o[i] if o is None else o
        x0, y0, x1, y1, _ = self.items[i]["geoms"][o]
        return x + x0, y + y0, x + x1, y + y1

    def pad(self, i, p):
        g = self.items[i]["geoms"][self.o[i]][4]
        if p not in g:
            return None
        dx, dy = g[p]
        return self.x[i] + dx, self.y[i] + dy

    def net_cost(self, k):
        w, pl = self.nets[k]
        xs, ys = [], []
        for i, p in pl:
            q = self.pad(i, p)
            if q is not None:
                xs.append(q[0]); ys.append(q[1])
        if len(xs) < 2:
            return 0.0
        return w * ((max(xs) - min(xs)) + (max(ys) - min(ys)))

    def out_area(self, i):
        x0, y0, x1, y1 = self.rect(i)
        a = (x1 - x0) * (y1 - y0)
        best = 0.0
        for rx0, ry0, rx1, ry1 in self.regions[self.o[i][0]]:
            ix = max(0.0, min(x1, rx1) - max(x0, rx0)); iy = max(0.0, min(y1, ry1) - max(y0, ry0))
            best = max(best, ix * iy)
        # outside area plus a distance term so a part far out is pulled back
        return (a - best) * 4.0

    def overlap(self, i):
        x0, y0, x1, y1 = self.rect(i); s = self.o[i][0]; mi = self.mi[i] * self.mscale
        tot = 0.0
        for j in range(self.n):
            if j == i or self.o[j][0] != s:
                continue
            m = max(mi, self.mi[j] * self.mscale)
            a0, b0, a1, b1 = self.rect(j)
            ix = min(x1 + m, a1) - max(x0 - m, a0)
            if ix <= 0:
                continue
            iy = min(y1 + m, b1) - max(y0 - m, b0)
            if iy <= 0:
                continue
            tot += ix * iy + 0.5 * min(ix, iy)
        return tot

    def part_cost(self, i):
        return self.lam * (self.overlap(i) + self.out_area(i))

    def total(self):
        wl = sum(self.net_cost(k) for k in range(len(self.nets)))
        ov = sum(self.overlap(i) for i in range(self.n)) / 2
        out = sum(self.out_area(i) for i in range(self.n) if not self.fixed[i])
        return wl, ov, out

    # ---- annealing
    def init_random(self):
        for i in range(self.n):
            if self.fixed[i]:
                continue
            o = self.rng.choice(self.opts[i]); self.o[i] = o
            r = self.rng.choice(self.regions[o[0]])
            self.x[i] = self.rng.uniform(r[0], r[2]); self.y[i] = self.rng.uniform(r[1], r[3])

    def _local(self, ids):
        ks = set()
        for i in ids:
            ks.update(self.part_nets[i])
        wl = sum(self.net_cost(k) for k in ks)
        pc = sum(self.part_cost(i) for i in ids)
        if len(ids) == 2:   # the pair's mutual overlap was counted twice
            pass
        return wl + pc

    def run(self, iters=200000, t0=None, t1=0.01, step0=4.0, step1=0.1, lam0=0.5, lam1=6000.0, log=None):
        mov = [i for i in range(self.n) if not self.fixed[i]]
        if t0 is None:
            t0 = 2.0
        for it in range(iters):
            f = it / iters
            T = t0 * (t1 / t0) ** f
            step = step0 * (step1 / step0) ** f
            self.lam = lam0 * (lam1 / lam0) ** f
            r = self.rng.random()
            i = self.rng.choice(mov)
            if r < 0.70:   # shift (now and then a jump anywhere)
                ids = [i]; old = [(self.x[i], self.y[i], self.o[i])]
                c0 = self._local(ids)
                if self.rng.random() < 0.05:
                    rg = self.rng.choice(self.regions[self.o[i][0]])
                    self.x[i] = self.rng.uniform(rg[0], rg[2]); self.y[i] = self.rng.uniform(rg[1], rg[3])
                else:
                    self.x[i] += self.rng.gauss(0, step); self.y[i] += self.rng.gauss(0, step)
            elif r < 0.85:   # swap
                j = self.rng.choice(mov)
                if j == i:
                    continue
                ids = [i, j]; old = [(self.x[i], self.y[i], self.o[i]), (self.x[j], self.y[j], self.o[j])]
                c0 = self._local(ids)
                self.x[i], self.x[j] = self.x[j], self.x[i]; self.y[i], self.y[j] = self.y[j], self.y[i]
                si, sj = self.o[i][0], self.o[j][0]
                if (sj, self.o[i][1]) in self.items[i]["geoms"] and (si, self.o[j][1]) in self.items[j]["geoms"]:
                    self.o[i], self.o[j] = (sj, self.o[i][1]), (si, self.o[j][1])
            else:   # turn or change face
                ids = [i]; old = [(self.x[i], self.y[i], self.o[i])]
                c0 = self._local(ids)
                self.o[i] = self.rng.choice(self.opts[i])
            c1 = self._local(ids)
            d = c1 - c0
            if d > 0 and self.rng.random() >= math.exp(-d / max(T, 1e-9)):
                for k, (ox, oy, oo) in zip(ids, old):
                    self.x[k], self.y[k], self.o[k] = ox, oy, oo
            if log and it % (iters // 10) == 0:
                wl, ov, out = self.total()
                log(f"  {it:7d}  T {T:7.3f}  step {step:5.2f}  wirelength {wl:8.1f}  overlap {ov:7.2f}  outside {out:6.2f}")

    def legalise(self, rounds=400):
        """Push overlapping courtyards apart along the shorter penetration, keep each inside its face's regions."""
        for _ in range(rounds):
            moved = False
            for i in range(self.n):
                if self.fixed[i]:
                    continue
                x0, y0, x1, y1 = self.rect(i)
                # into the region that holds most of it
                best, br = -1, None
                for r in self.regions[self.o[i][0]]:
                    ix = max(0.0, min(x1, r[2]) - max(x0, r[0])); iy = max(0.0, min(y1, r[3]) - max(y0, r[1]))
                    if ix * iy > best:
                        best, br = ix * iy, r
                dx = max(0.0, br[0] - x0) - max(0.0, x1 - br[2]); dy = max(0.0, br[1] - y0) - max(0.0, y1 - br[3])
                if abs(dx) > 1e-6 or abs(dy) > 1e-6:
                    self.x[i] += dx; self.y[i] += dy; moved = True
                for j in range(self.n):
                    if j == i or self.o[j][0] != self.o[i][0]:
                        continue
                    x0, y0, x1, y1 = self.rect(i); a0, b0, a1, b1 = self.rect(j)
                    m = max(self.mi[i], self.mi[j]) * self.mscale
                    ix = min(x1 + m, a1) - max(x0 - m, a0); iy = min(y1 + m, b1) - max(y0 - m, b0)
                    if ix <= 1e-6 or iy <= 1e-6:
                        continue
                    share = 1.0 if self.fixed[j] else 0.5
                    if ix < iy:
                        s = 1 if (x0 + x1) > (a0 + a1) else -1
                        self.x[i] += s * ix * share + s * 1e-3
                        if not self.fixed[j]:
                            self.x[j] -= s * ix * 0.5
                    else:
                        s = 1 if (y0 + y1) > (b0 + b1) else -1
                        self.y[i] += s * iy * share + s * 1e-3
                        if not self.fixed[j]:
                            self.y[j] -= s * iy * 0.5
                    moved = True
            if not moved:
                return True
        return False

    def repair(self, rounds=60, tries=120, log=None):
        """Greedy repair: each part still overlapping or outside tries positions round it (wider each round), both faces and all
        turns, and keeps the one with the least overlap, then the least wirelength."""
        mov = [i for i in range(self.n) if not self.fixed[i]]
        for rd in range(rounds):
            bad = [i for i in mov if self.overlap(i) > 1e-6 or self.out_area(i) > 1e-6]
            if not bad:
                return True
            self.rng.shuffle(bad)
            rad = 0.5 + 0.25 * rd
            for i in bad:
                ks = self.part_nets[i]
                def score():
                    return 1e4 * (self.overlap(i) + self.out_area(i)) + sum(self.net_cost(k) for k in ks)
                best = (score(), self.x[i], self.y[i], self.o[i])
                x0, y0, o0 = self.x[i], self.y[i], self.o[i]
                for _ in range(tries):
                    self.x[i] = x0 + self.rng.uniform(-rad, rad); self.y[i] = y0 + self.rng.uniform(-rad, rad)
                    self.o[i] = self.rng.choice(self.opts[i]) if self.rng.random() < 0.3 else o0
                    s = score()
                    if s < best[0]:
                        best = (s, self.x[i], self.y[i], self.o[i])
                self.x[i], self.y[i], self.o[i] = best[1], best[2], best[3]
            if log and rd % 10 == 0:
                log(f"  repair {rd}: {len(bad)} parts overlapping or outside")
        return not [i for i in mov if self.overlap(i) > 1e-6 or self.out_area(i) > 1e-6]

    def relocate(self, g=0.25, log=None):
        """Last resort for parts still overlapping: try every grid point on both faces, every turn; keep the free spot with the
        least wirelength."""
        mov = [i for i in range(self.n) if not self.fixed[i]]
        bad = [i for i in mov if self.overlap(i) > 1e-6 or self.out_area(i) > 1e-6]
        for i in bad:
            ks = self.part_nets[i]; best = None
            x0, y0, o0 = self.x[i], self.y[i], self.o[i]
            for o in self.opts[i]:
                self.o[i] = o
                for rg in self.regions[o[0]]:
                    x = rg[0]
                    while x <= rg[2]:
                        y = rg[1]
                        while y <= rg[3]:
                            self.x[i], self.y[i] = x, y
                            if self.out_area(i) < 1e-9 and self.overlap(i) < 1e-9:
                                s = sum(self.net_cost(k) for k in ks)
                                if best is None or s < best[0]:
                                    best = (s, x, y, o)
                            y += g
                        x += g
            if best:
                self.x[i], self.y[i], self.o[i] = best[1], best[2], best[3]
                if log:
                    log(f"  relocated {self.items[i]['ref']} to ({best[1]:.2f}, {best[2]:.2f}) {best[3]}")
            else:
                self.x[i], self.y[i], self.o[i] = x0, y0, o0
                if log:
                    log(f"  no free spot for {self.items[i]['ref']}")
        return not [i for i in mov if self.overlap(i) > 1e-6 or self.out_area(i) > 1e-6]

    def snap(self, g=0.05):
        for i in range(self.n):
            if not self.fixed[i]:
                self.x[i] = round(self.x[i] / g) * g; self.y[i] = round(self.y[i] / g) * g

    def result(self):
        return {it["ref"]: (float(self.x[i]), float(self.y[i]), self.o[i][0], self.o[i][1]) for i, it in enumerate(self.items)}
