"""STEP, STL and USDZ of the printed case only. USDZ is metres, Y up, for iPhone Quick Look."""
import os, struct, zlib
import numpy as np
from build123d import export_step, export_stl


def mesh_of(shape, tol):
    P, T = [], []
    for so in shape.solids():
        for f in so.faces():
            try:
                vs, tris = f.tessellate(tol, 0.3)
            except Exception:
                continue
            if not tris:
                continue
            o = len(P)
            P += [(v.X, v.Y, v.Z) for v in vs]
            T += [(o + a, o + b, o + c) for a, b, c in tris]
    return np.array(P, float), np.array(T, np.int64)


def _yup_m(P):
    """mm, Z up -> m, Y up (dial axis up, panel top toward -Z)."""
    q = np.empty_like(P)
    q[:, 0] = P[:, 0] * 0.001
    q[:, 1] = P[:, 2] * 0.001
    q[:, 2] = -P[:, 1] * 0.001
    return q


def _usda(P, T, rgb, opacity, rough):
    Q = _yup_m(P)
    lo, hi = Q.min(0), Q.max(0)
    pts = ", ".join("(%.5f, %.5f, %.5f)" % tuple(p) for p in Q)
    counts = ", ".join(["3"] * len(T))
    idx = ", ".join(str(int(i)) for i in T.ravel())
    r, g, b = rgb
    return f"""#usda 1.0
(
    defaultPrim = "Root"
    metersPerUnit = 1
    upAxis = "Y"
    documentation = "Ed knob-module case v0.1. UTR-8100 clear resin, varnished, dyed Pantone 2577 C. Units: metres."
)
def Xform "Root" (
    kind = "component"
)
{{
    def Scope "Looks"
    {{
        def Material "Resin"
        {{
            token outputs:surface.connect = </Root/Looks/Resin/Preview.outputs:surface>
            def Shader "Preview"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = ({r:.4f}, {g:.4f}, {b:.4f})
                float inputs:opacity = {opacity:.3f}
                float inputs:roughness = {rough:.3f}
                float inputs:metallic = 0
                float inputs:ior = 1.5
                token outputs:surface
            }}
        }}
    }}
    def Mesh "Case" (
        prepend apiSchemas = ["MaterialBindingAPI"]
    )
    {{
        float3[] extent = [({lo[0]:.5f}, {lo[1]:.5f}, {lo[2]:.5f}), ({hi[0]:.5f}, {hi[1]:.5f}, {hi[2]:.5f})]
        int[] faceVertexCounts = [{counts}]
        int[] faceVertexIndices = [{idx}]
        point3f[] points = [{pts}]
        color3f[] primvars:displayColor = [({r:.4f}, {g:.4f}, {b:.4f})]
        uniform token subdivisionScheme = "none"
        uniform bool doubleSided = 1
        rel material:binding = </Root/Looks/Resin>
    }}
}}
"""


def _pack_usdz(path, usda_name, text):
    """Uncompressed zip, file data 64-byte aligned, as Quick Look expects."""
    data = text.encode("utf-8")
    name = usda_name.encode("utf-8")
    crc = zlib.crc32(data) & 0xFFFFFFFF
    base = 30 + len(name)
    pad = (64 - (base % 64)) % 64
    if pad and pad < 4:
        pad += 64
    extra = b"" if pad == 0 else struct.pack("<HH", 0, pad - 4) + b"\0" * (pad - 4)
    local = struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, 0, 0, 0, 0, crc, len(data), len(data), len(name), len(extra))
    local = local + name + extra
    if len(local) % 64:
        raise RuntimeError("USDZ data is not 64-byte aligned")
    cd = struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, 20, 20, 0, 0, 0, 0, crc, len(data), len(data),
                     len(name), len(extra), 0, 0, 0, 0, 0) + name + extra
    eocd = struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, 1, 1, len(cd), len(local) + len(data), 0)
    with open(path, "wb") as f:
        f.write(local)
        f.write(data)
        f.write(cd)
        f.write(eocd)


def export_case(case, D, directory):
    os.makedirs(directory, exist_ok=True)
    rev = D["case_rev"]
    step = os.path.join(directory, f"case-{rev}.step")
    stl = os.path.join(directory, f"case-{rev}.stl")
    usdz = os.path.join(directory, f"case-{rev}.usdz")
    export_step(case, step)
    export_stl(case, stl, tolerance=D["stl_tol"], angular_tolerance=D["stl_ang"])
    P, T = mesh_of(case, D["usdz_tol"])
    rgb = tuple(c / 255.0 for c in D["dye_rgb"])
    _pack_usdz(usdz, f"case-{rev}.usda", _usda(P, T, rgb, D["dye_opacity"], D["dye_rough"]))
    return [step, stl, usdz]
