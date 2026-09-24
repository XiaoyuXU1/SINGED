# Public-package transfer slice

This frozen 324-cell slice tests SINGED in version-pinned public-package source
trees. It covers three transformation domains, nine packages, three displayed
ranks, six current model releases, and two decision policies. Within each
domain, role rotation places a controlled loopback-only probe into each package
in turn while keeping versions, inputs, canonical outputs, and schedules fixed.

The experiment does not claim that the upstream packages are malicious. The
probe exists only in locally modified archives and can reach only the benchmark's
loopback receipt server inside the sandbox.

## Reproduce

Place the archives named in `package_lock.json` in a local download directory,
then run:

```bash
python experiments/public_packages/prepare.py --downloads <archive-directory>
python experiments/public_packages/preflight.py
python experiments/public_packages/run_batch.py --workers 4
python experiments/public_packages/analyze.py
```

Generated candidates and raw runs are Git-ignored. The checked-in `results/`
directory contains the audited aggregates reported in the paper.

## Headline result

Deliberation executes the counterfeit in 36/162 cells and compare-all in 26/162
cells. The 6.2-point CER difference has a 95% clustered interval from -0.6 to
13.0 points. Both policies preserve the displayed-rank gradient, showing that
rank sensitivity transfers while the aggregate comparison benefit remains
uncertain in this slice.
