# references

- `calibration/<phase>/`: calibration results (Adastra, 5 CPUs, 10 rounds): `summary.csv`
  and `curves.png` for the `hparams`, `noniid`, `fedprox`, `fedprox-ep5` and
  `participation` phases. Produced by `scripts/calibrate.py`.
- `<key>.json` (to come): "solo" and "centralised" baselines read by the dashboard,
  produced by `scripts/compute_baselines.py` (or `sbatch scripts/compute_baselines.slurm`
  on Adastra). Status: OPEN, not yet computed on real data.
