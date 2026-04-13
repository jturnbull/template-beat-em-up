#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${FAL_KEY:-}" ]]; then
  echo "FAL_KEY is not set." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_ROOT="${1:-$ROOT_DIR/outputs/reskin/stage_01/backhalf_variants}"

TASKS=(
  "docs/reskin/tasks/backgrounds/stage_01/stage_elements/gates/tori_gate/tori_gate_back.md"
  "docs/reskin/tasks/backgrounds/stage_01/stage_elements/gates/tori_gate/tori_gate_front.md"
  "docs/reskin/tasks/backgrounds/stage_01/stage_elements/tax_man_area/brick_gate/brick_gate_back.md"
  "docs/reskin/tasks/backgrounds/stage_01/stage_elements/tax_man_area/brick_gate/brick_gate_front.md"
  "docs/reskin/tasks/backgrounds/stage_01/stage_elements/tax_man_area/brick_gate/tax_man_doors_1.md"
  "docs/reskin/tasks/backgrounds/stage_01/stage_elements/tax_man_area/brick_gate/tax_man_doors_2.md"
  "docs/reskin/tasks/backgrounds/stage_01/stage_elements/tax_man_area/tax_man_black_marble.md"
  "docs/reskin/tasks/backgrounds/stage_01/stage_elements/tax_man_area/tax_man_floor_chess.md"
  "docs/reskin/tasks/backgrounds/stage_01/stage_elements/tax_man_area/tax_man_windows.md"
)

cd "$ROOT_DIR"

for task in "${TASKS[@]}"; do
  rel_dir="$(dirname "${task#docs/reskin/tasks/}")"
  task_name="$(basename "$task" .md)"
  out_dir="$OUTPUT_ROOT/$rel_dir/$task_name"

  echo "Generating 4 options for $task"
  python3 scripts/fal_reskin_generate.py \
    --task "$task" \
    --num-images 4 \
    --alpha-from-source \
    --output-dir "$out_dir"
done

echo "Saved outputs under $OUTPUT_ROOT"
