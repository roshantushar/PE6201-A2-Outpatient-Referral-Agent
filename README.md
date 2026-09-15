# PE6201 A2 — Problem B: Outpatient Referral Coordination Agent

A bounded, tool-using single-agent system for outpatient referral coordination.

Given one referral at a time, the agent gathers evidence from deterministic tools and returns exactly one of:

- `book`
- `request_information`
- `escalate`

The only irreversible action, `book_slot`, is protected by deterministic validation and an autonomy gate.

This repository contains the complete implementation and experimental evidence for PE6201 Assessment 2, including D0–D7, the scripted reference backend, live-model comparison, guardrail tests, cost-to-serve analysis, and two reproduced failures.

---

## 1. Problem overview

Outpatient referral coordination is not treated as a one-shot classification problem.

The correct next action depends on evidence discovered during execution. A referral may terminate early because of:

- a clinical red flag,
- missing mandatory tests,
- a specialty mismatch,
- an existing future appointment,
- no valid slot within the allowed window, or
- hostile / injected instructions in referral free text.

A valid referral instead continues through:

```text
Referral
   ↓
Read referral
   ↓
Check referral criteria
   ↓
Check patient history
   ↓
Compute scheduling window
   ↓
Find eligible clinic slots
   ↓
Verify + gate book_slot
   ↓
BOOK
```

Because the next tool depends on prior observations and the number of turns varies by case, the system is implemented as a bounded single-agent ReAct-style loop rather than a fixed workflow.

---

## 2. System architecture

```text
                    ┌─────────────────────┐
                    │     Referral ID     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Agent loop     │
                    │   src/agent.py      │
                    └──────────┬──────────┘
                               │
                    next move / tool call(s)
                               │
             ┌─────────────────┴─────────────────┐
             │                                   │
             ▼                                   ▼
   ┌───────────────────┐              ┌───────────────────┐
   │ Scripted backend  │              │   Live backend    │
   │ reference policy  │              │ OpenRouter model  │
   └───────────────────┘              └───────────────────┘
             │                                   │
             └─────────────────┬─────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │       Tools         │
                    │    src/tools.py     │
                    └──────────┬──────────┘
                               │
                               ▼
                    Ground-truth fixture data
                               │
                               ▼
                         Observation
                               │
                               └───────────────↺

Final outcome:
book / request_information / escalate
```

The model controls the next tool selection, while deterministic Python code handles operations that should not depend on language-model reasoning, such as:

- scheduling-window arithmetic,
- slot validation,
- duplicate-appointment checks,
- action de-duplication,
- run/token limits,
- and irreversible-action gating.

---

## 3. Repository structure

```text
PE6201-A2-Outpatient-Referral-Agent/
│
├── src/
│   ├── agent.py
│   ├── backends.py
│   ├── config.py
│   ├── decision_log.py
│   ├── guardrails.py
│   ├── harness.py
│   ├── judge.py
│   ├── prompt.py
│   ├── run_eval.py
│   └── tools.py
│
├── data/
│   ├── make_fixtures_B_final.py
│   ├── check_my_data_final.py
│   ├── expected_outcomes_B.json
│   └── generated/
│
├── experiments/
│   ├── d0/
│   ├── d2a_tools/
│   ├── d2b_descriptors/
│   ├── d2c_parallelism/
│   ├── d3_guardrails/
│   ├── d4_evaluation/
│   ├── d5_models/
│   ├── d6_cost/
│   └── d7_failures/
│
├── results/
│   ├── scripted/
│   ├── evaluation/
│   ├── descriptors/
│   ├── parallelism/
│   ├── guardrails/
│   ├── live/
│   ├── cost/
│   └── d7/
│
├── docs/
│   ├── D0_AGENT_JUSTIFICATION.md
│   ├── D1_AGENT_LOOP.md
│   ├── D2_TOOL_DESIGN.md
│   ├── D3_GUARDRAILS.md
│   ├── D4_EVALUATION.md
│   ├── D4_EVALUATION_METRICS.md
│   ├── D5_MODEL_BATTERY.md
│   ├── D6_COST_MODEL.md
│   ├── D7_FAILURES.md
│   └── REPORT_EVIDENCE.md
│
├── notebooks/
├── CONTRIBUTIONS.md
├── requirements.txt
└── README.md
```

---

# 4. Quick start — scripted reproduction

## Requirements

- Python 3.9+
- No API key
- No network connection
- No external packages required for the scripted path

Clone the repository:

```bash
git clone https://github.com/roshantushar/PE6201-A2-Outpatient-Referral-Agent.git
cd PE6201-A2-Outpatient-Referral-Agent
```

Generate and validate the extended Problem B fixtures:

```bash
python3 data/make_fixtures_B_final.py
python3 data/check_my_data_final.py
```

The checker should report that the data hangs together successfully.

Run the full scripted evaluation:

```bash
cd src
python3 run_eval.py
```

Expected headline result:

```text
95 / 95 trials passed
0 step-cap hits
```

The run writes:

```text
results/scripted/final_eval.json
```

The committed default backend is `scripted`, so a marker can reproduce the main system without an API key.

---

# 5. Run individual examples

From `src/`:

```bash
python3 run_eval.py REF-5602
```

Example successful booking case.

```bash
python3 run_eval.py REF-5614
```

Example `request_information` case.

```bash
python3 run_eval.py REF-5590
```

Example `escalate` case.

To inspect the live-model prompt:

```bash
python3 run_eval.py --prompt
```

To inspect the deliberately weaker v1 prompt:

```bash
python3 run_eval.py --prompt --v1
```

---

# 6. Configuration

Main configuration is in:

```text
src/config.py
```

Important settings include:

- backend: `scripted` or `live`
- model name
- autonomy mode
- maximum turns
- token budget / ceiling
- data paths

The submitted default is:

```text
scripted
```

The live backend requires an OpenRouter API key.

Example:

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

Live-result files already committed under `results/live/` are the evidence used in the report; rerunning live experiments is not required to reproduce the scripted submission path.

---

# 7. Assignment mapping: D0–D7

| Assignment item | Implementation | Main evidence |
|---|---|---|
| **D0 — Why an agent?** | `docs/D0_AGENT_JUSTIFICATION.md`, `experiments/d0/` | reliability calculation and trajectory analysis |
| **D1 — Build the agent** | `src/agent.py`, `src/backends.py`, `docs/D1_AGENT_LOOP.md` | hand-built ReAct loop and decision logs |
| **D2(a) — Tool set** | `src/tools.py`, `experiments/d2a_tools/` | retained/rejected-tool analysis and prompt-tax measurement |
| **D2(b) — Tool descriptor + return shape** | `experiments/d2b_descriptors/` | isolated `get_clinic_slots` v1/v2 live ablation |
| **D2(c) — Sequential vs parallel calls** | `experiments/d2c_parallelism/` | 6→5-turn comparison with unchanged correctness |
| **D3 — Guardrails** | `src/guardrails.py`, `experiments/d3_guardrails/` | 19/19 guardrail tests |
| **D4 — Evaluation set** | `src/harness.py`, `src/judge.py`, `data/expected_outcomes_B.json` | 55 cases / 95 trials |
| **D5(a) — Scripted reproducibility** | `src/backends.py`, `src/run_eval.py` | 95/95 scripted trials |
| **D5(b) — Live model battery** | `experiments/d5_models/`, `results/live/` | five comparable live models |
| **D6 — Cost-to-serve** | `experiments/d6_cost/`, `docs/D6_COST_MODEL.md` | 3-layer model, 4 levers, sensitivity, break-even |
| **D7 — Reproduced failures** | `experiments/d7_failures/`, `docs/D7_FAILURES.md` | working → broken → restored for two layers |

---

# 8. Headline evaluation results

## Scripted reference backend

The scripted backend is a deterministic reference policy over the real tools.

It is **not** a language model.

Its purpose is to verify that the data, tools, guardrails and evaluation harness are wired correctly.

Final scripted result:

| Metric | Result |
|---|---:|
| Evaluation cases | 55 |
| Total trials | 95 |
| Code-check pass rate | **95 / 95 — 100%** |
| Negative trials | 60 |
| Negative pass rate | **100%** |
| Mean turns | 3.232 |
| Median turns | 2 |
| Worst legitimate run | 5 |
| Incorrect bookings | 0 |
| Unnecessary slot queries | 0 |

The evaluation set contains:

- 35 `book` cases
- 15 `escalate` cases
- 5 `request_information` cases

Negative cases are repeated three times.

This is intentionally a stress-weighted evaluation set rather than an estimate of real outpatient-referral prevalence.

---

# 9. Code checks vs judgement checks

Two different evaluation layers are kept separate.

## Code check

Deterministically checks fields such as:

- decision,
- trigger,
- missing item,
- clinic,
- date,
- time,
- unsafe booking,
- required evidence.

Scripted result:

```text
95 / 95
```

## Judgement check

A separate model evaluates whether the natural-language `reason` records the specific evidence expected by `must_record`.

Current judgement result:

```text
41 / 55 = 74.6%
```

This reveals an important distinction:

> A model may produce the correct structured action while still giving an incomplete explanation of why that action is justified.

---

# 10. D2(a) — Tool-set design

The final tool set is deliberately bounded.

Tools are retained only when:

1. a real task fails without them,
2. they are not easily confused with another tool, and
3. their prompt-prefix cost is justified even when unused.

The design also moves deterministic tasks out of the LLM where possible.

Examples include:

- date-window calculation,
- duplicate verification,
- slot validation,
- irreversible-action gating.

Two unnecessary candidate tools were tested and rejected.

Measured prompt tax:

```text
+178 prompt tokens per turn
```

This demonstrates that unused tools are not free.

---

# 11. D2(b) — Descriptor and return-shape ablation

The required isolated experiment changes only:

```text
get_clinic_slots
```

while keeping the model and the rest of the system fixed.

Model:

```text
openai/gpt-4o-mini
```

### v1

- weaker descriptor
- verbose return shape

### v2

- full descriptor
- compact return shape

Results:

| Metric | v1 | v2 |
|---|---:|---:|
| Relevant live trials | 41 | 41 |
| Pass rate | **100%** | **100%** |
| Negative trials | 6 | 6 |
| Negative pass rate | **100%** | **100%** |
| Mean returned tokens / `get_clinic_slots` call | **39.05** | **19.17** |
| Mean input tokens | 8,798 | 9,107 |
| Mean turns | 4.12 | 4.00 |
| Total live cost | $0.0608 | $0.0625 |

This is intentionally reported as a **null correctness result**.

The useful result is that the compact v2 return shape approximately halves the tool observation size while preserving correctness.

---

# 12. Whole-prompt v1 vs v2

The repository also contains a broader whole-prompt comparison on GPT-4o-mini.

```text
v1: 39 / 95 = 41.1%
v2: 95 / 95 = 100%
```

This experiment is separate from the isolated D2(b) single-tool ablation.

The large improvement was driven by fixes discovered during live testing, including:

- clearer canonical output vocabulary,
- improved action/output contracts,
- duplicate-check enforcement,
- tool-call shape normalisation,
- and booking verification.

See:

```text
results/descriptors/
docs/D2_TOOL_DESIGN.md
```

---

# 13. D2(c) — Sequential vs parallel tool calls

Parallelisation follows one rule:

> Two calls may share a turn only when neither call requires the other call's output and both are already known to be necessary.

Representative case:

```text
REF-5602
```

| Metric | Sequential | Parallel |
|---|---:|---:|
| Turns | 6 | **5** |
| Tool calls | 6 | 6 |
| Estimated total tokens | 38,220 | **29,460** |
| Estimated cost | $0.006079 | **$0.004716** |
| Correctness | correct | correct |
| Wasted calls | 0 | 0 |

The token/cost values above come from the scripted backend estimator and are therefore explicitly labelled as **estimates**, not live-provider token usage.

---

# 14. D3 — Guardrails

Guardrails are implemented in deterministic code rather than relying only on prompt instructions.

The system includes controls for:

- step cap,
- token / budget ceiling,
- duplicate-action detection,
- autonomy gate,
- one-booking-per-run,
- malformed tool arguments,
- malformed agent output,
- usage/monthly limits,
- duplicate-appointment protection,
- hostile referral free text.

Final guardrail result:

```text
19 / 19 passed
```

The suite includes:

- ordinary non-trigger controls,
- limit-exceeded tests,
- four hostile-text / injection patterns,
- one benign-text false-positive control,
- autonomy refusal,
- suggest-only mode,
- duplicate-booking attempt,
- malformed action/tool shapes.

See:

```text
results/guardrails/guardrail_results.json
```

---

# 15. D5(b) — Live model battery

The same v2 system was evaluated with multiple live model families on the identical 55-case / 95-trial battery.

## Comparable headline battery

| Model | Overall pass | Negative pass | Median turns | Total API cost |
|---|---:|---:|---:|---:|
| `openai/gpt-4o-mini` | **100.0%** | **100.0%** | 4 | $0.1154 |
| `google/gemini-2.5-flash-lite` | **95.8%** | **100.0%** | 2 | $0.1421 |
| `qwen/qwen-2.5-72b-instruct` | **83.2%** | **91.7%** | 3 | $0.1247 |
| `meta-llama/llama-3.1-8b-instruct` | **52.6%** | **33.3%** | 3 | $0.1381 |
| `mistralai/mistral-nemo` | **21.1%** | **25.0%** | 2 | $0.0814 |

Five live models form the final comparable headline table.

A sixth live attempt using Claude 3 Haiku is also retained as raw evidence. It failed the required turn-by-turn interaction protocol, so it is documented as a protocol-compliance failure rather than mixed into the comparable five-model table.

This raw failure was preserved rather than silently deleted.

See:

```text
results/live/
docs/D5_MODEL_BATTERY.md
```

---

# 16. D6 — Cost-to-serve

Problem B uses:

```text
4,000 referrals / month
```

and the default human failure cost:

```text
$55/hour × 10 minutes
= approximately $9.17 / failed referral
```

The cost model has three layers:

```text
Layer 1 — model/API variable cost
Layer 2 — expected human fallback cost
Layer 3 — fixed monthly operating allowance
```

Formula:

```text
monthly cost
=
volume × (variable cost + expected fallback)
+ fixed monthly cost
```

The experiment measures all four required cost levers:

1. tool-block size,
2. number of turns,
3. observation size,
4. model success rate.

The dominant lever is success rate because the human fallback penalty is much larger than the small difference in token prices between models.

## Switch break-even

Using GPT-4o-mini as the high-success reference and Mistral NeMo as the lower-token-cost candidate:

```text
GPT-4o-mini successful-task cost E = $0.002100
Mistral token-only cost C = $0.001480
Failure cost F = $9.1667
```

Required success rate for the cheaper model:

```text
1 - (E - C) / F
= 99.9932%
```

Measured Mistral success:

```text
21.05%
```

Therefore the cheaper-token model does **not** clear the economic break-even.

See:

```text
results/cost/
docs/D6_COST_MODEL.md
```

---

# 17. D7 — Reproduced failures

Both failure experiments use the same pattern:

```text
working
   ↓ remove one safeguard
broken
   ↓ restore safeguard
restored
```

## Failure 1 — loop-control layer

Remove action de-duplication.

Representative result:

```text
Working:  5 turns
Broken:   7 turns
Restored: 5 turns
```

The final booking remains correct, but the broken version performs unnecessary work and consumes substantially more estimated tokens.

This demonstrates why pass/fail accuracy alone is not sufficient observability.

## Failure 2 — tool-interface layer

Remove urgency-band filtering from slot lookup.

A routine referral can then incorrectly receive an urgent-reserved slot.

Restoring the interface restriction returns the original safe result.

The correct repair belongs in the tool interface rather than in another prompt instruction.

See:

```text
results/d7/
docs/D7_FAILURES.md
```

---

# 18. Result locations

| Deliverable | Command | Result |
|---|---|---|
| D0 reliability | `python3 experiments/d0/reliability_calc.py` | `experiments/d0/reliability_calc.json` |
| D2(a) tool-set analysis | tool-set experiment | `results/descriptors/tool_set_comparison.json` |
| D2(b) isolated interface | live ablation | `results/descriptors/single_tool_ablation_get_clinic_slots.json` |
| D2(c) parallelism | `python3 experiments/d2c_parallelism/run_comparison.py` | `results/parallelism/` |
| D3 guardrails | `python3 experiments/d3_guardrails/run_guardrail_cases.py` | `results/guardrails/guardrail_results.json` |
| D4/D5(a) scripted eval | `python3 src/run_eval.py` | `results/scripted/final_eval.json` |
| D5(b) live battery | live-model experiment | `results/live/` |
| D6 cost model | `python3 experiments/d6_cost/run_cost_model.py` | `results/cost/` |
| D7 failure 1 | `python3 experiments/d7_failures/failure_1_loop.py` | `results/d7/failure_1_loop.json` |
| D7 failure 2 | `python3 experiments/d7_failures/failure_2_slot_interface.py` | `results/d7/failure_2_slot_interface.json` |

For a claim-by-claim mapping between documentation and saved evidence, see:

```text
docs/REPORT_EVIDENCE.md
```

---

# 19. Limitations

This is an academic prototype and should not be interpreted as a production clinical scheduling system.

Important limitations include:

### Fixture data

All patient/referral/slot data are local fixtures rather than live clinical systems.

### Stress-weighted evaluation

The final set contains 55 cases and 20 negative cases, deliberately exceeding the suggested evaluation shape.

Therefore the measured pass rates should not be interpreted as real-world prevalence-weighted production accuracy.

### Confirmation during batch evaluation

The declared autonomy setting is `confirm`.

However, unattended batch experiments use a default approval callback so evaluation can run reproducibly without a human sitting at the terminal.

The gate mechanism itself is separately tested, including explicit refusal and suggest-only behaviour.

### Injection defence

Hostile-text detection is deliberately simple and primarily based on deterministic pattern/substring logic.

It performs correctly on the committed guardrail battery, but it is not claimed to be a complete defence against adaptive adversarial prompt injection.

### Explanation quality

Code-check correctness is stronger than natural-language explanation quality.

The independent judgement check shows that correct structured decisions do not guarantee that the model records every required supporting fact in its `reason`.

### Live-model results

Results are specific to:

- this evaluation set,
- these prompts/tools,
- these model versions/providers,
- and the measured run conditions.

They are not universal model rankings.

---

# 20. Contributions

Individual ownership, model assignments and file-level contributions are documented in:

```text
CONTRIBUTIONS.md
```

The Git history should be read together with that file.

---

# 21. Submission artefacts outside this repository

The following PE6201 submission artefacts are produced/submitted separately rather than treated as source-code files in this repository:

- final report,
- five-minute recorded demo,
- team self-appraisal,
- team declaration / other NTULearn administrative documents where required.

---

# 22. Reproducibility and provenance

All headline numerical claims in this README should be traceable to committed files under:

```text
results/
```

The project distinguishes clearly between:

- **scripted token/cost estimates**, and
- **real live-provider usage**.

Scripted evaluation exists to demonstrate reproducible system behaviour.

Live-model results exist to measure real model behaviour.

Neither is presented as a substitute for the other.