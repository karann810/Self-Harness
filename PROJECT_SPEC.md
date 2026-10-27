# SelfHarness: Final Project Specification

> A coding-agent harness that studies its own failures, writes its own rules, and keeps a rule only if it is proven to help on held-out tasks.

**Thesis:** The model stays fixed. Only the harness improves, and every improvement is measured.

## Current implementation status

This repository is an early scaffold, not a completed benchmark or a source of performance claims. Current code covers a bounded JSON tool loop, Docker-backed test execution, event logs, a basic paired gate, rule proposal, and a freeze marker. Missing or incomplete items are listed in [README.md](README.md) and tracked as build milestones below. Never fill results with estimates or synthetic demo numbers.

## 1. Problem and goal

Agent failures are commonly fixed by hand-editing prompts. This is slow, unmeasured, and can overfit to observed examples. SelfHarness automates failure analysis and candidate-rule generation, then uses held-out validation to reject rules that do not generalize.

Success means a measurable held-out gain with a fixed model, evidence for which rules/modules helped, failure-category rates before and after changes, and rejection of poisoned rules.

## 2. Core loop

```text
Training tasks → Agent attempts → Full traces → Failure classifier
       → Diagnoser proposes one rule per top category
       → Validation gate (3 repeats, paired tasks)
       → accept to rules/rules.md OR log rejection and reason
       → repeat for N rounds; chart validation scores
```

Rules are small readable instructions. Each accepted rule records its origin failure category, round, source evidence, and measured impact. The gate accepts only when success improves and no previously passing task regresses. The exact statistical policy must be predeclared and documented.

## 3. Architecture requirements

| Module | Responsibility |
|---|---|
| `agent_loop` | Think/act/observe; step, token, cost, time limits; loop/stall detection; malformed-call retry. |
| `tools` | Typed `read_file`, `write_file`, `list_dir`, `search_code`, `run_tests`, `run_shell`; safe model-facing errors. |
| `mcp_server` | Expose at least one tool through the MCP Python SDK. |
| `context_manager` | Token budget, truncation, compaction, rules injection. |
| `memory` | Per-run `progress.md`; persistent `rules/rules.md`. |
| `sandbox` | Docker per task; no network; resource/time limits; read-only mounts where possible. |
| `permissions` | Command allow/deny policy, path restrictions, approval gate for risky actions. |
| `verifier` | Tests and linter after edits; feed failures back; block completion until checks pass. |
| `tracer` | JSONL prompts, replies, tool calls/results, tokens, cost, and latency. |
| `eval_runner` | Parallel attempts, repeats, splits, result tables. |
| `classifier` | Failure category assignment, LLM-assisted and spot-checked by a person. |
| `diagnoser` | One rule per leading failure cluster. |
| `gate` | Accept/reject rule using validation improvement and regression protection. |
| `model_adapter` | Common provider interface; transfer test support. |
| `dashboard` | Streamlit results, trace replay, and rule history. |

All modules must be individually toggleable in configuration for ablations.

## 4. Benchmark design

- 40 small Python bug-fix repositories, each with failing pytest coverage before repair.
- Difficulty: 15 easy, 15 medium, 10 hard.
- Split: 25 training and 15 validation; the diagnoser must never receive validation content or results.
- Optional final test: 10 new tasks or 20–30 suitable SWE-bench Lite tasks, evaluated once at the end.
- Three repeats per task and configuration.
- Metrics: pass rate, average steps, estimated cost, wall time, and per-category failures.

## 5. Required experiments

1. Baseline: bare loop, no verifier, compaction, or rules.
2. Module ablations: add verifier, compaction, rules file, and sandbox one at a time.
3. Improvement curve: validation rounds 0–5, mean and spread across three seeds.
4. Auto-written rules versus human-written rules versus no rules.
5. Gate on versus gate off, demonstrating validation overfit risk.
6. Transfer rules learned on model A to model B.
7. Safety: poisoned rule; repository prompt injection; blocked destructive command.
8. Cost/reliability: pass rate versus tokens/cost.

## 6. Failure taxonomy

Start with premature completion, wrong file/function, looping, tool misuse, context loss, bad plan, regressions in other tests, and giving up too early. Refine from actual traces. For each category report count, example trace, fix/rule, and before/after rate. LLM labels must be spot-checked manually.

## 7. Stack and budget

Python 3.11+, hand-written core loop, cheap agent model, stronger classifier/diagnoser, second agent model for transfer, Docker, MCP Python SDK, pytest, JSONL, SQLite, pandas, matplotlib, and Streamlit. Set a hard API spending cap in config and stop before exceeding it. Target budget: USD 20–50.

## 8. Target repository structure

```text
selfharness/
  README.md
  PROJECT_SPEC.md
  pyproject.toml
  src/selfharness/
    agent_loop.py
    tools/
    mcp_server/
    context_manager.py
    memory.py
    sandbox.py
    permissions.py
    verifier.py
    tracer.py
    model_adapter.py
    eval_runner.py
    classifier.py
    diagnoser.py
    gate.py
    config.py
  benchmark/{train,validation,final_test}/
  rules/{rules.md,rejected.jsonl}
  runs/                         # ignored except sample artifacts
  results/{ablations.csv,selfimprove_curve.csv,failure_taxonomy.csv}
  dashboard/app.py
  docs/{architecture.png,failure_analysis.md,blog_post.md}
  tests/
```

The current tree may differ while code is being built, but the responsibilities and deliverables above remain the target.

## 9. Deliverables

- Working harness with toggleable modules.
- 40-task train/validation benchmark.
- Baseline and ablation table.
- Self-improvement loop and validation gate.
- Five-round, three-seed curve.
- `rules/rules.md` with measured impact per accepted rule.
- Failure taxonomy and fixes.
- Safety tests, transfer experiment, and trace-replay dashboard.
- README with diagram, results, and reproduction steps.
- Demo video, blog/LinkedIn copy, and resume bullets using only measured numbers.

## 10. README order

1. One-line pitch.
2. Headline result (leave explicitly pending until measured).
3. Architecture diagram.
4. Results table.
5. Improvement chart.
6. Quick start: install, one task, evaluation, one improvement round.
7. Honest limitations.

## 11. Limitations to report

The 40-task benchmark is small; few-point differences may be noise. Python bug-fix rules may not transfer domains. Results depend on the model; transfer only partly addresses that. LLM failure labels can be wrong and require manual spot-checking.

## 12. Resume bullet templates

Use only after experiments complete; replace placeholders with measured results:

- Built SelfHarness, a coding-agent harness with MCP tools, Docker sandbox, context compaction, test verification, tracing, and a validation-gated rule-learning loop.
- Raised held-out pass rate from **X% to Y%** across five rounds with the model unchanged; ablations identified **[module]** as the largest measured contributor.
- Classified **N** failures into eight categories and validated rules that reduced **[category]** failures by **Z%**.
- Tested poisoned rules and repository prompt injection; report measured rejection/block rates and test scope.

## 13. Interview prompts

Explain why validation gating prevents unchecked overfitting; identify the largest ablation gain; describe model-versus-harness effects using transfer results; discuss self-modifying rule risks (poisoning, drift, bloat) and mitigations (gate, size limits, regression tests).

## 14. Build order

1. Basic loop, tools, tests, tracing.
2. Sandbox and permissions.
3. Benchmark/eval runner and baseline.
4. Verifier, context manager, ablations.
5. Failure logger/classifier/diagnoser.
6. Validation gate and full loop.
7. Transfer, safety, human-versus-auto rules.
8. Dashboard and packaging.

Stretch goals: rule pruning, conflict detection, category-based rule retrieval, and publishing task data/traces.
