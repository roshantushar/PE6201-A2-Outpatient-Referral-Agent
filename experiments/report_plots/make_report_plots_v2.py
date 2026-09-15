#!/usr/bin/env python3
"""
REPORT PLOTS v2 - specific chart forms requested for the report:
reliability-vs-turns, dumbbell, donut, lollipop, slope chart, stacked
bar, and a D7 failure-2 state-flow diagram. All real data, same
committed results/ files as make_report_plots.py.

Items already built in make_report_plots.py with an equivalent form
are NOT rebuilt here (D2(c) sequential-vs-parallel = 08_*, overall vs
negative = 02_*, the B*T+D*T^2/2 curve = 13a_*) - see the printed note
at the end for exactly which files satisfy which requested item.
====================================================================
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(RESULTS, "report_plots")
os.makedirs(OUT, exist_ok=True)

COLORS = {
    "openai/gpt-4o-mini": "#0072B2",
    "google/gemini-2.5-flash-lite": "#E69F00",
    "qwen/qwen-2.5-72b-instruct": "#009E73",
    "meta-llama/llama-3.1-8b-instruct": "#D55E00",
    "mistralai/mistral-nemo": "#CC79A7",
    "anthropic/claude-3-haiku": "#999999",
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


# ---- 1. Reliability vs turns ---------------------------------------------
def plot_reliability_vs_turns():
    d = _load("..", "experiments", "d0", "reliability_calc.json") if False else \
        json.load(open(os.path.join(ROOT, "experiments", "d0", "reliability_calc.json"), encoding="utf-8"))
    live = d["live_one_model"]
    s_v1 = live["v1"]["s_per_step_at_median_T"]
    s_v2 = live["v2"]["s_per_step_at_median_T"]
    T = list(range(1, 13))

    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=150)
    for s, label, color in [(s_v1, "v1 (measured s=%.4f)" % s_v1, "#D55E00"),
                            (0.90, "illustrative s=0.90", "#999999"),
                            (0.9741, "illustrative s=0.9741 (P=0.90 at T=4)", "#E69F00"),
                            (s_v2, "v2 (measured s=%.4f)" % s_v2, "#009E73")]:
        ys = [s ** t * 100 for t in T]
        style = "-" if label.startswith(("v1", "v2")) else "--"
        ax.plot(T, ys, style, color=color, linewidth=2.2, label=label, marker="o", markersize=4)
    ax.axvline(4, color="#cccccc", linewidth=1, zorder=0)
    ax.text(4.1, 8, "this project's\nmedian T=4", fontsize=8, color="#666666")
    ax.set_xlabel("Turns (T)")
    ax.set_ylabel("Predicted run success rate P = sᵀ (%)")
    ax.set_title("D0 — reliability vs turns: same per-step quality, different turn count")
    ax.set_ylim(0, 105)
    ax.legend(loc="lower left", fontsize=8.5)
    ax.grid(True, linewidth=0.4, alpha=0.3)
    _save(fig, "14_reliability_vs_turns.png")


# ---- 2. Prompt-prefix cost of rejected tools ------------------------------
def plot_prefix_cost_rejected_tools():
    d = _load("descriptors", "tool_set_comparison.json")
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), dpi=150)

    ax = axes[0]
    labels = ["Shortest defensible\nset (%d tools)" % d["trimmed_tool_count"],
              "With 2 rejected\ntools (%d tools)" % d["larger_tool_count"]]
    vals = [d["trimmed_tokens_est"], d["larger_tokens_est"]]
    ax.bar(labels, vals, color=["#009E73", "#D55E00"])
    for i, v in enumerate(vals):
        ax.text(i, v + 20, "%d tok" % v, ha="center", fontsize=10)
    ax.set_ylabel("Prompt-prefix tokens (est.)")
    ax.set_title("Prompt prefix size,\nrejected tools in vs out")

    ax = axes[1]
    n = d["total_turns_one_full_pass"]
    wasted = d["wasted_tokens_est_one_full_pass"]
    per_turn = d["overhead_tokens_est_per_turn"]
    labels = ["Overhead per turn", "Wasted over one\nfull %d-turn pass" % n]
    ax.bar(labels[0], per_turn, color="#D55E00")
    ax.bar(labels[1], wasted, color="#D55E00", alpha=0.6)
    for i, v in enumerate([per_turn, wasted]):
        ax.text(i, v * 1.02, "%d tok" % v, ha="center", fontsize=10)
    ax.set_ylabel("Tokens (est.)")
    ax.set_title("Cost of never calling\nthe rejected tools")

    fig.suptitle("D2(a) — prompt-prefix cost of the 2 rejected tools (never called by the reference solver)", fontsize=12)
    _save(fig, "15_prompt_prefix_cost_rejected_tools.png")


# ---- 3. D2(b) observation-size dumbbell -----------------------------------
def plot_d2b_dumbbell():
    d = _load("descriptors", "single_tool_ablation_get_clinic_slots.json")
    v1 = d["v1_weak_descriptor_and_verbose_return"]["mean_get_clinic_slots_tokens_returned_per_call"]
    v2 = d["v2_full_descriptor_and_compact_return"]["mean_get_clinic_slots_tokens_returned_per_call"]

    fig, ax = plt.subplots(figsize=(8, 3.5), dpi=150)
    y = 0
    ax.plot([v2, v1], [y, y], color="#999999", linewidth=2.5, zorder=1)
    ax.scatter([v1], [y], s=220, color="#D55E00", zorder=3, label="v1 (verbose)")
    ax.scatter([v2], [y], s=220, color="#009E73", zorder=3, label="v2 (compact)")
    ax.annotate("v1: %.1f tok/call" % v1, (v1, y), textcoords="offset points",
               xytext=(0, 20), ha="center", fontsize=10, fontweight="bold")
    ax.annotate("v2: %.1f tok/call" % v2, (v2, y), textcoords="offset points",
               xytext=(0, -28), ha="center", fontsize=10, fontweight="bold")
    ax.annotate("", xy=((v1 + v2) / 2, y + 0.35), xytext=((v1 + v2) / 2, y + 0.05),
               arrowprops=dict(arrowstyle="-"))
    ax.text((v1 + v2) / 2, y + 0.42, "-%.1f%%" % (100 * (v1 - v2) / v1), ha="center", fontsize=10, color="#555555")
    ax.set_yticks([])
    ax.set_ylim(-0.6, 0.8)
    ax.set_xlim(0, v1 * 1.2)
    ax.set_xlabel("Mean tokens returned per get_clinic_slots call")
    ax.set_title("D2(b) — observation-size dumbbell: verbose → compact return shape")
    _save(fig, "16_d2b_observation_size_dumbbell.png")


# ---- 5. Evaluation-set donut ------------------------------------------------
def plot_eval_donut():
    with open(os.path.join(ROOT, "data", "expected_outcomes_B.json"), encoding="utf-8") as fh:
        cases = json.load(fh)
    from collections import Counter
    counts = Counter(c["expected_decision"] for c in cases)
    order = ["book", "escalate", "request_information"]
    vals = [counts[o] for o in order]
    colors = ["#009E73", "#D55E00", "#E69F00"]
    labels = ["book\n%d (%.0f%%)" % (v, 100 * v / sum(vals)) for v in [vals[0]]] + \
             ["escalate\n%d (%.0f%%)" % (vals[1], 100 * vals[1] / sum(vals))] + \
             ["request_information\n%d (%.0f%%)" % (vals[2], 100 * vals[2] / sum(vals))]

    fig, ax = plt.subplots(figsize=(7, 7), dpi=150)
    wedges, _ = ax.pie(vals, colors=colors, startangle=90, wedgeprops=dict(width=0.42, edgecolor="white"))
    ax.legend(wedges, labels, loc="center", fontsize=10, frameon=False)
    ax.text(0, 0, "%d\ncases" % sum(vals), ha="center", va="center", fontsize=0)  # keep center clear for legend
    ax.set_title("D4 — evaluation set: 55 cases by decision", fontsize=12)
    _save(fig, "18_evaluation_set_donut.png")


# ---- 6. Live-model pass-rate lollipop --------------------------------------
def plot_lollipop_pass_rate():
    rows = _load("live", "model_comparison.json")
    by_model = {r["model"]: r for r in rows}
    models = sorted(HEADLINE_ORDER, key=lambda m: by_model[m]["pass_rate"])
    vals = [by_model[m]["pass_rate"] * 100 for m in models]

    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)
    y = range(len(models))
    for i, (m, v) in enumerate(zip(models, vals)):
        ax.plot([0, v], [i, i], color="#cccccc", linewidth=2, zorder=1)
        ax.scatter([v], [i], s=180, color=COLORS[m], zorder=3, edgecolors="white", linewidths=1)
        ax.text(v + 3, i, "%.1f%%" % v, va="center", fontsize=9)
    ax.set_yticks(list(y))
    ax.set_yticklabels([_short(m) for m in models])
    ax.set_xlim(0, 115)
    ax.set_xlabel("Overall pass rate (%)")
    ax.set_title("D5(b) — live-model pass rate (lollipop)")
    ax.axvline(100, color="#eeeeee", linewidth=1, zorder=0)
    _save(fig, "19_live_model_pass_rate_lollipop.png")


# ---- 9. Three-layer monthly cost, stacked ----------------------------------
def plot_three_layer_stacked():
    rows = _load("cost", "d6_measured_all_models.json")
    rows = sorted(rows, key=lambda r: r["monthly_cost_usd_at_4000_referrals"])
    models = [r["model"] for r in rows]
    REFERRALS = 4000
    l1 = [r["variable_model_cost_per_referral_usd_MEASURED"] * REFERRALS for r in rows]
    l2 = [r["expected_fallback_cost_per_referral_usd"] * REFERRALS for r in rows]
    l3 = [r["layer_3_fixed_monthly_usd"] for r in rows]

    fig, ax = plt.subplots(figsize=(9, 6), dpi=150)
    x = range(len(models))
    ax.bar(x, l1, color="#0072B2", label="Layer 1 — variable (tokens)")
    ax.bar(x, l2, bottom=l1, color="#D55E00", label="Layer 2 — expected fallback")
    bottom3 = [a + b for a, b in zip(l1, l2)]
    ax.bar(x, l3, bottom=bottom3, color="#999999", label="Layer 3 — fixed monthly")
    ax.set_yscale("log")
    ax.set_xticks(list(x))
    ax.set_xticklabels([_short(m) for m in models], rotation=20, ha="right")
    ax.set_ylabel("Monthly cost at 4,000 referrals (US$, log scale)")
    ax.set_title("D6 — three-layer monthly cost, stacked by model")
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "20_three_layer_monthly_cost_stacked.png")


# ---- 10. Success vs monthly cost scatter -----------------------------------
def plot_success_vs_monthly_cost():
    rows = _load("cost", "d6_measured_all_models.json")
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    for r in rows:
        m = r["model"]
        ax.scatter(r["success_rate_measured"] * 100, r["monthly_cost_usd_at_4000_referrals"],
                  color=COLORS.get(m, "#999999"), s=160, zorder=3, edgecolors="white", linewidths=1)
        ax.annotate(_short(m), (r["success_rate_measured"] * 100, r["monthly_cost_usd_at_4000_referrals"]),
                   textcoords="offset points", xytext=(8, 5), fontsize=9)
    ax.set_yscale("log")
    ax.set_xlabel("Measured success rate (%)")
    ax.set_ylabel("Monthly cost at 4,000 referrals (US$, log scale)")
    ax.set_title("D6 — success rate vs monthly cost (one point per model)")
    ax.grid(True, linewidth=0.4, alpha=0.3)
    _save(fig, "21_success_vs_monthly_cost_scatter.png")


# ---- 11. D7 failure 1 slope chart -------------------------------------------
def plot_d7_failure1_slope():
    f1 = _load("d7", "failure_1_loop.json")
    stages = ["before", "broken", "restored"]
    stage_labels = ["Working", "Broken", "Restored"]
    turns = [f1[s]["turns"] for s in stages]
    tokens = [f1[s]["tokens_total"] for s in stages]

    fig, axes = plt.subplots(1, 2, figsize=(10, 5.5), dpi=150)
    for ax, vals, label, color in [(axes[0], turns, "Turns", "#0072B2"),
                                   (axes[1], tokens, "Total tokens", "#E69F00")]:
        x = range(3)
        ax.plot(x, vals, "-o", color=color, linewidth=2.5, markersize=10, zorder=3)
        for i, v in enumerate(vals):
            ax.annotate(str(v), (i, v), textcoords="offset points", xytext=(0, 12),
                       ha="center", fontsize=10, fontweight="bold")
        ax.set_xticks(list(x))
        ax.set_xticklabels(stage_labels)
        ax.set_ylabel(label)
        ax.set_ylim(0, max(vals) * 1.25)
        ax.grid(True, axis="y", linewidth=0.4, alpha=0.3)
    fig.suptitle("D7 Failure 1 — loop control (action de-duplication removed): slope chart", fontsize=12)
    _save(fig, "22_d7_failure1_slope_chart.png")


# ---- 12. D7 failure 2 state-flow diagram -------------------------------------
def plot_d7_failure2_flow():
    f2 = _load("d7", "failure_2_slot_interface.json")
    fig, ax = plt.subplots(figsize=(13, 5), dpi=150)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 4)
    ax.axis("off")

    boxes = [
        (0.3, "Referral\nREF-5602\n(routine)", "#0072B2"),
        (2.8, "get_clinic_slots\nband filter\nREMOVED", "#D55E00"),
        (5.3, "Returns ALL slots,\nincl. urgent-band\nrows", "#D55E00"),
        (7.8, "Calling code takes\nband from the\nslot row itself", "#D55E00"),
        (10.3, "book_slot\nOPH-C1 (urgent)\n2026-09-15 09:40", "#B22222"),
    ]
    for x, text, color in boxes:
        box = FancyBboxPatch((x, 1.3), 1.9, 1.4, boxstyle="round,pad=0.08",
                             linewidth=1.5, edgecolor=color, facecolor=color, alpha=0.15)
        ax.add_patch(box)
        ax.text(x + 0.95, 2.0, text, ha="center", va="center", fontsize=8.5, fontweight="bold", color="#222222")

    for (x1, _, _), (x2, _, _) in zip(boxes[:-1], boxes[1:]):
        ax.annotate("", xy=(x2, 2.0), xytext=(x1 + 1.9, 2.0),
                   arrowprops=dict(arrowstyle="->", color="#555555", linewidth=1.5))

    correct = f2["correct_booking"]
    ax.text(6.5, 0.5, "Restored (band filter back): correctly books %s, %s %s"
           % (correct["clinic"], correct["date"], correct["time"]),
           ha="center", fontsize=9.5, color="#009E73", fontweight="bold")
    ax.text(6.5, 3.6, "D7 Failure 2 — tool interface: how the unsafe booking happens",
           ha="center", fontsize=13)
    _save(fig, "23_d7_failure2_state_flow_diagram.png")


def main():
    plot_reliability_vs_turns()
    plot_prefix_cost_rejected_tools()
    plot_d2b_dumbbell()
    plot_eval_donut()
    plot_lollipop_pass_rate()
    plot_three_layer_stacked()
    plot_success_vs_monthly_cost()
    plot_d7_failure1_slope()
    plot_d7_failure2_flow()
    print()
    print("Items satisfied by ALREADY-BUILT plots (equivalent form/content),")
    print("not rebuilt here:")
    print("  4  D2(c) sequential vs parallel  -> 08_d2c_sequential_vs_parallel.png")
    print("  7  Overall vs negative performance -> 02_overall_vs_negative_pass_rate.png")
    print("  8  B*T + D*T^2/2 context growth  -> 13a_token_formula_illustrative.png")
    print("                                      (+ 13b: results/live/token_growth_all_models.png, all-models)")


if __name__ == "__main__":
    main()
