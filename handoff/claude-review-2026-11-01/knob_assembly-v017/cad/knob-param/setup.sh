#!/usr/bin/env bash
# Fresh Linux VM setup for knob-param.  Usage:  bash cad/knob-param/setup.sh [venv-dir]
# - creates a venv (default: cad/knob-param/.venv), installs pinned requirements
# - installs the headless-GL system libs VTK needs (apt, if sudo/root is available)
# KiCad is NOT required: the main-PCB STEP used by --full is committed in
# knobparam/electronics/kicad/knob-main-pcb/. kicad-cli is only needed to regenerate boards/STEP.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${1:-$HERE/.venv}"
PY="${PYTHON:-python3}"

if command -v apt-get >/dev/null 2>&1; then
  SUDO=""; [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1 && SUDO="sudo"
  if [ "$(id -u)" -eq 0 ] || [ -n "$SUDO" ]; then
    $SUDO apt-get update -qq || true
    $SUDO apt-get install -y -qq python3-venv libgl1 libegl1 libxrender1 libxext6 libsm6 libglu1-mesa libosmesa6 xvfb >/dev/null || \
      echo "WARN: some apt packages failed; rendering may need xvfb-run or OSMesa"
  else
    echo "WARN: no root/sudo; skipping apt. Rendering needs libgl1/libegl1/libxrender1 (or xvfb)."
  fi
fi

"$PY" -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$HERE/requirements.txt"
"$VENV/bin/python" "$HERE/build.py" --contract >/dev/null && echo "contract OK"
echo "Done. Try:  $VENV/bin/python $HERE/build.py --sub control_dial --preview"
echo "Full:       $VENV/bin/python $HERE/build.py --render     (assembly agent)"
echo "If the render fails with an OpenGL/display error:  xvfb-run -a $VENV/bin/python $HERE/build.py --render"
