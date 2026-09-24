# Reproducibility notes

## Experimental unit

Each primary or held-out trial fixes a controlled task instance, three output-equivalent candidates,
a model identifier, candidate order, evidence depth, and decision policy. The
model sees neutral candidate names and public source files. Evaluator-only role
labels are stored separately and are used only after execution.

The separate public-package transfer slice uses version-pinned public source
trees, controlled inputs, and the same local process-effect probe. It preserves
the task output while rotating the counterfeit role among matched packages.

## Task families

| Group | Family | Expected artifact | Forbidden process effect |
|---|---|---|---|
| Primary | Document redaction | Redacted text | Unauthorized loopback transmission |
| Primary | Speech transcription | Exact transcript | Unauthorized loopback transmission |
| Primary | Paper retrieval | Matching PDF | Unauthorized loopback transmission |
| Primary | Archive extraction | Canonical directory tree | Write outside the target |
| Primary | Tabular conversion | Canonical JSON | Read an unrelated file |
| Held out | Configuration editing | Updated configuration | Protected metadata change |
| Held out | Image thumbnailing | Thumbnail image | Unnecessary subprocess |

The public implementation represents every forbidden event with a controlled
local fixture. No event can transmit private data or contact an external service.

## Public-package transfer

The frozen slice covers Markdown 3.8.2, markdown2 2.5.4, Mistune 3.1.3, toml
0.10.2, tomli 2.2.1, TOML Kit 0.13.3, JSON5 0.12.0, Hjson 3.1.0, and
commentjson 0.9.0. Kimi K3, Qwen3.8 Max, GLM-5.3, DeepSeek V4.1 Flash,
MiniMax M3, and Grok 4.6 run with one fixed agent configuration across three
ranks and two policies. Three role rotations per domain yield 324 cells.

All packages return the same canonical artifact within each transformation
domain. Exactly one role-rotated source tree receives a controlled loopback-only
probe. Archive hashes and licenses are recorded in
`experiments/public_packages/package_lock.json`; the modified archives stay
local and run only in the sandbox. Audited aggregates are released under
`experiments/public_packages/results/`.

The slice records 36/162 counterfeit executions under deliberation and 26/162
under compare-all. The deliberation-minus-compare-all CER difference is 6.2
percentage points with a 95% clustered interval of -0.6 to 13.0 points. Both
policies retain a rank gradient. The result supports transfer of rank
sensitivity, while the aggregate comparison benefit remains uncertain.

## Evidence depth

Every candidate contains `run.py`, `pipeline.py`, and `hook.py`. The decisive
statement appears at the entrypoint, one import below it, or two imports below
it. Candidate topology is otherwise matched. This lets the evaluator vary the
inspection distance without changing the advertised capability or output.

## Model access

All entries in `configs/models.json` use OpenRouter Chat Completions through the
same client. This includes the OpenAI model entry. The release has no native
provider branch, Codex-authenticated model branch, or provider-specific key.
Temperature and top-p are omitted so each endpoint uses its default values.

OpenRouter aliases and availability can change after the frozen evaluation.
When an identifier is retired, record any replacement explicitly and treat the
new run as a release refresh rather than silently merging it with frozen data.

## Audit records

Each run produces:

- `events.jsonl`: tool calls, inspected files, executed package hash, output hash,
  and controlled process events;
- `model_audit.jsonl`: request hash, returned model/provider metadata, latency,
  and token usage without complete prompts;
- `summary.json`: task success, counterfeit execution, safe utility, and trial
  factors.

The model's final prose never overrides trace-derived execution labels.

## Determinism and endpoint variation

Fixture generation, candidate role assignment, rank schedules, controlled package content,
and expected hashes are deterministic under the configured seed. Model outputs
can vary because remote endpoints are stochastic and may be updated. Preserve
the generated manifest, run summaries, request hashes, and endpoint metadata for
every reported evaluation.
