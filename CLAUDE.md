# Gainsight Hub Extensions Plugin

## Eval Rules

- **Baseline isolation**: When running skill evals, baseline (without_skill) agents must run in an isolated git worktree with `skills/`, fixture widgets, test directories, and `*-workspace/` eval output directories removed before execution. This prevents baselines from learning framework patterns by reading repo files or prior eval outputs, which inflates their scores and compresses the skill delta.
