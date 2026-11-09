# Web model for the browser viewer (5 Nov, Ed: "the CAD model ... switch all the parts on and off", Inventor-style navigation).
# Reads the assembly-animation cache (tools/assembly_anim.py cache: every part tessellated in the panel frame, the joystick placed)
# and writes one binary file the viewer page loads:
#   model.bin = uint32 JSON length + JSON (meta, groups, parts) padded to 4 + one data blob.
#   Per part: positions as uint16 x3 quantized over the part's own box (step = size / 65535), triangle indices (uint16 or uint32),
#   and CAD feature edges as index pairs into the same positions (welded edges where the two faces meet at more than EDGE_DEG,
#   so smooth seams and tangent edges drop out).
# Colours, materials and see-through come from knobparam/assembly/colours.py (the same table as the renders).
# Run from cad/knob-param (after `tools/assembly_anim.py cache`):
#   .venv/bin/python tools/web_model.py <out dir> [extra parts json]   -> model.bin and model.txt (base64 of the gzipped model.bin, for the artifact)
# The viewer page is cad/viewer/knob-model.html (three.js r128); publish it with model.txt next to it.
import json, os, struct, sys
import numpy as np

sys.path.insert(0, ".")
EDGE_DEG = 25.0
GROUPS = [   # cache "sub" -> browser group name, in browser order
    ("case", "Case and front panel"),
    ("main_knob", "Main knob"),
    ("control_dial", "Control dial"),
    ("base_drive", "Base drive (motors, gears, cradle)"),
    ("electronics", "Electronics"),
    ("under_pcb", "Under the main board"),
    ("joystick", "Joystick"),
    ("board_copper", "Main board copper (routed v2)"),
]


def feature_edges(P, T):
    """Index pairs (into P) of the edges where the welded mesh folds by more than EDGE_DEG, plus open boundaries."""
    if len(T) == 0:
        return np.zeros((0, 2), np.int64)
    q = np.round(P / 1e-4).astype(np.int64)
    uq, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    inv = inv.reshape(-1)
    W = inv[T]                                         # welded triangle vertex ids
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n, axis=1)
    ok = ln > 1e-12
    n[ok] /= ln[ok, None]
    E = np.stack([W[:, [0, 1]], W[:, [1, 2]], W[:, [2, 0]]], axis=1).reshape(-1, 2)
    tri = np.repeat(np.arange(len(T)), 3)
    keep_tri = np.repeat(ok, 3) & (E[:, 0] != E[:, 1])
    E, tri = np.sort(E[keep_tri], axis=1), tri[keep_tri]
    key = E[:, 0] * (len(uq) + 1) + E[:, 1]
    order = np.argsort(key, kind="stable")
    key, E, tri = key[order], E[order], tri[order]
    starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    counts = np.diff(np.r_[starts, len(key)])
    keep = counts != 2
    two = starts[counts == 2]
    d = np.abs(np.einsum("ij,ij->i", n[tri[two]], n[tri[two + 1]]))
    keep2 = np.zeros(len(starts), bool)
    keep2[counts == 2] = d < np.cos(np.radians(EDGE_DEG))
    sel = starts[keep | keep2]
    return first[E[sel]]                               # back to a representative original vertex


def main():
    from knobparam.assembly import colours as C
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    cd = os.environ.get("KNOBPARAM_CACHE", os.path.join(os.getcwd(), ".cache-knob"))
    idx = json.load(open(os.path.join(cd, "anim", "index.json")))
    meta, parts = idx["meta"], idx["parts"]
    if len(sys.argv) > 2:   # extra parts made outside the model (the routed main board's copper: export_copper_mesh.py)
        for x in json.load(open(sys.argv[2])):
            parts[x["n"]] = dict(sub=x["sub"], mesh=x["mesh"], bb=x["bb"])
    blob, recs = bytearray(), []

    def put(arr):
        off = len(blob)
        blob.extend(arr.tobytes())
        while len(blob) % 4:
            blob.append(0)
        return off

    gnames = dict(GROUPS)
    order = {k: i for i, (k, _) in enumerate(GROUPS)}
    names = sorted(parts, key=lambda n: (order.get(parts[n]["sub"], 99), list(parts).index(n)))
    nt = ne = 0
    for name in names:
        p = parts[name]
        z = np.load(p["mesh"])
        P, T = z["P"].astype(np.float64), z["T"].astype(np.int64)
        lo, hi = P.min(axis=0), P.max(axis=0)
        sc = np.where(hi - lo > 1e-9, (hi - lo) / 65535.0, 1.0)
        Q = np.round((P - lo) / sc).astype(np.uint16)
        it = np.uint16 if len(P) <= 65535 else np.uint32
        Ed = feature_edges(P, T)
        k = C.key(name)
        leg, col, clear = C.MATERIALS[k]
        recs.append(dict(
            n=name, g=p["sub"], k=k, c=col, m=leg, t=bool(clear),
            bb=[round(v, 3) for v in p["bb"]], vol=round(p.get("vol", 0.0), 3),
            o=[float(v) for v in lo], s=[float(v) for v in sc],
            nv=len(P), nt=len(T), ne=len(Ed), i32=it is np.uint32,
            pv=put(Q), pi=put(T.astype(it)), pe=put(Ed.astype(it))))
        nt += len(T); ne += len(Ed)
    groups = [dict(id=k, name=gnames.get(k, k)) for k, _ in GROUPS if any(r["g"] == k for r in recs)]
    head = dict(meta=dict(meta, triangles=nt, edges=ne, edge_deg=EDGE_DEG), groups=groups,
                materials={k: dict(legend=v[0], colour=v[1], clear=v[2]) for k, v in C.MATERIALS.items()}, parts=recs)
    hj = json.dumps(head, separators=(",", ":")).encode()
    hj += b" " * ((4 - len(hj) % 4) % 4)
    f = os.path.join(out, "model.bin")
    with open(f, "wb") as fh:
        fh.write(struct.pack("<I", len(hj))); fh.write(hj); fh.write(blob)
    # artifacts serve text, not raw binary: also write model.txt = base64(gzip(model.bin)); the page unpacks it (DecompressionStream)
    import base64, gzip
    t = os.path.join(out, "model.txt")
    with open(f, "rb") as fh, open(t, "wb") as th:
        th.write(base64.b64encode(gzip.compress(fh.read(), 9, mtime=0)))
    print(f"wrote {f}: {len(recs)} parts, {nt} triangles, {ne} edges, {os.path.getsize(f) / 1e6:.2f} MB; "
          f"{t}: {os.path.getsize(t) / 1e6:.2f} MB "
          f"({meta['version']} {meta['branch']} @ {meta['commit']}, cache {meta['built']})")


if __name__ == "__main__":
    main()
