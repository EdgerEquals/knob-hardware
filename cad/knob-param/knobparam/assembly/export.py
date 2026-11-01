"""Exports from one build: STEP (named + coloured assembly), STL (one per part, for PCBWay quotes), USDZ (iPhone AR Quick Look).
Colours come from render.GROUPS so the AR model matches the section PNGs. Meshes are cached per part key, so a re-export after
a one-part change only re-tessellates that part. USD needs `pip install usd-core` (Pixar, TOST/Apache-2.0-style licence)."""
import os, re, hashlib, json
import numpy as np
from ..common.cache import CACHE

CLEAR = ("knob body", "control dial", "thrust carrier", "Risley", "screen carrier")   # [Ed] clear-resin parts: see-through in AR
OPACITY = 0.35                                                                           # [A]

def _colour(name):
    from .render import GROUPS
    for _, hexc, match in GROUPS:
        if match(name): return hexc
    return "#b0bec5"

def _rgb(hexc): return tuple(int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
def _safe(name): return re.sub(r"[^A-Za-z0-9_]", "_", name).strip("_") or "part"

def mesh(name, shape, key, tol=0.02, ang=0.2):
    """(V[n,3] mm, F[m,3]) for one part, cached on its build key + tolerances."""
    p = os.path.join(CACHE, "mesh_" + hashlib.sha1(f"{key}|{tol}|{ang}".encode()).hexdigest()[:16] + ".npz")
    if os.path.exists(p):
        z = np.load(p); return z["v"], z["f"]
    v, f = shape.tessellate(tol, ang)
    V = np.array([(q.X, q.Y, q.Z) for q in v], dtype=np.float32); F = np.array(f, dtype=np.int32).reshape(-1, 3)
    os.makedirs(CACHE, exist_ok=True); np.savez(p, v=V, f=F); return V, F

def step(parts, path):
    from build123d import Compound, Color, export_step
    kids = []
    for n, s in parts.items():
        c = s.moved(s.location) if hasattr(s, "moved") else s
        c.label = n; c.color = Color(*_rgb(_colour(n)), OPACITY if any(k in n for k in CLEAR) else 1.0); kids.append(c)
    export_step(Compound(children=kids, label=os.path.splitext(os.path.basename(path))[0]), path)

def stl(parts, folder, tol=0.01, ang=0.1):
    from build123d import export_stl
    os.makedirs(folder, exist_ok=True)
    for n, s in parts.items(): export_stl(s, os.path.join(folder, _safe(n) + ".stl"), tolerance=tol, angular_tolerance=ang)

def usdz(parts, keys, path, tol=0.02, ang=0.2):
    """Metres, Y-up (AR Quick Look convention), one Mesh + UsdPreviewSurface per part, then the ARKit packager + checker."""
    from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf, Vt, UsdUtils
    usda = os.path.splitext(path)[0] + ".usdc"
    st = Usd.Stage.CreateNew(usda)
    UsdGeom.SetStageUpAxis(st, UsdGeom.Tokens.y); UsdGeom.SetStageMetersPerUnit(st, 1.0)
    root = UsdGeom.Xform.Define(st, "/knob"); st.SetDefaultPrim(root.GetPrim())
    mats = {}
    for n, s in parts.items():
        V, F = mesh(n, s, keys.get(n, n), tol, ang)
        if not len(F): continue
        Vy = np.stack([V[:, 0], V[:, 2], -V[:, 1]], 1) * 1e-3          # Z-up mm -> Y-up m
        m = UsdGeom.Mesh.Define(st, f"/knob/{_safe(n)}")
        m.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(Vy.astype(np.float32)))
        m.CreateFaceVertexCountsAttr(Vt.IntArray.FromNumpy(np.full(len(F), 3, dtype=np.int32)))
        m.CreateFaceVertexIndicesAttr(Vt.IntArray.FromNumpy(F.ravel()))
        m.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)              # flat CAD facets; no Catmull-Clark smoothing
        lo, hi = Vy.min(0), Vy.max(0); m.CreateExtentAttr([Gf.Vec3f(*map(float, lo)), Gf.Vec3f(*map(float, hi))])
        hexc = _colour(n); clear = any(k in n for k in CLEAR); mk = (hexc, clear)
        if mk not in mats:
            mp = f"/knob/Looks/m{len(mats)}"; mat = UsdShade.Material.Define(st, mp)
            sh = UsdShade.Shader.Define(st, mp + "/s"); sh.CreateIdAttr("UsdPreviewSurface")
            sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*_rgb(hexc)))
            sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.15 if clear else 0.5)
            sh.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(OPACITY if clear else 1.0)
            mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface"); mats[mk] = mat
        UsdShade.MaterialBindingAPI.Apply(m.GetPrim()).Bind(mats[mk])
    st.GetRootLayer().Save()
    ok = UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(usda), path)
    return ok, verify_usdz(path)

def verify_usdz(path):
    """Self-check (usd-core 0.26 dropped UsdUtils.ComplianceChecker; `usdchecker --arkit` from a full USD build is stricter)."""
    import zipfile
    from pxr import Usd, UsdGeom
    st = Usd.Stage.Open(path); bb = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default"]).ComputeWorldBound(st.GetDefaultPrim()).GetRange()
    z = zipfile.ZipFile(path); names = z.namelist()
    return dict(default_prim=str(st.GetDefaultPrim().GetPath()), up=UsdGeom.GetStageUpAxis(st), m_per_unit=UsdGeom.GetStageMetersPerUnit(st),
                meshes=sum(1 for p in st.Traverse() if p.IsA(UsdGeom.Mesh)), size_mm=[round(x * 1e3, 1) for x in bb.GetSize()],
                first_file=names[0], stored=all(i.compress_type == zipfile.ZIP_STORED for i in z.infolist()), mb=round(os.path.getsize(path) / 1e6, 1))
