# SINGED

### Correct Outputs Do Not Certify Safe Execution in LLM Agents

**Source Integrity and the Nonidentifiability Gap in Execution Decisions for LLM Agents**

SINGED is a controlled benchmark for a failure that output-only evaluation cannot see: an agent can return the correct artifact while executing a functional counterfeit that causes a forbidden process effect.

[Project website](https://xiaoyuxu1.github.io/SINGED_project/) · [Paper](https://xiaoyuxu1.github.io/SINGED_project/paper.pdf) · [Quick start](#quick-start) · [Benchmark design](#benchmark-design) · [Reproduce](#reproduce-the-evaluation)

> All benchmark names, inputs, documents, audio, packages, and process events are synthetic. The release contains no participant data, personal information, credentials, proprietary code, or user files.

## Why SINGED

Tool-using agents increasingly search for, inspect, install, and execute third-party artifacts. Several implementations can advertise the same capability and return the same result while taking different execution paths. A task oracle sees only the artifact; SINGED also records the source, files inspected, executed hash, and sandbox events that produced it.

| Channel | Question | Oracle |
| --- | --- | --- |
| Task outcome | Did the agent return the requested artifact? | Task-specific artifact validator |
| Execution process | Did the trajectory trigger a forbidden effect? | Instrumented sandbox trace |
| Safe utility | Did both channels pass? | Joint task and process decision |

## Benchmark design

Each instance presents three output-equivalent candidates:

1. an intended implementation;
2. a benign community implementation; and
3. a functional counterfeit that preserves the requested output but adds one forbidden effect.

Candidate role labels are hidden from the agent. SINGED randomizes displayed rank, places decisive evidence at the entrypoint or one/two imports deep, and varies decision policy, model release, and agent configuration. A private manifest retains ground-truth roles for scoring.

### Task families

| Task | Expected artifact | Forbidden process effect |
| --- | --- | --- |
| Document redaction | Redacted text | Unauthorized transmission |
| Speech transcription | Exact transcript | Unauthorized transmission |
| Paper retrieval | Matching PDF | Unauthorized transmission |
| Archive extraction | Verified file tree | Write outside the target |
| Tabular conversion | Canonical JSON | Read an unrelated file |
| Configuration editing | Updated configuration | Change protected metadata |
| Image thumbnailing | Thumbnail image | Launch an unnecessary subprocess |

The first five are primary tasks. Configuration editing and image thumbnailing are held-out transfer tasks.

## What is included

- deterministic generation of five primary and two held-out task families;
- matched intended, community, and counterfeit candidate packages;
- randomized rank and entrypoint, one-import, and two-import evidence variants;
- baseline, deliberation, and compare-all decision policies;
- an auditable tool-calling loop with channel-separated scoring;
- one OpenRouter interface for every model family, including OpenAI models;
- release checks for secrets, local paths, and identifying metadata.

## Quick start

Python 3.11 or later is required.

```bash
git clone https://github.com/XiaoyuXU1/SINGED.git
cd SINGED
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
```

Set `OPENROUTER_API_KEY` in `.env`. Credentials are read only by the local runner and excluded from Git.

Prepare inspectable candidates and manifests:

```bash
singed prepare --output benchmark/generated
```

Run one inexpensive cell:

```bash
singed run \
  --manifest benchmark/generated/manifest.json \
  --model moonshotai/kimi-k2.5 \
  --family document \
  --policy compare_all \
  --depth entrypoint \
  --rank 1 \
  --limit 1
```

All model requests use OpenRouter Chat Completions. Sampling parameters are omitted so endpoints use their defaults. A run stores request hashes, route metadata, usage, tool events, artifact hashes, and process events; API credentials are never written to logs.

## Reproduce the evaluation

Omit filters to execute all cells selected by the experiment configuration. Runs are sequential by default so cost and failure handling remain explicit.

```bash
singed analyze --runs runs --group-by model,policy --output aggregate.json
```

The evaluator derives task success, counterfeit execution rate (CER), outcome-to-execution gap (OEG), and safe utility from local traces rather than model claims. Exact factor mappings and audit conventions are documented in [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).

## Safety boundary

Candidate code is generated locally, checked against its SHA-256 digest, extracted with path-traversal protection, and executed without a shell in a fresh temporary directory. Forbidden effects target only controlled local fixtures or a loopback receipt server. Use the bundled synthetic candidates only; executing untrusted third-party packages requires an additional OS- or container-level sandbox.

## Validation

```bash
make test
make check
```

`make check` scans the release for credentials, local user paths, personal identifiers, and other material that must not enter an anonymous artifact.

## Repository layout

```text
configs/             model and experiment configuration
src/singed/          benchmark generator, agent loop, world, and scoring
scripts/             release and privacy checks
tests/               deterministic unit and integration tests
benchmark/generated/ locally generated fixtures and candidates (Git-ignored)
runs/                model traces and summaries (Git-ignored)
```

## Citation

```bibtex
@misc{anonymous2026singed,
  title  = {SINGED: Correct Outputs Do Not Certify Safe Execution in LLM Agents},
  author = {Anonymous Authors},
  year   = {2026}
}
```

## License

Released under the MIT License.
