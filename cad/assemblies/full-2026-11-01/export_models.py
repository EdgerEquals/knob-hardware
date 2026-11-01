"""STEP, STL and USDZ for the full assembly and each sub-assembly.

USDZ is metres, Y up, one mesh and one PreviewSurface per part (Quick Look).
STL is one mesh per assembly (the format has no part colours). STEP is the BRep.
Mesh chord tolerance is MESH_TOL mm so the files stay small enough for git without LFS.
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "cad", "knob-param")))

from build123d import Compound, export_step
import trimesh
from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf, UsdUtils

import render_full as F
from knobparam.common import model
from knobparam.assembly.build import build_all
from knobparam.assembly import render as R

OUT = os.path.join(HERE, "exports")
MESH_TOL = 0.22
MESH_ANG = 0.5


def solids_of(s):
    if s is None:
        return []
    try:
        found = list(s.solids())
    except Exception:
        found = []
    return found or [s]


def tessellate(shape):
    P, T = [], []
    for so in solids_of(shape):
        for f in so.faces():
            try:
                vs, tris = f.tessellate(MESH_TOL, MESH_ANG)
            except Exception:
                continue
            if not tris:
                continue
            o = len(P)
            P += [(v.X, v.Y, v.Z) for v in vs]
            T += [(o + a, o + b, o + c) for a, b, c in tris]
    if not T:
        return None
    return np.array(P, float), np.array(T, np.int64)


def to_metres_y_up(P):
    """Knob frame is millimetres, Z up, origin on the dial axis at the PCB front."""
    q = P * 0.001
    return np.c_[q[:, 0], q[:, 2], -q[:, 1]]


def safe(n):
    return "".join(c if c.isalnum() else "_" for c in n).strip("_") or "part"


def hex_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def colour(name):
    return R.GROUPS[R.group_of(name)][1]


def write_step(parts, path):
    solids = [s for s in parts.values() if s is not None]
    export_step(Compound(children=solids), path)


def write_stl(meshes, path):
    bodies = []
    for _n, P, T in meshes:
        if len(T) == 0:
            continue
        bodies.append(trimesh.Trimesh(P, T, process=False))
    if not bodies:
        return
    trimesh.util.concatenate(bodies).export(path)


def write_usdz(named, path):
    usdc = path[:-1] + "c"
    st = Usd.Stage.CreateNew(usdc)
    UsdGeom.SetStageUpAxis(st, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(st, 1.0)
    root = UsdGeom.Xform.Define(st, "/Root")
    st.SetDefaultPrim(root.GetPrim())
    for i, (n, P, T) in enumerate(named):
        if len(T) == 0:
            continue
        nm = f"p{i:03d}_{safe(n)[:40]}"
        mesh = UsdGeom.Mesh.Define(st, f"/Root/{nm}")
        Q = to_metres_y_up(P)
        mesh.CreatePointsAttr([Gf.Vec3f(*map(float, q)) for q in Q])
        mesh.CreateFaceVertexCountsAttr([3] * len(T))
        mesh.CreateFaceVertexIndicesAttr([int(x) for x in T.ravel()])
        mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
        col = hex_rgb(colour(n))
        mesh.CreateDisplayColorAttr([Gf.Vec3f(*col)])
        mesh.CreateDoubleSidedAttr(True)
        lo, hi = Q.min(0), Q.max(0)
        mesh.CreateExtentAttr([Gf.Vec3f(*map(float, lo)), Gf.Vec3f(*map(float, hi))])
        mp = f"/Root/Looks/{nm}"
        mat = UsdShade.Material.Define(st, mp)
        sh = UsdShade.Shader.Define(st, mp + "/PBR")
        sh.CreateIdAttr("UsdPreviewSurface")
        sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*col))
        sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.55)
        sh.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.05)
        mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(mat)
    st.GetRootLayer().Save()
    ok = UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(usdc), path)
    os.remove(usdc)
    if not ok:
        raise RuntimeError(f"USDZ package failed: {path}")


def export_set(name, parts, cache):
    os.makedirs(OUT, exist_ok=True)
    step = os.path.join(OUT, f"{name}.step")
    stl = os.path.join(OUT, f"{name}.stl")
    usdz = os.path.join(OUT, f"{name}.usdz")
    print(f"STEP {name} ({len(parts)} parts)", flush=True)
    write_step(parts, step)
    meshes = []
    for n, s in parts.items():
        if n not in cache:
            cache[n] = tessellate(s)
        if cache[n] is not None:
            meshes.append((n, *cache[n]))
    print(f"STL/USDZ {name} ({len(meshes)} meshes)", flush=True)
    write_stl(meshes, stl)
    write_usdz(meshes, usdz)
    return step, stl, usdz


def main():
    os.makedirs(OUT, exist_ok=True)
    D = model.derive(model.default_params())
    print("building knob", flush=True)
    parts, _stats, _keys, owner = build_all(D)
    F.patch_groups()
    print("building joystick", flush=True)
    JP, JParts = F.load_joystick()
    J = JP.derive(JP.P)
    js = F.place_joystick(JParts.build(J), J["place_y"])
    face = {"assembly faceplate (10HP x 3U)": F.faceplate_panel(D, J)}
    full = dict(parts)
    full.update(js)
    full.update(face)
    cache = {}
    paths = []
    paths += export_set("full", full, cache)
    for sub in ("main_knob", "control_dial", "base_drive", "under_pcb", "electronics"):
        sub_parts = {n: s for n, s in parts.items() if owner.get(n) == sub}
        paths += export_set(sub, sub_parts, cache)
    # joystick in its own frame, including the local faceplate proxy it already builds
    js_local = {n: s for n, s in JParts.build(J).items() if s is not None and n != "main PCB (proxy, local patch)"}
    paths += export_set("joystick", js_local, {})
    lines = ["# Exports", "", "Mesh chord 0.22 mm. USDZ is metres, Y up, one material per part. STL has no colours. No Git LFS.", ""]
    for p in paths:
        lines.append(f"- `{os.path.relpath(p, os.path.join(HERE, '..', '..', '..'))}`  {os.path.getsize(p) / 1e6:.2f} MB")
        print(f"{os.path.getsize(p)/1e6:8.2f} MB  {p}", flush=True)
    open(os.path.join(OUT, "README.md"), "w").write("\n".join(lines) + "\n")
    print("done", flush=True)


if __name__ == "__main__":
    main()
