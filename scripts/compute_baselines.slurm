#!/bin/bash
#SBATCH --job-name=fl-references
#SBATCH --account=<project>
#SBATCH --constraint=GENOA
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --time=01:00:00
#SBATCH --output=references-%j.out

# "Solo" / "centralised" references of the hands-on (CPU only).
# 6 trainings per configuration (5 solo clients + 1 centralised), 2 threads each.
# Prerequisites, from a login node (compute nodes have no internet access):
#   uv sync
#   uv run python scripts/prepare_data.py
# Submit from the repository root: sbatch scripts/compute_baselines.slurm
# Replace <project> with your Adastra project before submitting (do not commit it).

set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"

export OMP_NUM_THREADS=2
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1

# Use the project's Python directly: `uv run` could try a network sync.
srun --cpu-bind=cores .venv/bin/python scripts/compute_baselines.py --dataset all --workers 6 --threads 2
