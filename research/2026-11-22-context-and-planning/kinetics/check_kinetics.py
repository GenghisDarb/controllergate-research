"""Exact, illustrative state/time counterexample; not a new biological result.

Also checks arithmetic from the rounded Table 1 means in Hammar et al. (2014),
doi:10.1038/ng.2905. This is not a reanalysis of their raw measurements.
Run: python check_kinetics.py
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parent


def state_model(a: float, b: float, tau: float = 1.0) -> dict:
    """0 -> 1 at rate a; 1 -> 0 at rate b; arbitrary time units."""
    if a <= 0 or b <= 0 or tau < 0:
        raise ValueError("positive rates and nonnegative duration required")
    occupancy = a / (a + b)
    q = np.array([[-a, a], [b, -b]], dtype=float)
    endpoint_formula = occupancy + (1.0 - occupancy) * math.exp(-(a + b) * tau)
    endpoint_matrix = float(expm(q * tau)[1, 1])
    continuous_on = math.exp(-b * tau)
    np.testing.assert_allclose(endpoint_formula, endpoint_matrix, rtol=1e-12, atol=1e-14)
    np.testing.assert_allclose(np.array([1 - occupancy, occupancy]) @ q, 0, atol=1e-14)
    assert continuous_on <= endpoint_formula + 1e-14
    return {
        "rate_on": a, "rate_off": b, "duration": tau,
        "stationary_on_probability": occupancy,
        "normalized_autocorrelation": math.exp(-(a + b) * tau),
        "on_at_end_given_on_at_start": endpoint_formula,
        "continuous_on_given_on_at_start": continuous_on,
        "stationary_probability_of_continuous_on_window": occupancy * continuous_on,
        "independent_matrix_exponential_endpoint_check": endpoint_matrix,
    }


def main() -> None:
    slow = state_model(0.1, 0.1)
    fast = state_model(10.0, 10.0)
    assert slow["stationary_on_probability"] == fast["stationary_on_probability"] == 0.5
    assert slow["continuous_on_given_on_at_start"] / fast["continuous_on_given_on_at_start"] > 19000
    for a, b, t in [(0.1, 1.3, 0), (0.1, 1.3, 2), (1.7, 0.2, 3), (10, 10, 1)]:
        state_model(a, b, t)

    source = {
        "title": "Direct measurement of transcription factor dissociation excludes a simple operator occupancy model for gene regulation",
        "authors": "Hammar et al.", "year": 2014, "doi": "10.1038/ng.2905",
        "url": "https://elflab.icm.uu.se/lore/ref/NatureGen-2014-Hammar.pdf",
        "table": 1,
        "scope": "Published rounded means only; no raw data, covariance, refitting or new significance test.",
    }
    published = []
    for name, on_s, off_min, model_rr, model_sem, reporter, reporter_sem in [
        ("lacO1", 30.9, 5.3, 11.2, 0.5, 10.0, 1.3),
        ("lacOsym", 27.6, 9.3, 21.2, 0.9, 29.7, 3.4),
    ]:
        off_s = 60.0 * off_min
        recalculated = (on_s + off_s) / on_s
        # Rounded published input means need not reproduce a ratio derived from
        # underlying observations. Do not label the small difference an error.
        assert abs(recalculated - model_rr) < 0.11
        published.append({
            "operator": name, "tau_on_seconds": on_s, "tau_off_minutes": off_min,
            "tau_off_seconds": off_s, "repression_ratio_from_rounded_means": recalculated,
            "paper_model_repression_ratio": model_rr, "paper_model_SEM": model_sem,
            "paper_reporter_repression_ratio": reporter, "paper_reporter_SEM": reporter_sem,
        })

    receipt = {
        "status": "PASS",
        "scope": "Exact Markov-chain counterexample and arithmetic check, not biological validation or a novel theorem.",
        "illustrative_time_units": "arbitrary; not fitted to Hammar or any ControllerGate trace",
        "models": {"slow": slow, "fast": fast},
        "published_source": source, "published_table_arithmetic": published,
        "checks": ["stationary distributions satisfy pi Q = 0", "closed-form endpoints match scipy.linalg.expm",
                   "continuous-on events are subsets of endpoint-on events", "two models have identical occupancy",
                   "published arithmetic uses consistent units and explicitly rounded inputs"],
        "limits": ["No new molecular measurement", "No evidence selecting fourteen layers",
                   "No claim that current ControllerGate lacks freshness or revocation checks",
                   "No claim that an endpoint check is always the wrong specification: it depends on the task"],
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (ROOT / "kinetics_results.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), gridspec_kw={"width_ratios": [1, 1.45]})
    colors = ["#2878aa", "#bb4c25"]
    axes[0].bar([0, 1], [0.5, 0.5], width=0.55, color=colors)
    axes[0].set_xticks([0, 1], ["Slow switching", "Fast switching"])
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Probability of state 1")
    axes[0].set_title("Identical steady occupancy")
    for x in [0, 1]:
        axes[0].text(x, 0.53, "50%", ha="center", weight="bold")
    durations = np.linspace(0, 1, 301)
    for b, label, color in [(0.1, "Slow: off rate 0.1", colors[0]), (10, "Fast: off rate 10", colors[1])]:
        axes[1].plot(durations, np.exp(-b * durations), label=label, color=color, lw=2.5)
    axes[1].set_xlabel("Required continuous duration (arbitrary units)")
    axes[1].set_ylabel("Probability of staying continuously in state 1")
    axes[1].set_ylim(0, 1.03)
    axes[1].set_title("Uninterrupted availability\n(given state 1 at the start)")
    axes[1].legend(loc="center right", frameon=False)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
    fig.suptitle("A pathway and its average occupancy do not determine its timing", fontsize=14, weight="bold")
    fig.text(0.5, 0.015, "Illustrative standard two-state model. No biological data fitted; no TORUS-specific result.", ha="center", fontsize=9)
    fig.tight_layout(rect=[0, 0.05, 1, 0.94])
    fig.savefig(ROOT / "same_occupancy_different_timing.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(json.dumps({"status": receipt["status"], "slow": slow, "fast": fast,
                      "published_table_arithmetic": published}, indent=2))


if __name__ == "__main__":
    main()
