# Generated benchmark data

Run `singed prepare --output benchmark/generated` to create the controlled
fixtures, candidate archives, schedules, and evaluator manifests. Generated
files are excluded from Git so that the checked-in artifact remains compact and
every public instance can be reproduced deterministically from the seed.

The separate public-package slice is prepared with
`experiments/public_packages/prepare.py`. Its version and license lockfile,
runner, analyzer, and audited aggregate results are checked in under that
directory; downloaded and modified archives remain local and Git-ignored.
