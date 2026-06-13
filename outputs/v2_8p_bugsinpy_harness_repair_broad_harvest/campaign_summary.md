# v2.8p BugsInPy Harness Repair Broad Harvest

Status: `blocked_pending_v2_8p_harness_repair_broad_harvest_artifact`.

- Official v2.8o artifact was verified locally and recorded as a harness regression baseline.
- v2.8p must restore `youtube-dl:1` and `black:4` as scoreable before broad harvest.
- Raw `pytest` commands normalize to `python -m pytest`, with pytest installed for pytest candidates.
- Returncode 127 is treated as harness/command-normalization failure, not candidate failure.
- Full scoring remains NOT_RUN / disallowed.
- Memory lift is not demonstrated.
- Self-maintaining software is not demonstrated.
