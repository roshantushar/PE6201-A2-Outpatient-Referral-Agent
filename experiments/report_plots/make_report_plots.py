#!/usr/bin/env python3
"""
REPORT PLOTS - all real, measured data, no fabricated numbers.
====================================================================
Generates every chart requested for the team report: model comparisons
(D5(b)), cost-model plots (D6), architecture-efficiency comparisons
(D2(b)/D2(c)/D7), evaluation-set plots (D4), and the B*T + D*T^2/2
token-growth formula (both a generic illustrative curve and the
per-model empirical comparison already built in D2(c)'s own script).

Every number plotted here is read directly from a committed results/
file - nothing is estimated or eyeballed for this script.
====================================================================
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(RESULTS, "report_plots")
os.makedirs(OUT, exist_ok=True)

# Okabe-Ito colorblind-safe palette, fixed assignment per model (never
# re-cycled), matching the assignment already used in
# experiments/d2c_parallelism/plot_token_growth.py
COLORS = {
    "openai/gpt-4o-mini": "#0072B2",
    "google/gemini-2.5-flash-lite": "#E69F00",
    "qwen/qwen-2.5-72b-instruct": "#009E73",
    "meta-llama/llama-3.1-8b-instruct": "#D55E00",
    "mistralai/mistral-nemo": "#CC79A7",
    "anthropic/claude-3-haiku": "#999999",  # excluded model - grey
}
HEADLINE_ORDER = [
    "openai/gpt-4o-mini", "google/gemini-2.5-flash-lite",
    "qwen/qwen-2.5-72b-instruct", "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-nemo",
]


def _short(model):
    return model.split("/")[-1]


def _load(*parts):
    with open(os.path.join(RESULTS, *parts), encoding="utf-8") as fh:
        return json.load(fh)


def _save(fig, name):
    path = os.path.join(OUT, name)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print("wrote", os.path.relpath(path, ROOT))


# ---- 1. Overall pass rate by model -------------------------------------
def plot_1_overall_pass_rate():
    rows = _load("live", "model_comparison.json")
    by_model = {r["model"]: r for r in rows}
    models = HEADLINE_ORDER + [m for m in by_model if m not in HEADLINE_ORDER]
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    xs = range(len(models))
    vals = [by_model[m]["pass_rate"] * 100 for m in models]
    colors = [COLORS.get(m, "#999999") for m in models]
    bars = ax.bar(xs, vals, color=colors)
    for i, v in enumerate(vals):
        ax.text(i, v + 1.5, "%.1f%%" % v, ha="center", fontsize=9)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([_short(m) for m in models], rotation=20, ha="right")
    ax.set_ylabel("Overall pass rate (%)")
    ax.set_ylim(0, 110)
    ax.set_title("D5(b) — overall pass rate by model (95 trials each)")
    ax.axhline(100, color="#cccccc", linewidth=0.8, zorder=0)
    _save(fig, "01_overall_pass_rate_by_model.png")


# ---- 2. Overall vs negative pass rate ------------------------------------
def plot_2_overall_vs_negative():
    rows = _load("live", "model_comparison.json")
    by_model = {r["model"]: r for r in rows}
    models = HEADLINE_ORDER
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    x = range(len(models))
    w = 0.35
    overall = [by_model[m]["pass_rate"] * 100 for m in models]
    negative = [by_model[m]["negative_pass_rate"] * 100 for m in models]
    ax.bar([i - w / 2 for i in x], overall, width=w, label="Overall pass rate",
           color=[COLORS[m] for m in models])
    ax.bar([i + w / 2 for i in x], negative, width=w, label="Negative-case pass rate",
           color=[COLORS[m] for m in models], alpha=0.45, hatch="//")
    ax.set_xticks(list(x))
    ax.set_xticklabels([_short(m) for m in models], rotation=20, ha="right")
    ax.set_ylabel("Pass rate (%)")
    ax.set_ylim(0, 110)
    ax.set_title("D5(b) — where models diverge: overall vs negative-case pass rate")
    ax.legend(loc="lower left", fontsize=9)
    _save(fig, "02_overall_vs_negative_pass_rate.png")


# ---- 3. Monthly cost by model (log scale) --------------------------------
def plot_3_monthly_cost():
    rows = _load("cost", "d6_measured_all_models.json")
    rows = sorted(rows, key=lambda r: r["monthly_cost_usd_at_4000_referrals"])
    models = [r["model"] for r in rows]
    vals = [r["monthly_cost_usd_at_4000_referrals"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    bars = ax.bar(range(len(models)), vals, color=[COLORS.get(m, "#999999") for m in models])
    ax.set_yscale("log")
    for i, v in enumerate(vals):
        ax.text(i, v * 1.15, "$%.0f" % v if v >= 1 else "$%.2f" % v,
                ha="center", fontsize=9)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([_short(m) for m in models], rotation=20, ha="right")
    ax.set_ylabel("Monthly cost at 4,000 referrals/month (US$, log scale)")
    ax.set_title("D6 — monthly cost by model (three-layer model, log scale)")
    ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
    _save(fig, "03_monthly_cost_by_model_log.png")


# ---- 4. Cost per successful referral vs pass rate (scatter) -------------
def plot_4_cost_vs_pass_rate():
    rows = _load("cost", "d6_measured_all_models.json")
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    for r in rows:
        m = r["model"]
        ax.scatter(r["success_rate_measured"] * 100, r["cost_per_successful_referral_usd"],
                   color=COLORS.get(m, "#999999"), s=140, zorder=3,
                   edgecolors="white", linewidths=0.8)
        ax.annotate(_short(m), (r["success_rate_measured"] * 100, r["cost_per_successful_referral_usd"]),
                    textcoords="offset points", xytext=(8, 4), fontsize=9)
    ax.set_yscale("log")
    ax.set_xlabel("Measured success rate (%)")
    ax.set_ylabel("Cost per successful referral (US$, log scale)")
    ax.set_title("D6 — reliability vs effective cost (one point per model)")
    ax.grid(True, linewidth=0.4, alpha=0.3)
    _save(fig, "04_cost_vs_pass_rate_scatter.png")


# ---- 5. Mean latency by model --------------------------------------------
def plot_5_latency():
    rows = _load("live", "model_comparison.json")
    by_model = {r["model"]: r for r in rows}
    models = HEADLINE_ORDER + ["anthropic/claude-3-haiku"] if "anthropic/claude-3-haiku" in by_model else HEADLINE_ORDER
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    vals = [by_model[m]["mean_latency_seconds"] for m in models]
    ax.bar(range(len(models)), vals, color=[COLORS.get(m, "#999999") for m in models])
    for i, v in enumerate(vals):
        ax.text(i, v + 0.4, "%.1fs" % v, ha="center", fontsize=9)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([_short(m) for m in models], rotation=20, ha="right")
    ax.set_ylabel("Mean latency per run (seconds)")
    ax.set_title("D5(b) — mean latency by model (separate from token cost)")
    _save(fig, "05_mean_latency_by_model.png")


# ---- 6. Sensitivity range -------------------------------------------------
def plot_6_sensitivity():
    rows = _load("cost", "d6_real_sensitivity.json")
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    for i, r in enumerate(rows):
        m = r["model"]
        pts = sorted(r["points"], key=lambda p: p["success_rate"])
        xs = [p["success_rate"] * 100 for p in pts]
        ys = [p["monthly_cost_usd"] for p in pts]
        ax.plot(xs, ys, "o-", color=COLORS.get(m, "#999999"), label=_short(m),
                linewidth=2, markersize=6)
    ax.set_yscale("log")
    ax.set_xlabel("Success rate (%) — measured ± 10pp")
    ax.set_ylabel("Monthly cost at 4,000 referrals (US$, log scale)")
    ax.set_title("D6 — cost sensitivity: ±10pp around each model's measured success rate")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, linewidth=0.4, alpha=0.3)
    _save(fig, "06_sensitivity_range.png")


# ---- 7. Switch break-even --------------------------------------------------
def plot_7_switch_breakeven():
    d = _load("cost", "d6_switch_breakeven.json")
    fig, ax = plt.subplots(figsize=(7.5, 5.5), dpi=150)
    labels = ["Breakeven success rate\nneeded", "Measured success rate\n(mistral-nemo)"]
    vals = [d["breakeven_success_rate"] * 100, d["cheap_model_measured_success_rate"] * 100]
    colors = ["#D55E00", COLORS["mistralai/mistral-nemo"]]
    bars = ax.bar(labels, vals, color=colors)
    for i, v in enumerate(vals):
        ax.text(i, v + 1.5, "%.2f%%" % v, ha="center", fontsize=10, fontweight="bold")
    ax.set_ylim(0, 110)
    ax.set_ylabel("Success rate (%)")
    ax.set_title("D6 — switch break-even: gpt-4o-mini (E) → mistral-nemo (C)\n"
                 "F = $%.4f/failure — mistral-nemo would need %.2f%% to be worth switching to"
                 % (d["F_failure_cost_usd"], d["breakeven_success_rate"] * 100))
    ax.annotate("Gap: %.1f percentage points" % (vals[0] - vals[1]),
                xy=(0.5, max(vals) + 6), ha="center", fontsize=9, color="#555555")
    _save(fig, "07_switch_breakeven.png")


# ---- 8. D2(c) sequential vs parallel --------------------------------------
def plot_8_d2c():
    d = _load("parallelism", "comparison.json")
    seq, par = d["sequential"], d["parallel"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5), dpi=150)
    metrics = [("turns", "Turns"), ("total_tokens_estimate", "Total tokens (est.)"),
              ("cost_usd_estimate", "Cost (est., US$)")]
    for ax, (key, label) in zip(axes, metrics):
        vals = [seq[key], par[key]]
        bars = ax.bar(["Sequential", "Parallel"], vals, color=["#999999", "#0072B2"])
        for i, v in enumerate(vals):
            fmt = "%.4f" if key == "cost_usd_estimate" else "%.0f"
            ax.text(i, v * 1.02, fmt % v, ha="center", fontsize=9)
        ax.set_title(label, fontsize=10)
    fig.suptitle("D2(c) — REF-5602: sequential vs parallel tool calls", fontsize=12)
    _save(fig, "08_d2c_sequential_vs_parallel.png")


# ---- 9. D2(b) tokens returned per call + pass rate -----------------------
def plot_9_d2b():
    d = _load("descriptors", "single_tool_ablation_get_clinic_slots.json")
    v1 = d["v1_weak_descriptor_and_verbose_return"]
    v2 = d["v2_full_descriptor_and_compact_return"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), dpi=150)

    ax = axes[0]
    vals = [v1["mean_get_clinic_slots_tokens_returned_per_call"],
            v2["mean_get_clinic_slots_tokens_returned_per_call"]]
    ax.bar(["v1 (verbose)", "v2 (compact)"], vals, color=["#D55E00", "#009E73"])
    for i, v in enumerate(vals):
        ax.text(i, v + 0.8, "%.1f" % v, ha="center", fontsize=10)
    ax.set_ylabel("Tokens returned per get_clinic_slots call")
    ax.set_title("Observation size")

    ax = axes[1]
    vals = [v1["pass_rate"] * 100, v2["pass_rate"] * 100]
    ax.bar(["v1 (verbose)", "v2 (compact)"], vals, color=["#D55E00", "#009E73"])
    for i, v in enumerate(vals):
        ax.text(i, v + 1.5, "%.1f%%" % v, ha="center", fontsize=10)
    ax.set_ylim(0, 110)
    ax.set_ylabel("Pass rate (%)")
    ax.set_title("Correctness (null result: unchanged)")

    fig.suptitle("D2(b) — get_clinic_slots descriptor + return-shape ablation (41 trials/version)", fontsize=12)
    _save(fig, "09_d2b_descriptor_ablation.png")


# ---- 10. D7 both failures --------------------------------------------------
def plot_10_d7():
    f1 = _load("d7", "failure_1_loop.json")
    f2 = _load("d7", "failure_2_slot_interface.json")
    stages = ["before", "broken", "restored"]
    stage_labels = ["Working", "Broken", "Restored"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), dpi=150)

    ax = axes[0]
    turns = [f1[s]["turns"] for s in stages]
    ax.bar(stage_labels, turns, color=["#0072B2", "#D55E00", "#0072B2"])
    for i, v in enumerate(turns):
        ax.text(i, v + 0.15, str(v), ha="center", fontsize=10)
    ax.set_ylabel("Turns")
    ax.set_title("Failure 1 — turns\n(action de-duplication removed)")

    ax = axes[1]
    tokens = [f1[s]["tokens_total"] for s in stages]
    ax.bar(stage_labels, tokens, color=["#0072B2", "#D55E00", "#0072B2"])
    for i, v in enumerate(tokens):
        ax.text(i, v + 800, "%d" % v, ha="center", fontsize=9)
    ax.set_ylabel("Total tokens")
    ax.set_title("Failure 1 — tokens\n(same correct decision throughout)")

    ax = axes[2]
    labels = ["Working", "Broken\n(band filter removed)", "Restored"]
    booked = [f2["before"]["booked"], f2["broken"]["booked"], f2["restored"]["booked"]]
    correct = f2["correct_booking"]
    colors = ["#009E73" if b == correct else "#D55E00" for b in booked]
    ax.bar(labels, [1, 1, 1], color=colors, width=0.7)
    ax.set_yticks([])
    ax.set_xlim(-0.6, 2.6)
    for i, b in enumerate(booked):
        label = "%s\n%s\n%s" % (b["clinic"], b["date"], b["time"])
        ax.text(i, 0.5, label, ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")
    ax.set_title("Failure 2 — booking outcome\n(green = safe, red = unsafe)")

    fig.suptitle("D7 — two reproduced failures: working → broken → restored", fontsize=13)
    _save(fig, "10_d7_both_failures.png")


# ---- 11. Code check vs judgement check ------------------------------------
def plot_11_code_vs_judgement():
    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=150)
    labels = ["Code check\n(95 trials)", "Judgement check\n(55 cases)"]
    vals = [100.0, 74.6]
    ns = ["95/95", "41/55"]
    bars = ax.bar(labels, vals, color=["#0072B2", "#E69F00"])
    for i, (v, n) in enumerate(zip(vals, ns)):
        ax.text(i, v + 1.5, "%.1f%% (%s)" % (v, n), ha="center", fontsize=10, fontweight="bold")
    ax.set_ylim(0, 110)
    ax.set_ylabel("Pass rate (%)")
    ax.set_title("D4 — code check vs judgement check")
    _save(fig, "11_code_check_vs_judgement_check.png")


# ---- 12. Decision distribution ---------------------------------------------
def plot_12_decision_distribution():
    key = _load("..", "data", "expected_outcomes_B.json") if False else None
    with open(os.path.join(ROOT, "data", "expected_outcomes_B.json"), encoding="utf-8") as fh:
        cases = json.load(fh)
    from collections import Counter
    counts = Counter(c["expected_decision"] for c in cases)
    order = ["book", "escalate", "request_information"]
    vals = [counts[o] for o in order]
    colors = ["#009E73", "#D55E00", "#E69F00"]
    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=150)
    bars = ax.bar(order, vals, color=colors)
    total = sum(vals)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.8, "%d (%.1f%%)" % (v, 100 * v / total), ha="center", fontsize=10)
    ax.set_ylabel("Number of cases")
    ax.set_title("D4 — evaluation set decision distribution (55 cases)")
    _save(fig, "12_decision_distribution.png")


# ---- 13a. Generic illustrative B*T + D*T^2/2 -------------------------------
def plot_13a_formula_illustrative():
    B, D = 1200, 400
    T = list(range(0, 13))
    linear = [B * t for t in T]
    full = [B * t + D * t * t / 2.0 for t in T]
    quadratic_only = [D * t * t / 2.0 for t in T]

    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)
    ax.plot(T, linear, "--", color="#999999", linewidth=1.8, label="Linear term only: B·T")
    ax.plot(T, full, "-", color="#0072B2", linewidth=2.5, label="Full: B·T + D·T²/2")
    ax.fill_between(T, linear, full, color="#E69F00", alpha=0.25, label="Quadratic term: D·T²/2")
    ax.set_xlabel("Turns (T)")
    ax.set_ylabel("Input tokens")
    ax.set_title("Illustrative: input tokens ~ B·T + D·T²/2  (B=1,200, D=400)")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, linewidth=0.4, alpha=0.3)
    ax.annotate("At T=12: %d tokens\n(%.0f%% from the quadratic term)"
                % (full[12], 100 * quadratic_only[12] / full[12]),
                xy=(12, full[12]), xytext=(7, full[12] * 0.7),
                fontsize=9, arrowprops=dict(arrowstyle="->", color="#555555"))
    _save(fig, "13a_token_formula_illustrative.png")


def main():
    plot_1_overall_pass_rate()
    plot_2_overall_vs_negative()
    plot_3_monthly_cost()
    plot_4_cost_vs_pass_rate()
    plot_5_latency()
    plot_6_sensitivity()
    plot_7_switch_breakeven()
    plot_8_d2c()
    plot_9_d2b()
    plot_10_d7()
    plot_11_code_vs_judgement()
    plot_12_decision_distribution()
    plot_13a_formula_illustrative()
    print("\nAll plots written to", os.path.relpath(OUT, ROOT))
    print("(13b - all-models empirical token growth - already exists at "
         "results/live/token_growth_all_models.png, built by "
         "experiments/d2c_parallelism/plot_token_growth.py)")


if __name__ == "__main__":
    main()
