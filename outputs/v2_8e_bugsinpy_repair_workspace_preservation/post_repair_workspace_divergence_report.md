# Post-repair Workspace Divergence

Git-only repair workspaces can omit BugsInPy checkout overlays, injected test context, or local files that existed in the validated pre-repair workspace. v2.8e therefore archives the validated baseline workspace and restores it into both no-memory and memory-enabled repair workspaces before replaying the target failure again.
