"""Export a scientific figure from the reviewed, frozen dynamics experiment.

Only pinned LadderKernel._relax is executed. RNG draws are replayed in exactly
the original case order, including the validation draws preceding each start.
The script does not import or execute the root audit program and writes only
inside this figure directory. This is a visualization replay, not new evidence
from an independent physical system.
"""
from __future__ import annotations

import ast
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

HERE = Path(__file__).resolve().parent
DYNAMICS = HERE.parents[1] / "dynamics"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_step():
    tree = ast.parse((DYNAMICS / "source_snapshot/kernels.py").read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "LadderKernel")
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "_relax")
    fn.decorator_list = []
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    scope = {}
    exec(compile(module, "figure_pinned_relax_only", "exec"), scope)
    return scope["_relax"]


def write_csv(name, header, rows):
    with (HERE / name).open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def main():
    inputs = ["experiment_spec.json", "FROZEN_DESIGN.json", "run_operator_audit.py",
              "results.json", "summary.json", "source_snapshot/kernels.py",
              "source_snapshot/SOURCE_PROVENANCE.json", "independent_operator_review_receipt.json"]
    initial_hashes = {name: sha(DYNAMICS / name) for name in inputs}
    spec = json.loads((DYNAMICS / "experiment_spec.json").read_text())
    freeze = json.loads((DYNAMICS / "FROZEN_DESIGN.json").read_text())
    saved_results = json.loads((DYNAMICS / "results.json").read_text())
    review = json.loads((DYNAMICS / "independent_operator_review_receipt.json").read_text())
    source_provenance = json.loads((DYNAMICS / "source_snapshot/SOURCE_PROVENANCE.json").read_text())
    for path, expected in freeze["files"].items():
        assert sha(DYNAMICS / path) == expected, path
    assert saved_results["frozen_design_sha256"] == initial_hashes["FROZEN_DESIGN.json"]
    assert review["status"] == "PASS_WITH_DECLARED_SCOPE"
    for path in ["results.json", "run_operator_audit.py", "source_snapshot/kernels.py"]:
        assert review["files"][path] == initial_hashes[path], path

    relax = source_step()
    rng = np.random.default_rng(spec["seed"])
    all_checks = []
    focus = None
    for n in spec["sizes"]:
        parent = np.sin(2*np.pi*np.arange(n)/n) + .3*np.cos(6*np.pi*np.arange(n)/n)
        zero = np.zeros(n)
        for a in spec["anchorings"]:
            saved = next(c for c in saved_results["cases"] if c["N"] == n and c["a"] == a)
            # These draws were used by root's per-state gradient/source checks.
            for _ in range(spec["random_states_per_case"]):
                rng.normal(size=n)
            initial = parent + .4*rng.normal(size=n)
            original = initial.copy()
            candidate = initial.copy()
            original_rms, candidate_rms = [], []
            for t in range(spec["trajectory_steps"]+1):
                original_rms.append(float(np.sqrt(np.mean((original-parent)**2))))
                candidate_rms.append(float(np.sqrt(np.mean((candidate-parent)**2))))
                if t < spec["trajectory_steps"]:
                    original = np.asarray(relax(original.tolist(), parent.tolist(), a))
                    candidate = parent + np.asarray(relax((candidate-parent).tolist(), zero.tolist(), a))
            errors = {
                "original": abs(original_rms[-1]-saved["original_final_parent_rms"]),
                "candidate": abs(candidate_rms[-1]-saved["candidate_final_parent_rms"]),
            }
            assert max(errors.values()) <= 1e-14, (n, a, errors)
            all_checks.append({"N": n, "a": a, "final_rms_absolute_errors": errors})
            if n == 14 and a == .5:
                focus = dict(parent=parent, initial=initial, original_rms=np.asarray(original_rms),
                             candidate_rms=np.asarray(candidate_rms), saved=saved)
    assert focus is not None and len(all_checks) == 20
    assert focus["parent"].min() < 0
    h = np.asarray(focus["saved"]["impulse_history"])
    # Check the plotted, saved impulse values with the same pinned source.
    state = np.eye(14)[0]
    replay = [state.copy()]
    for _ in range(spec["impulse_steps"]):
        state = np.asarray(relax(state.tolist(), [0.]*14, .5))
        replay.append(state.copy())
    impulse_error = float(np.max(np.abs(np.asarray(replay)-h)))
    assert impulse_error <= 1e-15
    first_nonzero = int(np.flatnonzero(h[:,7] > 0)[0])
    threshold = 1e-6
    crossing = int(np.flatnonzero(h[:,7] >= threshold)[0])
    assert first_nonzero == 7 and crossing == 17
    assert np.all(h[:7,7] == 0)
    assert h[16,7] < threshold <= h[17,7]
    visibility = next(v for v in focus["saved"]["visibility"] if v["floor"] == threshold)
    assert visibility["first_detected_step"][7] == crossing

    t = np.arange(spec["trajectory_steps"]+1)
    write_csv("reference_rms_trajectories.csv",
              ["update", "original_parent_rms", "residual_candidate_parent_rms"],
              zip(t, focus["original_rms"], focus["candidate_rms"]))
    write_csv("reference_and_initial_state.csv", ["node", "supplied_parent", "shared_initial_state"],
              zip(range(14), focus["parent"], focus["initial"]))
    write_csv("unit_impulse_full_history.csv",
              ["update", "node", "shortest_ring_distance_edges", "impulse_amplitude"],
              ((step, node, min(node,14-node), float(value))
               for step, row in enumerate(h) for node, value in enumerate(row)))

    bg, fg, muted, grid = "#15191E", "#F0F3F6", "#BAC4CD", "#53606B"
    cyan, gold = "#72DAE6", "#F6BE68"
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 11,
        "text.color": fg, "axes.labelcolor": fg, "xtick.color": muted, "ytick.color": muted,
        "axes.edgecolor": muted, "axes.facecolor": bg, "figure.facecolor": bg,
        "savefig.facecolor": bg, "svg.fonttype": "none", "axes.linewidth": .8,
    })
    fig = plt.figure(figsize=(13, 7.4), dpi=180)
    axa = fig.add_axes([.082, .29, .365, .50])
    axb = fig.add_axes([.558, .29, .329, .50])
    cax = fig.add_axes([.907, .29, .014, .50])

    fig.text(.082, .949, "Reference recovery and local propagation", fontsize=20, weight="bold")
    fig.text(.082, .900, "Reviewed synthetic audit  |  14-node ring  |  anchoring a = 0.5  |  discrete updates",
             fontsize=11.5, color=muted)
    fig.text(.082, .832, "A  Recovery of a supplied reference", fontsize=14, weight="bold")
    fig.text(.558, .832, "B  Propagation and declared visibility", fontsize=14, weight="bold")

    axa.semilogy(t, focus["original_rms"], color=gold, linewidth=2.4, label="Original rule")
    axa.semilogy(t, focus["candidate_rms"], color=cyan, linewidth=2.4, linestyle="--",
                 label="Residual candidate")
    axa.scatter([200], [focus["original_rms"][-1]], s=30, marker="o", color=gold, zorder=4)
    axa.scatter([200], [focus["candidate_rms"][-1]], s=30, marker="s", color=cyan, zorder=4)
    axa.set(xlim=(0,204), ylim=(1e-17,1), xlabel="Update count", ylabel="RMS difference from supplied reference")
    axa.set_xticks([0,50,100,150,200])
    axa.set_yticks([1,1e-4,1e-8,1e-12,1e-16])
    axa.minorticks_off()
    axa.grid(axis="y", color=grid, alpha=.45, linewidth=.7)
    axa.spines[["top","right"]].set_visible(False)
    legend = axa.legend(loc="upper right", bbox_to_anchor=(1,.82), fontsize=10.5, frameon=True,
                        facecolor=bg, edgecolor="none", framealpha=.95)
    for text in legend.get_texts():
        text.set_color(fg)

    # One representative node at each shortest distance; j=7 is unique.
    display_last = 32
    amplitudes = h[:display_last+1,:8].T
    log_amplitudes = np.ma.masked_all(amplitudes.shape)
    positive = amplitudes > 0
    log_amplitudes[positive] = np.log10(amplitudes[positive])
    cmap = plt.get_cmap("cividis").copy()
    cmap.set_bad("#303940")
    im = axb.pcolormesh(np.arange(34)-.5, np.arange(9)-.5, log_amplitudes,
                        cmap=cmap, vmin=-9, vmax=0, shading="flat",
                        edgecolors="none", antialiased=False, rasterized=False)
    axb.set(xlim=(-.5,32.5), ylim=(-.5,7.5))
    distance = np.arange(8)
    axb.plot(distance, distance, color=fg, linestyle=":", linewidth=1.5)
    first_visible = visibility["first_detected_step"][:8]
    axb.plot(first_visible, distance, color=gold, linestyle="--", linewidth=1.8)
    axb.plot([7],[7], marker="o", markerfacecolor=bg, markeredgecolor=fg,
             markeredgewidth=1.7, markersize=8, linestyle="none", zorder=5)
    axb.plot([17],[7], marker="s", markerfacecolor=bg, markeredgecolor=gold,
             markeredgewidth=1.7, markersize=8, linestyle="none", zorder=5)
    axb.set(xlabel="Updates after unit impulse", ylabel="Distance from source (graph edges)")
    axb.set_xticks([0,7,17,24,32])
    axb.set_yticks(range(8))
    cb = fig.colorbar(im, cax=cax, ticks=[-9,-6,-3,0])
    cb.set_label(r"$\log_{10}$ impulse amplitude", labelpad=10)
    cb.ax.tick_params(labelsize=10)
    cb.outline.set_edgecolor(muted)

    fig.text(.082, .216, "At update 200", fontsize=10.8, color=muted)
    fig.text(.082, .181, "Original: 0.06811", fontsize=11.1, color=gold)
    fig.text(.272, .181, "Residual: 2.88 × 10⁻¹⁶", fontsize=11.1, color=cyan)
    fig.text(.272, .146, "Numerical precision", fontsize=9.7, color=muted)
    fig.legend(handles=[
        Line2D([0],[0], color=fg, linestyle=":", marker="o", markerfacecolor=bg,
               markeredgewidth=1.3, label="First nonzero: 7"),
        Line2D([0],[0], color=gold, linestyle="--", marker="s", markerfacecolor=bg,
               markeredgewidth=1.3, label="First ≥10⁻⁶: 17")],
        loc="lower left", bbox_to_anchor=(.552,.164), frameon=False,
        ncol=1, fontsize=10.7, handlelength=2.0, labelcolor=fg)
    fig.text(.558, .136, "Opposite node, 7 edges away; first 32 of 64 updates shown.", fontsize=9.7, color=muted)
    fig.text(.082, .101, "A: shared start; signed reference supplied, not predicted. B: fixed zero parent; the dark upper-left wedge shows exact zeros.",
             fontsize=9.8, color=muted)
    fig.text(.082, .065, "Model coordinates and update counts have no calibrated physical units. The 10⁻⁶ threshold is declared, not a measured noise floor.",
             fontsize=9.8, color=muted)
    fig.text(.082, .029, "The nonnegative projection extension is separate and is not applied in this figure.", fontsize=9.8, color=muted)

    png = HERE / "recovery_and_propagation.png"
    svg = HERE / "recovery_and_propagation.svg"
    fig.savefig(png, dpi=180, metadata={"Title":"Reference recovery and local propagation",
                                      "Description":"Frozen synthetic N14 a0.5 audit; supplied reference and declared amplitude threshold."})
    fig.savefig(svg, metadata={"Title":"Reference recovery and local propagation",
                              "Description":"Reproducible scientific figure; see figure_provenance.json."})
    plt.close(fig)
    assert png.stat().st_size < 1_000_000
    assert all(sha(DYNAMICS/name) == digest for name,digest in initial_hashes.items())

    artifacts = ["plot_recovery_propagation.py", "reference_rms_trajectories.csv",
                 "reference_and_initial_state.csv", "unit_impulse_full_history.csv",
                 png.name, svg.name]
    provenance = {
        "schema":"torus_scientific_figure_provenance.v1",
        "generated_utc":datetime.now(timezone.utc).isoformat(),
        "input_directory":"../../dynamics", "input_sha256":initial_hashes,
        "source_commit":source_provenance["commit"],
        "source_blob_sha":source_provenance["git_blob_sha"],
        "replay":"Source-only AST extraction; consume all 20 validation draws then the initial-state draw per case in original frozen order.",
        "final_rms_checks_all_cases":all_checks,
        "maximum_final_rms_absolute_error":max(v for row in all_checks for v in row["final_rms_absolute_errors"].values()),
        "selected_impulse_replay_absolute_error":impulse_error,
        "selected_case":{"N":14,"a":.5,"trajectory_steps":200,"impulse_steps":64,"displayed_impulse_steps":[0,32]},
        "panel_A":{"original_final_rms":focus["original_rms"][-1],"candidate_final_rms":focus["candidate_rms"][-1],
                   "signed_supplied_parent":True,"projection_applied":False},
        "panel_B":{"node":7,"distance_edges":7,"first_nonzero_update":7,"first_at_or_above_1e_minus6_update":17,
                   "amplitude_at_7":h[7,7],"amplitude_at_16":h[16,7],"amplitude_at_17":h[17,7],
                   "gray_cells":"exact zeros, not missing values","distance_rows":"representative nodes j=0..7",
                   "color_scale":"log10 amplitude, fixed range [-9,0]; exact zero cells masked distinctly"},
        "input_files_unchanged":True,
        "scope":["Synthetic replay, not new physical data.","Supplied reference is not predicted.",
                 "No preferred layer-count conclusion.","No physical time calibration or empirical detector noise model.",
                 "Projection extension does not apply to this signed-parent figure."],
        "versions":{"numpy":np.__version__,"matplotlib":matplotlib.__version__},
        "artifact_sha256":{name:sha(HERE/name) for name in artifacts},
        "artifact_bytes":{name:(HERE/name).stat().st_size for name in artifacts},
    }
    (HERE/"figure_provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    print(json.dumps({"status":"REPLAY_VERIFIED_FIGURE_EXPORTED", "cases_replayed":len(all_checks),
                      "maximum_final_rms_absolute_error":provenance["maximum_final_rms_absolute_error"],
                      "impulse_replay_absolute_error":impulse_error,
                      "png_bytes":png.stat().st_size,"svg_bytes":svg.stat().st_size},indent=2))


if __name__ == "__main__":
    main()
