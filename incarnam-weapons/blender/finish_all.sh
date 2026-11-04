#!/usr/bin/env bash
# Finish every weapon in sequence (bake -> export -> renders -> turntable). Safe to re-run.
set -uo pipefail
cd "$(dirname "$0")"
export EGL_PLATFORM=surfaceless
PY=/opt/blender-venv/bin/python
for w in "$@"; do
  echo "=== $w $(date +%H:%M:%S)"
  $PY "build_$w.py" ${EXTRA_ARGS:-} 2>&1 | grep -vE "^Fra:|EGL Error|Saved:|^\s*Time:|Remaining|DeprecationWarning|use_nodes" | tail -40
  echo "=== $w done rc=${PIPESTATUS[0]} $(date +%H:%M:%S)"
done
echo "=== rig validation"
$PY validate_rigs.py 2>&1 | grep -E "PASS|FAIL|Error"
