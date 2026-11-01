"""Renders and 3D exports for a generated KiCad board. Run after make_board.py [--route].

Writes, next to the project:
  <name>-schematic.pdf
  <name>-copper-top.png / -copper-bottom.png
  <name>-3d-top.png / -3d-bottom.png
  <name>.step   (already produced by make_board; refreshed here)
  <name>.usdz   metres, Y up, for iPhone AR Quick Look
"""
import os, sys, subprocess, zipfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))

def _run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout[-2000:] + r.stderr[-2000:])
        raise SystemExit(f"failed: {' '.join(args[:6])}")
    return r

def copper_png(pcb, out, layers):
    svg = out.replace(".png", ".svg")
    _run(["kicad-cli", "pcb", "export", "svg", "--exclude-drawing-sheet", "--fit-page-to-board",
          "--page-size-mode", "2", "-l", layers, "--mode-single", "-o", svg, pcb])
    _run(["rsvg-convert", "-w", "1600", "-o", out, svg])

def render3d(pcb, out, side):
    _run(["kicad-cli", "pcb", "render", "--side", side, "--quality", "high", "--background", "opaque",
          "-w", "1600", "-h", "2200", "--zoom", "1.05", "-o", out, pcb])

def step_to_usdz(step, usdz):
    """Tessellate the STEP (mm) into a Y-up USDZ in metres."""
    import numpy as np, cascadio, tempfile
    obj = step + ".obj"
    cascadio.step_to_obj(step, obj, tol_linear=0.2, tol_angular=0.6, use_colors=False)
    verts, faces = [], []
    for line in open(obj):
        if line.startswith("v "):
            verts.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            idx = []
            for tok in line.split()[1:]:
                idx.append(int(tok.split("/")[0]) - 1)
            if len(idx) == 3: faces.append(idx)
            elif len(idx) > 3:
                for k in range(1, len(idx) - 1): faces.append([idx[0], idx[k], idx[k + 1]])
    os.remove(obj)
    v, f = np.asarray(verts, dtype="float64"), np.asarray(faces, dtype="int64")
    # OBJ from cascadio is in the STEP units (mm)
    v *= 0.001
    # KiCad STEP is Z up, Y... kicad uses Z up, X right, Y depth. Map to Y-up: (x, z, -y)
    x, y, z = v[:, 0], v[:, 1], v[:, 2]
    v = np.stack([x, z, -y], axis=1)
    f = np.asarray(f, dtype="int64")
    lines = ["#usda 1.0", "(", "    metersPerUnit = 1", '    upAxis = "Y"', "    defaultPrim = \"Board\"", ")",
             'def Xform "Board" {', '    def Mesh "PCB" {', "        int[] faceVertexCounts = [" + ", ".join(["3"] * len(f)) + "]",
             "        int[] faceVertexIndices = [" + ", ".join(str(int(i)) for i in f.reshape(-1)) + "]",
             "        point3f[] points = [" + ", ".join(f"({p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f})" for p in v) + "]",
             "        uniform token subdivisionScheme = \"none\"",
             "        color3f[] primvars:displayColor = [(0.15, 0.45, 0.22)]",
             "        uniform token primvars:displayColor:interpolation = \"constant\"",
             "    }", "}"]
    usda = "\n".join(lines) + "\n"
    tmp = usdz + ".usda"
    open(tmp, "w").write(usda)
    with zipfile.ZipFile(usdz, "w") as z:
        # Apple Quick Look wants the first USD uncompressed
        z.write(tmp, os.path.basename(usdz).replace(".usdz", ".usda"), compress_type=zipfile.ZIP_STORED)
    os.remove(tmp)

def export(name, kdir):
    pcb = os.path.join(kdir, name + ".kicad_pcb")
    sch = os.path.join(kdir, name + ".kicad_sch")
    # point 3D models at the STEP files KiCad 9 actually ships
    original = open(pcb).read()
    text = original.replace(".wrl", ".step").replace("${KICAD6_3DMODEL_DIR}", "${KICAD9_3DMODEL_DIR}")
    if text != original:
        open(pcb, "w").write(text)
    outdir = os.path.dirname(kdir)
    base = os.path.join(outdir, name)
    _run(["kicad-cli", "sch", "export", "pdf", "--output", base + "-schematic.pdf", sch])
    copper_png(pcb, base + "-copper-top.png", "F.Cu,F.Silkscreen,F.Mask,Edge.Cuts")
    copper_png(pcb, base + "-copper-bottom.png", "B.Cu,B.Silkscreen,B.Mask,Edge.Cuts")
    render3d(pcb, base + "-3d-top.png", "top")
    render3d(pcb, base + "-3d-bottom.png", "bottom")
    step = base + ".step"
    _run(["kicad-cli", "pcb", "export", "step", "--grid-origin", "--force", "--no-dnp",
          "-D", "KICAD9_3DMODEL_DIR=/usr/share/kicad/3dmodels", "-o", step, pcb])
    step_to_usdz(step, base + ".usdz")
    print("exported", base)

if __name__ == "__main__":
    export(sys.argv[1], sys.argv[2])
