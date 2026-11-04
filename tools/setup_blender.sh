#!/usr/bin/env bash
# Installs headless Blender (bpy module from PyPI) plus software OpenGL so
# Cycles, EEVEE and Workbench all render without a GPU or display.
# Safe to re-run. Usage: bash tools/setup_blender.sh
set -euo pipefail
VENV=/opt/blender-venv
BPY_VERSION=5.2.3
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq libegl1 libgl1 libgles2 libgl1-mesa-dri libegl-mesa0 \
  libxkbcommon0 libsm6 libxi6 libxxf86vm1 libxfixes3 libxrender1 ffmpeg >/dev/null
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q "bpy==$BPY_VERSION"
"$VENV/bin/python" -c "import bpy; print('Blender', bpy.app.version_string, 'ready')"
# Run scripts with:  EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python your_script.py
