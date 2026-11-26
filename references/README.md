# references

- `calibration/<phase>/`: calibration results (Adastra, 5 CPUs, 10 rounds): `summary.csv`
  and `curves.png` for the `hparams`, `noniid`, `fedprox`, `fedprox-ep5` and
  `participation` phases. Produced by `scripts/calibrate.py`.
- `calibration/commcomp/`: rounds × local epochs at an equal budget of 20 local epochs
  (20×1, 10×2, 5×4, 2×10), IID and Dirichlet 0.1, Fashion-MNIST. Measured on a 4-CPU
  Linux machine, not on Adastra: accuracies are comparable, times are not.
- `<key>.json` (to come): "solo" and "centralised" baselines read by the dashboard,
  produced by `scripts/compute_baselines.py` (or `sbatch scripts/compute_baselines.slurm`
  on Adastra). Status: OPEN, not yet computed on real data.
