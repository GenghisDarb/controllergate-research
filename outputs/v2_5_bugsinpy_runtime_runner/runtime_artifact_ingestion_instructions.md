# v2.5 Runtime Artifact Ingestion Instructions

After downloading and unpacking the GitHub Actions artifact, verify it contains:

- `runtime_environment.txt`
- `bugsinpy_install_log.txt`
- `bugsinpy_command_probe.txt`
- `runtime_probe_summary.json`
- `black_2/`
- `youtube_dl_1/`
- `black_8/`

Then run the parser:

```powershell
C:\Users\thisb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\v2_5_parse_bugsinpy_runtime_artifacts.py <artifact-folder>
```

Handoff logic:

- 3 promoted candidates: recommend `v2_5_bugsinpy_real_bug_limited_replay_execution`.
- 1-2 promoted candidates: recommend `v2_5_small_bugsinpy_probe_execution`.
- 0 promoted candidates: recommend `runner_environment_fix_required`.

Do not use fixed/gold patches as decision-time inputs. Do not run full scoring from this parser.
