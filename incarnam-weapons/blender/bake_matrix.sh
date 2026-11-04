#!/usr/bin/env bash
# Bake + export every race x category (skips ones already exported and Iop bespoke). Resumable.
cd "$(dirname "$0")"
export EGL_PLATFORM=surfaceless
PY=/opt/blender-venv/bin/python
for r in $(ls lib/kit/races | grep -v '^_' | grep '\.py$' | sed 's/\.py//'); do
  for c in fists staff spear sword greatsword gun dagger scythe katana dual_blades chain blunt; do
    if [ -f "logs/done_${r}_${c}" ]; then continue; fi
    mkdir -p logs
    if $PY build_matrix.py --race $r --cat $c > logs/${r}_${c}.log 2>&1; then touch logs/done_${r}_${c}; echo "ok $r $c"; else echo "FAIL $r $c"; fi
  done
done
echo ALLDONE
