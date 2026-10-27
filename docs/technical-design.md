# SelfHarness technical design

## Goal

Measure whether behavioral rules inferred from coding-agent failures on training tasks improve success on held-out tasks. Every result should be reconstructible from a task manifest, run config, traces, rule versions, and gate policy. The tiny included tasks validate wiring only; they are not a meaningful benchmark.

## Architecture and flow

1. A JSONL manifest defines each task, split, fixture path, instruction, test argv, timeout, write globs, and test paths. `splits.json` independently lists split membership. Fixture bytes and task metadata are hashed.
2. Each task-seed attempt copies a clean fixture to a temporary directory. The agent gets bounded JSON actions and four scoped tools: list/read/write files and run the configured tests.
3. The model cannot submit arbitrary shell. Test commands run in a disposable Docker container with network disabled, read-only workspace mount, and CPU, memory, PID, and time limits. Local mode is for development only.
4. The runner records model responses, tool calls, test output, token use, estimated cost, changed paths, patch hash, and final status to JSONL.
5. A diagnoser sees training failures only and proposes a structured rule. It cannot edit evaluator code, tests, or task data.
6. The gate compares accepted rules with accepted-plus-candidate on the same validation task/seed pairs. It records paired task outcomes, bootstrap interval, exact McNemar result, seed deltas, cost, and audit flags.
7. A rule is accepted only if minimum pair count, confidence-bound gain, per-seed regression limit, and audit policy pass. Otherwise it is rejected or inconclusive.
8. Freeze records accepted-rule and dataset hashes. Final evaluation requires the hashes to match and explicit CLI acknowledgment to show sealed results.
9. Streamlit dashboard reads the stored reports and traces; it cannot alter gate decisions.

## Statistical interpretation

Primary metric is the fraction of valid attempts whose full test command exits successfully. Always show numerator and denominator. Infrastructure errors are reported and excluded from paired scoring; this starter has no automatic retries. The paired bootstrap resamples binary task-seed deltas. McNemar's exact p-value is descriptive. Neither makes tiny samples conclusive. A repeated validation set becomes development data through selection pressure; only the sealed test supports a final post-freeze comparison.

For 40 tasks, a plausible first split is 25 training, 10 validation, 5 sealed test. Three repetitions yield 30 validation pairs, but five final tasks are too few for broad claims. Expand the benchmark before making a resume claim about a measured gain.

## Patch auditing and limits

Changed files outside allowlisted source paths, test-file modifications, and selected suspicious patterns are flagged. These checks aid review and can reject obvious test tampering; they do not prove a patch is correct or non-cheating. Add independent hidden tests and human diff review. Pin Docker images by digest for published work. Model nondeterminism and provider changes also affect reproducibility. API cost is an estimate from manually configured prices, not a bill.

## Records

`Task`: ID, split, fixture, instruction, test command, timeout, editable globs, test paths, tags, difficulty.

`AttemptResult`: run and attempt IDs, task, condition, seed, status, pass flag, exit code, steps, time, tokens, estimated cost, patch hash, changed paths, flags, output excerpt, and error.

`RuleProposal`: rule ID/text/rationale and source training run/task IDs.

Gate report: decision/reason, valid pair count, paired interval and outcomes, seed deltas, audit flags, cost/tokens, policy, data hash, baseline/candidate run IDs, and accepted-rule version.
