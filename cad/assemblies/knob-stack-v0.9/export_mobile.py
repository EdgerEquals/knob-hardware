"""Knob stack v0.9 -> GLB + USDZ for viewing on an iPhone (Quick Look opens the USDZ; the GLB is for any glTF viewer).
Full assembly and the A-A half-section (near half removed, as iso_section.py; clash volumes in red).
Units: metres (mm x 0.001), Y up (the dial axis), model centred on the dial axis at the PCB front. Colours per part (iso legend)."""
import os, sys, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import knob_stack as ks
import iso_section as iso
from build123d import *
import trimesh
from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf, UsdUtils

def tess(solids, tol=0.03):
    P, T = [], []
    for so in solids:
        for f in so.faces():
            try: vs, tris = f.tessellate(tol, 0.3)
            except Exception: continue
            o = len(P); P += [(v.X, v.Y, v.Z) for v in vs]; T += [(o + a, o + b, o + c) for a, b, c in tris]
    return np.array(P, float), np.array(T, int)

def to_view(P, origin):
    """mm, world (Z up) -> m, Y up; centred on the dial axis at the PCB front."""
    q = (P - origin) * 0.001
    return np.c_[q[:, 0], q[:, 2], -q[:, 1]]

def hex_rgb(h): return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]

def build_sets():
    parts, board, zf, zb, hx, hy, BZ, dz = ks.build_parts()
    origin = np.array([hx, -hy, zf])
    full = [(n, iso.GROUPS[iso.group_of(n)][1], iso.solids_of(s)) for n, s in parts.items()]
    bb = Compound(children=list(parts.values())).bounding_box(); pad = 5; y_cut = -hy
    keep = Pos(bb.min.X - pad, bb.min.Y - pad, bb.min.Z - pad) * Box(bb.max.X - bb.min.X + 2 * pad, y_cut - bb.min.Y + pad, bb.max.Z - bb.min.Z + 2 * pad,
                                                                     align=(Align.MIN, Align.MIN, Align.MIN))
    half = []
    for n, s in parts.items():
        if ks.bbox_overlap(s, keep):
            r = iso.solids_of(s.intersect(keep))
            if r: half.append((n, iso.GROUPS[iso.group_of(n)][1], r))
    for (na, a), (nb, b) in itertools.combinations(parts.items(), 2):
        if not ks.bbox_overlap(a, b): continue
        sol = iso.solids_of(a.intersect(b))
        if sum(x.volume for x in sol) > 1e-3:
            cut = [x for y in sol for x in iso.solids_of(y.intersect(keep))]
            half.append((f"CLASH {na} - {nb}", iso.CLASH, cut or sol))
    return {"knob-stack-v0.9": full, "knob-stack-v0.9-half-section": half}, origin

def safe(n): return "".join(c if c.isalnum() else "_" for c in n).strip("_") or "part"

def write_glb(items, origin, path):
    sc = trimesh.Scene()
    for n, col, sol in items:
        P, T = tess(sol)
        if not len(T): continue
        mat = trimesh.visual.material.PBRMaterial(name=safe(n), baseColorFactor=hex_rgb(col) + [1.0], metallicFactor=0.1, roughnessFactor=0.6)
        m = trimesh.Trimesh(to_view(P, origin), T, process=False, visual=trimesh.visual.TextureVisuals(material=mat))
        sc.add_geometry(m, node_name=safe(n), geom_name=safe(n))
    sc.export(path)

def write_usdz(items, origin, path):
    usdc = path[:-1] + "c"
    st = Usd.Stage.CreateNew(usdc)
    UsdGeom.SetStageUpAxis(st, UsdGeom.Tokens.y); UsdGeom.SetStageMetersPerUnit(st, 1.0)
    root = UsdGeom.Xform.Define(st, "/Root"); st.SetDefaultPrim(root.GetPrim())
    for i, (n, col, sol) in enumerate(items):
        P, T = tess(sol)
        if not len(T): continue
        nm = f"p{i:02d}_{safe(n)}"
        mesh = UsdGeom.Mesh.Define(st, f"/Root/{nm}")
        Q = to_view(P, origin)
        mesh.CreatePointsAttr([Gf.Vec3f(*map(float, q)) for q in Q])
        mesh.CreateFaceVertexCountsAttr([3] * len(T)); mesh.CreateFaceVertexIndicesAttr([int(x) for x in T.ravel()])
        mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
        mesh.CreateDisplayColorAttr([Gf.Vec3f(*hex_rgb(col))])
        mesh.CreateDoubleSidedAttr(True)
        lo, hi = Q.min(0), Q.max(0); mesh.CreateExtentAttr([Gf.Vec3f(*map(float, lo)), Gf.Vec3f(*map(float, hi))])
        mp = f"/Root/Looks/{nm}"
        mat = UsdShade.Material.Define(st, mp)
        sh = UsdShade.Shader.Define(st, mp + "/PBR"); sh.CreateIdAttr("UsdPreviewSurface")
        sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*hex_rgb(col)))
        sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.6); sh.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
        mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(mat)
    st.GetRootLayer().Save()
    ok = UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(usdc), path)
    os.remove(usdc)
    return ok

def check(path):
    if path.endswith(".glb"):
        s = trimesh.load(path); b = s.bounds
        return len(s.geometry), b
    st = Usd.Stage.Open(path); ms = [p for p in st.Traverse() if p.IsA(UsdGeom.Mesh)]
    bc = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default", "render"]); r = bc.ComputeWorldBound(st.GetPseudoRoot()).ComputeAlignedRange()
    nmat = sum(1 for p in st.Traverse() if p.IsA(UsdShade.Material))
    return len(ms), (tuple(r.GetMin()), tuple(r.GetMax())), nmat

if __name__ == "__main__":
    sets, origin = build_sets()
    for name, items in sets.items():
        g = os.path.join(HERE, name + ".glb"); u = os.path.join(HERE, name + ".usdz")
        write_glb(items, origin, g); ok = write_usdz(items, origin, u)
        print(name, "usdz ok", ok)
        print("  glb", os.path.getsize(g), check(g)); print("  usdz", os.path.getsize(u), check(u))
