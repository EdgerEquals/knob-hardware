/* Search core for router4.py (knob step 2, 6 Nov 2026): A* / Dijkstra on a multi-layer grid, called once per connection.
   Nodes are layer * N + cell (N = nx * ny). Moves: 8 neighbours in a layer (no corner cutting past a statically blocked cell),
   and a through via to any other layer at the same cell. One extra node, nl * N, is the "sink" (the ground plane): a node u with
   a finite sinkc[u] reaches it at that extra cost. Written for this project; no outside code. */
#include <stdlib.h>
#include <stdint.h>
#include <math.h>

typedef struct { float f, d; int u; } HE;
static HE *heap = 0; static int hn = 0, hcap = 0;
static float *dist = 0; static int *prev = 0; static int *stamp = 0; static int cap = 0, cur = 0;

static void hpush(float f, float d, int u) {
    if (hn >= hcap) { hcap = hcap ? hcap * 2 : (1 << 16); heap = (HE *)realloc(heap, (size_t)hcap * sizeof(HE)); }
    int i = hn++;
    while (i > 0) { int p = (i - 1) / 2; if (heap[p].f <= f) break; heap[i] = heap[p]; i = p; }
    heap[i].f = f; heap[i].d = d; heap[i].u = u;
}

static HE hpop(void) {
    HE top = heap[0]; HE last = heap[--hn]; int i = 0;
    for (;;) {
        int l = 2 * i + 1; if (l >= hn) break;
        int r = l + 1, c = (r < hn && heap[r].f < heap[l].f) ? r : l;
        if (heap[c].f >= last.f) break;
        heap[i] = heap[c]; i = c;
    }
    heap[i] = last; return top;
}

static float hfun(int x, int y, const int *tb, int ntb, float g) {
    if (!tb || ntb <= 0) return 0.f;
    float best = 1e30f;
    for (int k = 0; k < ntb; k++) {
        int dx = tb[4 * k] - x; if (dx < 0) { dx = x - tb[4 * k + 2]; if (dx < 0) dx = 0; }
        int dy = tb[4 * k + 1] - y; if (dy < 0) { dy = y - tb[4 * k + 3]; if (dy < 0) dy = 0; }
        int mn = dx < dy ? dx : dy, mx = dx < dy ? dy : dx;
        float h = (float)(mx - mn) + 1.41421356f * (float)mn;
        if (h < best) best = h;
    }
    return best * g;
}

/* Returns the path length written to out (source first, last node = target, or the node that drops to the sink), 0 if none. */
int route_search(int nx, int ny, int nl, const float *cost, const float *vcost, const uint8_t *blk,
                 const int *src, int nsrc, const uint8_t *tgt, const float *sinkc,
                 const int *tb, int ntb, float g, int *out, int maxout, int *reached_sink, long maxexp) {
    int N = nx * ny, T = nl * N + 1, SINK = nl * N;
    if (T > cap) {
        cap = T; dist = (float *)realloc(dist, (size_t)cap * sizeof(float)); prev = (int *)realloc(prev, (size_t)cap * sizeof(int));
        stamp = (int *)realloc(stamp, (size_t)cap * sizeof(int));
        for (int i = 0; i < cap; i++) stamp[i] = 0;
        cur = 0;
    }
    cur++; hn = 0; *reached_sink = 0;
    for (int k = 0; k < nsrc; k++) {
        int u = src[k]; if (u < 0 || u >= SINK) continue;
        stamp[u] = cur; dist[u] = 0.f; prev[u] = -1;
        int c = u % N; hpush(hfun(c % nx, c / nx, tb, ntb, g), 0.f, u);
    }
    const int DX[8] = {1, -1, 0, 0, 1, 1, -1, -1}, DY[8] = {0, 0, 1, -1, 1, -1, 1, -1};
    const float LN[8] = {1, 1, 1, 1, 1.41421356f, 1.41421356f, 1.41421356f, 1.41421356f};
    int found = -1; long nexp = 0;
    while (hn > 0) {
        HE e = hpop();
        int u = e.u;
        if (stamp[u] != cur || e.d > dist[u]) continue;
        if (u == SINK) { found = u; break; }
        if (tgt && tgt[u]) { found = u; break; }
        if (++nexp > maxexp) break;
        int L = u / N, c = u % N, x = c % nx, y = c / nx;
        const float *cl = cost + (size_t)L * N; const uint8_t *bl = blk + (size_t)L * N;
        for (int k = 0; k < 8; k++) {
            int jx = x + DX[k], jy = y + DY[k];
            if (jx < 0 || jy < 0 || jx >= nx || jy >= ny) continue;
            int j = jy * nx + jx; float cj = cl[j];
            if (!isfinite(cj)) continue;
            if (k >= 4 && (bl[y * nx + jx] || bl[jy * nx + x])) continue;
            int v = L * N + j; float nd = e.d + LN[k] * g * cj;
            if (stamp[v] != cur || nd < dist[v]) {
                stamp[v] = cur; dist[v] = nd; prev[v] = u; hpush(nd + hfun(jx, jy, tb, ntb, g), nd, v);
            }
        }
        float vc = vcost[c];
        if (isfinite(vc)) {
            for (int L2 = 0; L2 < nl; L2++) {
                if (L2 == L) continue;
                int v = L2 * N + c; if (!isfinite(cost[v])) continue;
                float nd = e.d + vc;
                if (stamp[v] != cur || nd < dist[v]) { stamp[v] = cur; dist[v] = nd; prev[v] = u; hpush(nd + hfun(x, y, tb, ntb, g), nd, v); }
            }
        }
        if (sinkc && isfinite(sinkc[u])) {
            float nd = e.d + sinkc[u];
            if (stamp[SINK] != cur || nd < dist[SINK]) { stamp[SINK] = cur; dist[SINK] = nd; prev[SINK] = u; hpush(nd, nd, SINK); }
        }
    }
    if (found < 0) return 0;
    int n = 0, u = found;
    if (u == SINK) { *reached_sink = 1; u = prev[u]; }
    while (u != -1 && n < maxout) { out[n++] = u; u = prev[u]; }
    for (int i = 0; i < n / 2; i++) { int t = out[i]; out[i] = out[n - 1 - i]; out[n - 1 - i] = t; }
    return n;
}
