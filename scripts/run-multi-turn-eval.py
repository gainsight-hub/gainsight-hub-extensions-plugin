#!/usr/bin/env python3
"""
Multi-turn eval runner for build-extension skill.

Runs a single eval using claude CLI sessions with --resume for follow-up turns.
The agent works in a temporary workspace that mirrors the widgets-repository-template
structure, so the skill creates files in their natural locations (widgets/<name>/,
scripts/<name>/, stylesheets/<name>/).

After all turns complete, the runner collects created files into outputs/ for grading.

Usage:
    python scripts/run-multi-turn-eval.py \
        --eval-id 14 \
        --config with_skill \
        --output-dir build-extension-workspace/iteration-7/vague-multiturn/with_skill/run-1 \
        --skill-path skills/build-extension
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

EXTENSION_DIRS = ["widgets", "scripts", "stylesheets"]


def run_turn(session_id: str, prompt: str, work_dir: Path, resume: bool = False,
             permission_mode: str = "auto") -> dict:
    cmd = ["claude"]
    if resume:
        cmd += ["--resume", session_id]
    else:
        cmd += ["--session-id", session_id]
    cmd += ["-p", prompt, "--permission-mode", permission_mode]

    start = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(work_dir),
        timeout=300,
    )
    duration = time.time() - start

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "duration_seconds": round(duration, 1),
    }


def collect_outputs(work_dir: Path, output_dir: Path) -> list[str]:
    """Find extension files created in the workspace and copy to outputs/."""
    outputs_dir = output_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    collected = []

    for ext_dir_name in EXTENSION_DIRS:
        ext_dir = work_dir / ext_dir_name
        if not ext_dir.exists():
            continue
        for item in sorted(ext_dir.iterdir()):
            if not item.is_dir():
                continue
            # Copy the entire extension directory (e.g., widgets/my-widget/)
            dest = outputs_dir / ext_dir_name / item.name
            shutil.copytree(item, dest, dirs_exist_ok=True)
            for f in sorted(dest.rglob("*")):
                if f.is_file():
                    collected.append(str(f.relative_to(outputs_dir)))

    return collected


def main():
    parser = argparse.ArgumentParser(description="Multi-turn eval runner")
    parser.add_argument("--eval-file", default="skills/build-extension/evals/evals.json")
    parser.add_argument("--eval-id", type=int, required=True)
    parser.add_argument("--config", choices=["with_skill", "without_skill"], required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--skill-path", default="skills/build-extension")
    args = parser.parse_args()

    # Load eval
    evals_data = json.loads(Path(args.eval_file).read_text())
    eval_def = next((e for e in evals_data["evals"] if e["id"] == args.eval_id), None)
    if not eval_def:
        print(f"Error: eval id {args.eval_id} not found", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a clean workspace for the agent to work in
    work_dir = output_dir / "workspace"
    work_dir.mkdir(exist_ok=True)

    session_id = str(uuid.uuid4())
    transcript_turns = []

    # Build turn 1 — no output dir override, let the skill place files naturally
    if args.config == "with_skill":
        skill_abs = str(Path(args.skill_path).resolve() / "SKILL.md")
        turn1 = (
            f"Read the skill at {skill_abs} and follow its instructions.\n\n"
            f"User request: {eval_def['prompt']}"
        )
    else:
        turn1 = (
            f"You are working on a Gainsight Hub (Insided) Extensions project.\n\n"
            f"{eval_def['prompt']}"
        )

    # Execute turn 1
    print(f"[Turn 1] {eval_def['prompt'][:80]}")
    r = run_turn(session_id, turn1, work_dir, resume=False)
    transcript_turns.append({
        "turn": 1,
        "user": eval_def["prompt"],
        "agent": r["stdout"],
        "duration_seconds": r["duration_seconds"],
        "returncode": r["returncode"],
    })
    print(f"  -> {r['duration_seconds']}s, exit {r['returncode']}")
    if r["stderr"]:
        print(f"  stderr: {r['stderr'][:200]}")

    # Follow-up turns
    for i, user_msg in enumerate(eval_def.get("turns", []), start=2):
        print(f"[Turn {i}] {user_msg[:80]}")
        r = run_turn(session_id, user_msg, work_dir, resume=True)
        transcript_turns.append({
            "turn": i,
            "user": user_msg,
            "agent": r["stdout"],
            "duration_seconds": r["duration_seconds"],
            "returncode": r["returncode"],
        })
        print(f"  -> {r['duration_seconds']}s, exit {r['returncode']}")

    # Collect extension files from workspace into outputs/
    collected = collect_outputs(work_dir, output_dir)
    if collected:
        print(f"\nCollected {len(collected)} files:")
        for f in collected:
            print(f"  {f}")

    # Save transcript.json
    (output_dir / "transcript.json").write_text(json.dumps(transcript_turns, indent=2))

    # Save response.md (for eval viewer — also into outputs/ so viewer shows it)
    parts = []
    for t in transcript_turns:
        parts.append(f"## Turn {t['turn']}\n\n**User:** {t['user']}\n\n**Agent:**\n\n{t['agent']}")
    response_md = "\n\n---\n\n".join(parts)
    (output_dir / "response.md").write_text(response_md)
    (output_dir / "outputs").mkdir(exist_ok=True)
    (output_dir / "outputs" / "response.md").write_text(response_md)

    # Save timing.json
    total = sum(t["duration_seconds"] for t in transcript_turns)
    (output_dir / "timing.json").write_text(json.dumps({
        "total_duration_seconds": total,
        "duration_ms": int(total * 1000),
        "turns": len(transcript_turns),
        "per_turn": [
            {"turn": t["turn"], "duration_seconds": t["duration_seconds"]}
            for t in transcript_turns
        ],
    }, indent=2))

    # Save eval_metadata.json (for viewer)
    (output_dir / "eval_metadata.json").write_text(json.dumps({
        "eval_id": eval_def["id"],
        "eval_name": eval_def.get("name", f"eval-{eval_def['id']}"),
        "prompt": eval_def["prompt"],
        "turns": eval_def.get("turns", []),
        "assertions": eval_def.get("assertions", []),
    }, indent=2))

    print(f"\nDone. {len(transcript_turns)} turns, {total}s total.")
    print(f"Outputs: {output_dir}")


if __name__ == "__main__":
    main()
