# SelfHarness

> A coding-agent harness that studies its own failures, writes its own rules, and keeps a rule only if it is proven to help on held-out tasks.

**Headline result: pending experiments.** This repository has not yet produced benchmark measurements. No performance-improvement claim is made.

## Architecture

```text
Train tasks → Agent loop + tools → Traces → Failure classifier → Diagnoser
                                                          │
                                                          ▼
Rules file ◀── accept ── Validation gate ── reject → rejection log
                              │
                              └── paired held-out runs → results and dashboard
```

## Results

| Experiment | Status | Result |
|---|---|---|
| Baseline | Not run | — |
| Verifier / context / rules / sandbox ablations | Not run | — |
| Self-improvement rounds 0–5, 3 seeds | Not run | — |
| Auto vs human vs no rules | Not run | — |
| Gate on vs off | Not run | — |
| Transfer and safety tests | Not run | — |

The current three tiny fixtures are wiring examples only, not the specified benchmark. No synthetic demo score is evidence.

## Quick start

Install with `pip install -e ".[dev]"`, then use `selfharness demo` to inspect synthetic report formatting. Model-backed execution requires a configured API key and Docker. The CLI and runner are still an early scaffold; end-to-end execution has not yet been verified.

## Current contents

- Python package scaffold with a basic bounded JSON-action loop and file/test tools.
- Docker test-runner path, event JSONL helpers, attempt records, patch audit, and paired gate calculations.
- Training-failure rule proposal and freeze-before-final-test marker.
- Three small fixtures (one task per split), configuration, a basic dashboard, and design documents.

## Remaining work

1. Create the full 40-task benchmark (25 train, 15 validation) at the specified difficulty mix; optionally add a separate final set.
2. Complete the promised modules: MCP server, shell/search tools with permissions, context compaction, progress memory, verifier/linter, SQLite results, real classifier, module toggles, budget cap, parallel evaluation, automatic infra retries, and accurate gate checks for previously passing tasks.
3. Make the CLI and imports work end to end; install dependencies and run unit/integration tests, Docker smoke tests, and dashboard checks.
4. Implement experiment orchestration and export the required CSVs, rule history, failure taxonomy, trace replay, and charts.
5. Run all eight required experiments and only then write result claims, resume bullets, blog/LinkedIn copy, and demo.

See [PROJECT_SPEC.md](PROJECT_SPEC.md) for the complete specification, [docs/technical-design.md](docs/technical-design.md) for the current design, and [docs/reproducibility-checklist.md](docs/reproducibility-checklist.md) for experiment hygiene.

## Limitations

The starter dataset is much smaller than the target and cannot establish a reliable improvement. Small benchmarks are noisy; rules may not transfer to other domains or models; LLM-based failure labels require human spot-checking. Any future report should include task counts, spread, model configuration, exclusions, cost, and audit findings.
