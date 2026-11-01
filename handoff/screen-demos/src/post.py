import subprocess, os, glob
from PIL import Image, ImageDraw, ImageFont
from common import *
PPI = 460; PXMM = PPI/25.4
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"; FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TAGS = ["-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
        "-color_trc", "iec61966-2-1", "-colorspace", "bt709", "-movflags", "+faststart"]
def run(a): subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + a, check=True)
os.makedirs(f"{OUT}/gif", exist_ok=True); os.makedirs(f"{OUT}/iphone-actual-size", exist_ok=True)
clips = {"round_a_mandelbrot_knob_zoom": ROUND, "round_b_liquid_morph": ROUND, "round_c_fifths_radar": ROUND,
         "joy_d_curl_flow": RECT, "joy_e_julia_stick": RECT, "joy_d_curl_flow_IPS-sim": RECT}
# IPS reference look (for the unspecified bottom screen): ~1000:1 so black is lifted to ~code 11, sRGB
run(["-i", f"{OUT}/joy_d_curl_flow.mp4", "-vf", "lutrgb=r='val*0.957+11':g='val*0.957+11':b='val*0.957+12'"] + TAGS + [f"{OUT}/joy_d_curl_flow_IPS-sim.mp4"])
for name, S in clips.items():
    src = f"{OUT}/{name}.mp4"
    run(["-i", src, "-vf", "fps=12,split[a][b];[a]palettegen=max_colors=160:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle", f"{OUT}/gif/{name}.gif"])
    pw, ph = round(S["mm"][0]*PXMM/2)*2, round(S["mm"][1]*PXMM/2)*2
    cap = Image.new("RGBA", (1180, 2556), (0, 0, 0, 0)); d = ImageDraw.Draw(cap)
    y0 = 1278 + ph//2 + 70
    d.text((590, y0), "actual size", fill=(200, 200, 200, 255), font=ImageFont.truetype(FB, 44), anchor="mm")
    d.text((590, y0 + 60), f"{S['part']}", fill=(140, 140, 140, 255), font=ImageFont.truetype(F, 28), anchor="mm")
    d.text((590, y0 + 100), f"active {S['mm'][0]:.2f} x {S['mm'][1]:.2f} mm, {S['w']}x{S['h']} px native", fill=(140, 140, 140, 255), font=ImageFont.truetype(F, 28), anchor="mm")
    d.text((590, 2556 - 120), f"scaled for a 460 ppi iPhone (1179x2556, iPhone 15/16 class): {pw}x{ph} px on screen", fill=(110, 110, 110, 255), font=ImageFont.truetype(F, 24), anchor="mm")
    d.text((590, 2556 - 84), "play full-screen, don't pinch-zoom; brightness ~50-60%, True Tone off", fill=(110, 110, 110, 255), font=ImageFont.truetype(F, 24), anchor="mm")
    cap.save("/tmp/cap.png")
    run(["-i", src, "-i", "/tmp/cap.png", "-filter_complex",
         f"[0:v]scale={pw}:{ph}:flags=lanczos,pad=1180:2556:(ow-iw)/2:(oh-ih)/2:black[v];[v][1:v]overlay=0:0"] + TAGS + [f"{OUT}/iphone-actual-size/{name}_iphone460ppi.mp4"])
    print("post", name, flush=True)
# showcase: round above, joystick screen below, true relative scale (16 px/mm), dark module face
PX = 12; CW, CH = 720, 1280
rd = round(35.41*PX/2)*2; jw, jh = round(35.57*PX/2)*2, round(21.84*PX/2)*2
bg = Image.new("RGBA", (CW, CH), (14, 14, 18, 255)); d = ImageDraw.Draw(bg)
cy1, cy2 = 400, 900
R = 41.65*PX/2; d.ellipse([CW/2-R, cy1-R, CW/2+R, cy1+R], fill=(0, 0, 0, 255), outline=(60, 60, 70, 255), width=3)          # knob glass Ø41.65
bw, bh = 41.62*PX, 26.74*PX; d.rounded_rectangle([CW/2-bw/2, cy2-bh/2, CW/2+bw/2, cy2+bh/2], 10, fill=(0, 0, 0, 255), outline=(60, 60, 70, 255), width=3)
d.text((CW/2, 60), "Both screens, true relative scale", fill=(170, 170, 180, 255), font=ImageFont.truetype(FB, 30), anchor="mm")
d.text((CW/2, cy1+R+28), '1.39" round AMOLED 454x454 (knob)', fill=(120, 120, 130, 255), font=ImageFont.truetype(F, 22), anchor="mm")
d.text((CW/2, cy2+bh/2+28), '1.64" AMOLED 456x280 (joystick top)', fill=(120, 120, 130, 255), font=ImageFont.truetype(F, 22), anchor="mm")
bg.save("/tmp/bg.png")
mk = Image.new("L", (rd, rd), 0); ImageDraw.Draw(mk).ellipse([0, 0, rd-1, rd-1], fill=255); mk.save("/tmp/mk.png")
parts = []
for i, (ra, jo) in enumerate([("round_c_fifths_radar", "joy_d_curl_flow"), ("round_a_mandelbrot_knob_zoom", "joy_e_julia_stick"), ("round_b_liquid_morph", "joy_d_curl_flow")]):
    p = f"/tmp/show{i}.mp4"
    run(["-loop", "1", "-framerate", "30", "-i", "/tmp/bg.png", "-i", f"{OUT}/{ra}.mp4", "-i", f"{OUT}/{jo}.mp4", "-loop", "1", "-i", "/tmp/mk.png", "-filter_complex",
         f"[1:v]scale={rd}:{rd}:flags=lanczos,format=rgba[r0];[3:v]format=gray[m];[r0][m]alphamerge[r];[2:v]scale={jw}:{jh}:flags=lanczos[j];[0:v][r]overlay={(CW-rd)//2}:{cy1-rd//2}:shortest=1[t];[t][j]overlay={(CW-jw)//2}:{cy2-jh//2}:shortest=1,format=yuv420p",
         "-t", "10", "-r", "30"] + TAGS + [p]); parts.append(p)
open("/tmp/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
run(["-f", "concat", "-safe", "0", "-i", "/tmp/list.txt", "-crf", "20"] + TAGS[:1+1+2] + ["-pix_fmt", "yuv420p", "-x264-params", "colorprim=bt709:transfer=iec61966-2-1:colormatrix=bt709", "-movflags", "+faststart", f"{OUT}/showcase_module_both_screens.mp4"])
run(["-i", f"{OUT}/showcase_module_both_screens.mp4", "-vf", "fps=10,scale=300:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4", f"{OUT}/gif/showcase_module_both_screens.gif"])
print("post done")
