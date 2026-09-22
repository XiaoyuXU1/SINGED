<div align="center">

# SINGED

## Correct Outputs Do Not Certify Safe Execution in LLM Agents

**Source Integrity and the Nonidentifiability Gap in Execution Decisions for LLM Agents**

[![Project](https://img.shields.io/badge/Project-Website-a7ff4d?style=for-the-badge&labelColor=111812)](https://xiaoyuxu1.github.io/SINGED_project/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-4f8e25?style=for-the-badge&labelColor=111812)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-f2f0e8?style=for-the-badge&labelColor=111812)](LICENSE)

### Xiaoyu Xu<sup>1†</sup> · Zi Liang<sup>1†</sup> · Minxin Du<sup>1*</sup> · Qipeng Xie<sup>1</sup> · Qingqing Ye<sup>1</sup> · Yuyuan Li<sup>2</sup> · Haibo Hu<sup>1*</sup>

<sup>1</sup> Hong Kong Polytechnic University &nbsp;&nbsp; <sup>2</sup> Hangzhou Dianzi University<br>
<sup>†</sup> Equal contribution &nbsp;&nbsp; <sup>*</sup> Corresponding authors

**[Project website](https://xiaoyuxu1.github.io/SINGED_project/)** · **[Paper](https://xiaoyuxu1.github.io/SINGED_project/paper.pdf)** · **[Quick start](#quick-start)** · **[Reproduce](#reproduce-the-evaluation)**

<br>

**SINGED evaluates a failure that output-only benchmarks cannot see: an agent can return the correct artifact while executing a functional counterfeit that causes a forbidden process effect.**

</div>

<p align="center">
  <img src="docs/assets/framework.png" width="100%" alt="SINGED framework">
</p>

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

<p align="center">
  <img src="docs/assets/benchmark.png" width="100%" alt="Matched and auditable benchmark construction">
</p>

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

## Main findings

- **Rank concentrates risk.** The original study records 27/60 counterfeit executions when the counterfeit ranks first and none at later ranks.
- **Comparison interrupts early commitment.** Mandatory three-way comparison removes all matched rank-one failures when decisive evidence is visible.
- **Choice can mask execution willingness.** Seven releases with zero CER under three-source choice still execute the counterfeit in 55/175 single-source cells after benign alternatives are removed.

<p align="center">
  <img src="docs/assets/mechanism.png" width="100%" alt="Effects of rank, inspection path, decision rule, and evidence depth">
</p>

<table>
  <tr>
    <td width="40%" align="center"><img src="docs/assets/single-source.png" width="100%" alt="Single-source stress test"><br><b>Single-source stress test</b></td>
    <td width="60%" align="center"><img src="docs/assets/transfer.png" width="100%" alt="Transfer across tasks, agent configurations, and model releases"><br><b>Transfer across tasks and systems</b></td>
  </tr>
</table>

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

Candidate code is generated locally, checked against its SHA-256 digest, extracted with path-traversal protection, and executed without a shell in a fresh temporary directory. Forbidden effects target only controlled local fixtures or a loopback receipt server. Executing untrusted third-party packages requires an additional OS- or container-level sandbox.

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
@misc{xu2026singed,
  title  = {SINGED: Correct Outputs Do Not Certify Safe Execution in LLM Agents},
  author = {Xu, Xiaoyu and Liang, Zi and Du, Minxin and Xie, Qipeng and Ye, Qingqing and Li, Yuyuan and Hu, Haibo},
  year   = {2026}
}
```

## License

Released under the MIT License.
