import numpy as np, subprocess, os
FPS = 30
OUT = "/workspace/screen-demos"
# Screen definitions (from the knob-hardware repo, see README)
ROUND = dict(name="round", w=454, h=454, mm=(35.41, 35.41), part='Kingtech PV13904PY24G-V01 1.39" round AMOLED (RM69330)')
RECT  = dict(name="joy",   w=456, h=280, mm=(35.57, 21.84), part='DWO DO0164FMST05 1.64" AMOLED, landscape 456x280')

def amoled(img):
    """Panel model for AMOLED: true black (0), sRGB-clipped (no extra saturation), 8-bit."""
    return (np.clip(img, 0, 1) ** (1/2.2) * 255 + 0.5).astype(np.uint8) if img.dtype != np.uint8 else img

def round_mask(w):
    y, x = np.mgrid[0:w, 0:w] + 0.5
    r = np.hypot(x - w/2, y - w/2)
    return np.clip(w/2 - r + 0.5, 0, 1)[..., None]   # anti-aliased circle

class Writer:
    """Takes linear-light float RGB frames; writes sRGB-tagged H.264."""
    def __init__(self, path, w, h):
        self.p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
            "-pix_fmt", "yuv420p", "-x264-params", "colorprim=bt709:transfer=iec61966-2-1:colormatrix=bt709",
            "-color_range", "tv", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
    def write(self, lin):
        self.p.stdin.write(amoled(lin).tobytes())
    def close(self):
        self.p.stdin.close(); self.p.wait()

def palette(t, a, b, c, d):
    """Inigo Quilez cosine palette, returns linear-ish 0..1."""
    return a + b * np.cos(2*np.pi*(c*t[..., None] + d))
