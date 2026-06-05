# v2.5 GitHub Actions Usage Instructions

The workflow creates a Linux runtime path for BugsInPy replay.

1. Commit and push this workflow to GitHub.
2. Open the repository on GitHub.
3. Go to **Actions**.
4. Select **v2_5_bugsinpy_runtime_probe**.
5. Click **Run workflow** on branch `controllergate-v1.7-alpha-real-trace-pilot`.
6. Wait for the run to finish.
7. Download the artifact named `v2_5_bugsinpy_runtime_probe_artifacts`.
8. Provide the artifact back to Codex or unpack it into the repo workspace.
9. Run:

```powershell
C:\Users\thisb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\v2_5_parse_bugsinpy_runtime_artifacts.py <path-to-artifact-folder>
```

Candidate replay readiness requires fresh checkout/compile/test logs. Candidate metadata alone does not prove replay readiness.

Gold/fixed patches are outcome-only. Full scoring remains disallowed. Self-maintaining software remains undemonstrated.
