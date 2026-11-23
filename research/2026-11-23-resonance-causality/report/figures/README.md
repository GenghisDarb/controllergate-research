# Reference recovery and local propagation

## Figure files

- `recovery_and_propagation.png`: 2340 × 1332 pixels, dark neutral background; approximately 280 KB.
- `recovery_and_propagation.svg`: scalable export with editable text and vector heatmap cells; approximately 81 KB.
- `plot_recovery_propagation.py`: complete reconstruction and plotting script.
- `figure_provenance.json`: frozen input hashes, source identity, all replay comparisons, output hashes and scope.
- `visual_review.json`: final image inspection and export checks.

## Suggested scientific caption

**Reference restoration and finite local propagation in a supplied synthetic ladder model.** Both panels use the recovered Field Studio `LadderKernel._relax` update on a fourteen-node cycle with anchoring parameter \(a=0.5\) and step factor 0.42. **(A)** Root-mean-square difference from a fixed, supplied signed reference \(p_i=\sin(2\pi i/14)+0.3\cos(6\pi i/14)\), averaged across fourteen coordinates. The original rule and the new residual candidate start from the same seeded state. After 200 updates, their RMS differences are 0.06811019837998819 and \(2.884444029575346\times10^{-16}\), respectively. The latter is at floating-point precision. The residual candidate changes the coupling objective to preserve the supplied reference; it does not predict that reference or establish improved performance on external data. **(B)** Logarithmic unit-impulse response with fixed zero parent. Rows show representative nodes at shortest graph distances zero through seven; the opposite node is unique. Its first nonzero response is at update 7, with amplitude \(2.1985944104003897\times10^{-9}\). It first meets the declared amplitude threshold \(10^{-6}\) at update 17, with amplitude \(1.0380335560431822\times10^{-6}\); its amplitude at update 16 is \(8.799530868140716\times10^{-7}\). Dotted and dashed curves mark first nonzero response and first threshold crossing at each displayed distance. The upper-left dark wedge contains exact zeros. The heatmap displays updates 0–32; the data file retains all 64 updates after the initial impulse. Update counts and amplitudes have no calibrated physical units. The threshold is a numerical probe, not an empirical detector-noise model. The nonnegative projection extension is separate and is not used in this signed-reference figure. Neither panel selects fourteen as a preferred layer count.

## Data and replay

The source is the already reviewed `../../dynamics/results.json` and its frozen source/specification. No frozen file was modified. The script verifies input hashes and the existing independent review receipt. It extracts only `_relax` from the archived module and consumes the random draws in the original sequence: twenty validation-state draws followed by one initial-state draw for each case, traversing all size/anchoring combinations in the frozen order.

All twenty cases' final RMS values match their stored values **exactly in this runtime**; the maximum absolute difference is zero. The selected saved impulse history also matches its source replay exactly. This is a checked visualization replay of synthetic results, not independent experimental evidence.

| Data file | Grain and contents |
|---|---|
| `reference_rms_trajectories.csv` | 201 updates, with original and residual-candidate RMS differences |
| `reference_and_initial_state.csv` | Fourteen nodes, with supplied reference and shared starting coordinates |
| `unit_impulse_full_history.csv` | 910 node/update rows: 65 states × fourteen nodes, retaining distance and exact saved floating-point amplitude |

## Reproduce

From any working directory with NumPy and Matplotlib available:

```sh
python /absolute/path/to/report/figures/plot_recovery_propagation.py
```

The script resolves its input paths relative to its own directory. It writes only to this figure folder and verifies that all frozen inputs remain unchanged. The figure exports and their provenance are regenerated; the frozen experiment is not rerun or overwritten.

## Visual verification

The final PNG was opened and inspected. During authoring, an initial legend that covered the original rule's plateau was moved to an empty region, and an ambiguous statement about gray cells was changed to identify the exact-zero wedge. The final labels, marked events, legends, scope notes and export boundaries were checked for legibility and overlap. The SVG parses successfully and retains text elements. Distinctions between the two trajectories and the two onset curves use line styles and marker shapes as well as color. No new physical uncertainty band is shown because these are deterministic model trajectories, not sampled empirical estimates.
