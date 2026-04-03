#!/usr/bin/env python3
"""
Multi-turn eval runner for build-extension skill.

Runs a single eval using claude CLI sessions with --resume for follow-up turns.
Supports both single-turn (backward compatible) and multi-turn evals.

Usage:
    python scripts/run-multi-turn-eval.py \
        --eval-id 14 \
        --config with_skill \
        --output-dir build-extension-workspace/iteration-7/vague-multiturn/with_skill/run-1 \
        --skill-path skills/build-extension

    # Baseline (no skill, isolated worktree):
    python scripts/run-multi-turn-eval.py \
        --eval-id 14 \
        --config without_skill \
        --output-dir build-extension-workspace/iteration-7/vague-multiturn/without_skill/run-1
"""

import argparse
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path


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
    (output_dir / "outputs").mkdir(exist_ok=True)

    session_id = str(uuid.uuid4())
    transcript_turns = []

    # Build turn 1
    outputs_path = output_dir / "outputs"
    if args.config == "with_skill":
        skill_abs = str(Path(args.skill_path).resolve() / "SKILL.md")
        turn1 = (
            f"Read the skill at {skill_abs} and follow its instructions.\n\n"
            f"User request: {eval_def['prompt']}\n\n"
            f"Create any extension files in {outputs_path}/"
        )
    else:
        turn1 = (
            f"You are working on a Gainsight Hub (Insided) Extensions project.\n\n"
            f"{eval_def['prompt']}\n\n"
            f"Create any extension files in {outputs_path}/"
        )

    # Execute turn 1
    print(f"[Turn 1] {eval_def['prompt'][:80]}")
    r = run_turn(session_id, turn1, output_dir, resume=False)
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
        r = run_turn(session_id, user_msg, output_dir, resume=True)
        transcript_turns.append({
            "turn": i,
            "user": user_msg,
            "agent": r["stdout"],
            "duration_seconds": r["duration_seconds"],
            "returncode": r["returncode"],
        })
        print(f"  -> {r['duration_seconds']}s, exit {r['returncode']}")

    # Save transcript.json
    (output_dir / "transcript.json").write_text(json.dumps(transcript_turns, indent=2))

    # Save response.md (for eval viewer)
    parts = []
    for t in transcript_turns:
        parts.append(f"## Turn {t['turn']}\n\n**User:** {t['user']}\n\n**Agent:**\n\n{t['agent']}")
    response_md = "\n\n---\n\n".join(parts)
    (output_dir / "response.md").write_text(response_md)
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

    # Copy content.html to outputs/ root if it's in outputs/dist/
    dist_html = output_dir / "outputs" / "dist" / "content.html"
    if dist_html.exists():
        import shutil
        shutil.copy2(dist_html, output_dir / "outputs" / "content.html")

    print(f"\nDone. {len(transcript_turns)} turns, {total}s total.")
    print(f"Outputs: {output_dir}")


if __name__ == "__main__":
    main()
