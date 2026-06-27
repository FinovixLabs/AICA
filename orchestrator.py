"""
orchestrator.py
───────────────
Autonomous coding loop for the AICA project.

Flow:
    1. You provide a task (prompt or --task flag)
    2. Orchestrator runs Claude Code CLI to write the code
    3. Orchestrator runs Codex CLI to audit what Claude wrote
    4. If Codex finds critical issues → feeds findings back to Claude
    5. Loop continues until Codex is satisfied OR max_iterations hit
    6. All output logged to logs/

Usage:
    python orchestrator.py
    python orchestrator.py --task "implement notice classification endpoint"
    python orchestrator.py --task "..." --max-iter 5
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# ── Config ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent
LOGS_DIR     = PROJECT_ROOT / "logs"
TASK_FILE     = PROJECT_ROOT / "TASK.md"
REVIEW_FILE   = PROJECT_ROOT / "CODEX_REVIEW.md"
STATUS_FILE   = PROJECT_ROOT / "STATUS.md"
CHANGED_FILES = PROJECT_ROOT / "CHANGED_FILES.md"

CLAUDE_CMD = "claude"
CODEX_CMD  = "codex"

DEFAULT_MAX_ITERATIONS = 3


# ── Prompts ───────────────────────────────────────────────────────────────────

def claude_initial_prompt(task: str) -> str:
    return f"""You are working on the AICA project at {PROJECT_ROOT}.
Read CLAUDE.md for architecture rules, constraints, and your role assignments.

Your task:
{task}

Instructions:
- Write complete, working code directly into the appropriate project files
- Follow all rules in CLAUDE.md exactly
- After writing, run any relevant existing tests if they exist
- Write a brief summary of what you built to TASK.md when done
- IMPORTANT: After finishing, write CHANGED_FILES.md listing every file you
  created or modified. Use this exact format:

  # Changed Files

  ## Created
  - path/to/new_file.py

  ## Modified
  - path/to/existing_file.py

  Use paths relative to the project root. Include every file you touched.
  This file is read by the Codex auditor — be precise and complete.

Do not ask for confirmation. Work autonomously until the task is complete."""


def claude_revision_prompt(task: str, iteration: int) -> str:
    review = REVIEW_FILE.read_text() if REVIEW_FILE.exists() else "No review found."
    return f"""You are working on the AICA project at {PROJECT_ROOT}.
Read CLAUDE.md for architecture rules.

This is revision #{iteration}. Codex has audited your previous code and found issues.

Original task:
{task}

Codex audit findings (fix ALL critical and high severity issues):
{review}

Instructions:
- Fix every critical and high severity issue Codex identified
- Do not break anything that was working
- Focus on edge cases, error handling, and logic errors first
- Update TASK.md with a summary of what you changed
- Update CHANGED_FILES.md to reflect any additional files you touched
  during this revision (add to the existing list, do not replace it)

Work autonomously. Do not ask for confirmation."""


def read_changed_files_content() -> tuple[list[str], str]:
    """
    Read CHANGED_FILES.md, resolve each listed path, load the actual source.

    Returns (paths, formatted_code_block) where:
      paths              — list of relative path strings Claude changed
      formatted_code_block — each file's full content fenced in a code block,
                             ready to paste directly into the Codex prompt
    """
    if not CHANGED_FILES.exists():
        return [], "(CHANGED_FILES.md not found — Claude did not write the file list)"

    raw = CHANGED_FILES.read_text(encoding="utf-8")

    # Collect every "- path/to/file" line regardless of section
    paths: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            rel = stripped[2:].strip()
            if rel:
                paths.append(rel)

    if not paths:
        return [], "(CHANGED_FILES.md exists but lists no file paths)"

    blocks: list[str] = []
    missing: list[str] = []

    for rel in paths:
        full = PROJECT_ROOT / rel
        if not full.exists():
            missing.append(rel)
            continue
        try:
            content = full.read_text(encoding="utf-8")
            lang    = "python" if rel.endswith(".py") else ""
            blocks.append(f"### {rel}\n```{lang}\n{content}\n```")
        except Exception as exc:
            blocks.append(f"### {rel}\n(read error: {exc})")

    if missing:
        blocks.append(
            "### Missing files (listed in CHANGED_FILES.md but not found)\n"
            + "\n".join(f"- {p}" for p in missing)
        )

    return paths, "\n\n".join(blocks)


def codex_audit_prompt(task: str, iteration: int) -> str:
    paths, code_block = read_changed_files_content()

    if paths:
        files_summary = (
            f"Files to audit ({len(paths)} total):\n"
            + "\n".join(f"  - {p}" for p in paths)
        )
    else:
        files_summary = (
            "CHANGED_FILES.md was not produced. "
            f"Audit all recently modified files in {PROJECT_ROOT} "
            "relevant to the task."
        )

    return f"""You are a ruthless code auditor. Your only job is to find problems.

Task that was just implemented:
{task}

{files_summary}

Code to audit:
{code_block}

Audit focus (in priority order):
1. Logic errors and edge cases — does the code handle all inputs correctly?
   Pay special attention to None values, empty lists, missing dict keys,
   type mismatches, and off-by-one errors.
2. Error handling — are all failure modes caught? Are DB errors, file I/O
   errors, and external API failures handled gracefully?
3. Security — SQL injection, path traversal, unvalidated user input,
   exposed credentials, missing auth checks on endpoints.
4. Integration correctness — does it follow the existing Flask/Supabase
   patterns in the AICA project? Does it match CLAUDE.md architecture rules?

Write your findings to {REVIEW_FILE} using this exact format:

## Codex Audit — Iteration {iteration}

### CRITICAL
- <file:line — precise description of the issue>

### HIGH
- <file:line — precise description>

### MEDIUM
- <file:line — precise description>

### LOW
- <file:line — precise description>

### VERDICT
PASS — zero critical and zero high issues found
FAIL — one or more critical or high issues found

Rules:
- Reference specific file names and line numbers wherever possible
- Be precise and brutal — vague findings are useless
- Do not flag style issues unless they mask a real bug
- If the code is genuinely clean, say PASS and explain why you trust it"""


# ── CLI flags ─────────────────────────────────────────────────────────────────
#
# Claude Code: -p is non-interactive mode WITH full tool execution (file edits
#   included). --dangerously-skip-permissions bypasses all permission prompts.
#   Prompt is a positional argument — must be a SINGLE LINE on Windows.
#
# Codex CLI: --approval-mode full-auto bypasses confirmation prompts.
#   Adjust CODEX_FLAGS if your Codex version uses different flags.
#
CLAUDE_FLAGS = ["--dangerously-skip-permissions", "-p"]
CODEX_FLAGS  = ["--approval-mode", "full-auto", "-q"]


# ── Subprocess runner ─────────────────────────────────────────────────────────

def run_cli(
    cmd:      str,
    prompt:   str,
    log_path: Path,
    timeout:  int = 300,
) -> tuple[bool, str]:
    """
    Run a CLI tool (claude or codex) with full tool/file-edit execution.

    Strategy:
      1. Write the full prompt to a known file (TASK.md for Claude,
         CODEX_TASK.md for Codex) so the CLI reads it as a file.
      2. Pass a SHORT SINGLE-LINE prompt as the CLI argument pointing
         to that file. Multiline args break on Windows.
      3. Redirect stdout/stderr directly to the log file rather than
         using capture_output=True, which avoids pipe/TTY conflicts.
    """
    if cmd == CLAUDE_CMD:
        prompt_file = TASK_FILE                  # C:\aicaa\TASK.md
        short_prompt = "Read TASK.md and execute the task described there. Work autonomously without asking for confirmation."
    else:
        prompt_file  = PROJECT_ROOT / "CODEX_TASK.md"
        short_prompt = "Read CODEX_TASK.md and execute the audit task described there. Work autonomously."

    # Write full prompt to the known file
    prompt_file.write_text(prompt, encoding="utf-8")

    # Build command — short_prompt is a single line, safe on Windows
    full_cmd = [cmd, *CLAUDE_FLAGS, short_prompt] if cmd == CLAUDE_CMD \
               else [cmd, *CODEX_FLAGS, short_prompt]

    print(f"\n  running {cmd}...", flush=True)
    print(f"  prompt file : {prompt_file.name}", flush=True)
    print(f"  log         : {log_path.name}", flush=True)

    try:
        # Redirect output directly to log file — avoids capture_output pipe issues
        with open(log_path, "w", encoding="utf-8") as log_file:
            log_file.write(f"CMD:  {' '.join(full_cmd[:3])} [prompt omitted]\n")
            log_file.write(f"TASK: {prompt_file}\n")
            log_file.write("─" * 60 + "\n")
            log_file.flush()

            result = subprocess.run(
                full_cmd,
                stdout=log_file,
                stderr=log_file,
                timeout=timeout,
                cwd=str(PROJECT_ROOT),
            )

        output = log_path.read_text(encoding="utf-8")
        success = result.returncode == 0

        if not success:
            print(f"  {cmd} exited with code {result.returncode}")

        return success, output

    except subprocess.TimeoutExpired:
        msg = f"{cmd} timed out after {timeout}s"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg)
        print(f"  {msg}")
        return False, msg

    except FileNotFoundError:
        msg = (
            f"'{cmd}' not found. "
            f"Make sure {cmd} CLI is installed and on your PATH."
        )
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(msg)
        print(f"\n  ERROR: {msg}")
        return False, msg


# ── Verdict parser ────────────────────────────────────────────────────────────

def codex_passed(review_output: str) -> bool:
    """
    Return True if Codex verdict is PASS.
    Checks both the REVIEW_FILE and the raw output.
    """
    sources = [review_output]
    if REVIEW_FILE.exists():
        sources.append(REVIEW_FILE.read_text())

    for text in sources:
        upper = text.upper()
        if "VERDICT" in upper:
            # Look for PASS after VERDICT
            verdict_idx = upper.rfind("VERDICT")
            snippet = upper[verdict_idx:verdict_idx + 100]
            if "PASS" in snippet:
                return True
            if "FAIL" in snippet:
                return False

    # No explicit verdict — treat as fail to be safe
    return False


# ── Status writer ─────────────────────────────────────────────────────────────

def write_status(task: str, iteration: int, state: str, note: str = "") -> None:
    STATUS_FILE.write_text(
        f"# Orchestrator Status\n\n"
        f"Task: {task}\n"
        f"Iteration: {iteration}\n"
        f"State: {state}\n"
        f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{('Note: ' + note) if note else ''}\n",
        encoding="utf-8",
    )


# ── Session logger ────────────────────────────────────────────────────────────

class SessionLog:
    """Writes a structured JSON summary of the full session to logs/."""

    def __init__(self, task: str) -> None:
        self.task      = task
        self.started   = datetime.now()
        self.iterations: list[dict] = []
        self.outcome   = "unknown"

        LOGS_DIR.mkdir(exist_ok=True)
        slug = self.started.strftime("%Y%m%d_%H%M%S")
        self.path = LOGS_DIR / f"session_{slug}.json"

    def record(
        self,
        iteration:     int,
        claude_ok:     bool,
        codex_ok:      bool,
        verdict:       str,
        changed_files: list[str] | None = None,
    ) -> None:
        self.iterations.append({
            "iteration":     iteration,
            "claude_ok":     claude_ok,
            "codex_ok":      codex_ok,
            "verdict":       verdict,
            "changed_files": changed_files or [],
            "timestamp":     datetime.now().isoformat(),
        })
        self._flush()

    def finish(self, outcome: str) -> None:
        self.outcome = outcome
        self._flush()
        print(f"\n  session log → {self.path}")

    def _flush(self) -> None:
        self.path.write_text(
            json.dumps({
                "task":       self.task,
                "started":    self.started.isoformat(),
                "outcome":    self.outcome,
                "iterations": self.iterations,
            }, indent=2),
            encoding="utf-8",
        )


# ── Main loop ─────────────────────────────────────────────────────────────────

def run(task: str, max_iterations: int = DEFAULT_MAX_ITERATIONS) -> None:
    LOGS_DIR.mkdir(exist_ok=True)

    session = SessionLog(task)
    ts      = session.started.strftime("%Y%m%d_%H%M%S")

    print(f"\n{'═'*60}")
    print(f"  AICA Orchestrator")
    print(f"{'═'*60}")
    print(f"  Task:     {task[:80]}{'...' if len(task) > 80 else ''}")
    print(f"  Max iter: {max_iterations}")
    print(f"  Logs:     {LOGS_DIR}")
    print(f"{'─'*60}")

    write_status(task, 0, "starting")

    for iteration in range(1, max_iterations + 1):
        print(f"\n[iter {iteration}/{max_iterations}]")

        # ── Step 1: Claude writes (or revises) code ────────────────────────
        write_status(task, iteration, "claude_writing")

        if iteration == 1:
            claude_prompt = claude_initial_prompt(task)
        else:
            claude_prompt = claude_revision_prompt(task, iteration)

        claude_log  = LOGS_DIR / f"{ts}_iter{iteration}_claude.txt"
        claude_ok, claude_out = run_cli(
            CLAUDE_CMD,
            claude_prompt,
            claude_log,
            timeout=600,   # 10 min — Claude may write a lot
        )

        if not claude_ok:
            write_status(task, iteration, "claude_failed")
            print(f"  Claude failed on iteration {iteration}. Check {claude_log}")
            session.record(iteration, False, False, "claude_failed")
            # Try to continue — sometimes exit code ≠ 0 but work was done
            if iteration == max_iterations:
                break

        # ── Step 2: Codex audits what Claude wrote ─────────────────────────
        write_status(task, iteration, "codex_auditing")

        codex_prompt = codex_audit_prompt(task, iteration)
        codex_log    = LOGS_DIR / f"{ts}_iter{iteration}_codex.txt"
        codex_ok, codex_out = run_cli(
            CODEX_CMD,
            codex_prompt,
            codex_log,
            timeout=300,   # 5 min for audit
        )

        passed  = codex_passed(codex_out)
        verdict = "PASS" if passed else "FAIL"

        # Capture which files were changed this iteration for the session log
        changed_paths, _ = read_changed_files_content()
        session.record(iteration, claude_ok, codex_ok, verdict, changed_paths)

        print(f"  Codex verdict: {verdict}")

        if passed:
            write_status(task, iteration, "done", "Codex passed — no critical issues")
            print(f"\n{'═'*60}")
            print(f"  DONE — Codex passed on iteration {iteration}")
            print(f"{'═'*60}")
            session.finish("passed")
            _cleanup_temp_files()
            return

        if iteration < max_iterations:
            print(f"  Issues found — handing back to Claude for revision")
            write_status(task, iteration, "revision_needed")
        else:
            print(f"\n{'─'*60}")
            print(f"  Max iterations ({max_iterations}) reached.")
            print(f"  Codex review is at: {REVIEW_FILE}")
            print(f"  Review manually before shipping.")
            print(f"{'─'*60}")

    session.finish("max_iterations_reached")
    write_status(task, max_iterations, "max_iterations_reached")


def _cleanup_temp_files() -> None:
    """Remove handoff files after a clean run."""
    for f in (TASK_FILE, STATUS_FILE, CHANGED_FILES, PROJECT_ROOT / "CODEX_TASK.md"):
        if f.exists():
            f.unlink()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Autonomous Claude + Codex coding loop for AICA"
    )
    parser.add_argument(
        "--task", "-t",
        type=str,
        default=None,
        help="Task description. If omitted, will prompt interactively.",
    )
    parser.add_argument(
        "--max-iter", "-m",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f"Max Claude→Codex iterations (default: {DEFAULT_MAX_ITERATIONS})",
    )
    args = parser.parse_args()

    task = args.task
    if not task:
        print("\nWhat should Claude build?")
        print("(Be specific — include file names, endpoint paths, behaviour)")
        print()
        task = input("Task: ").strip()
        if not task:
            print("No task given. Exiting.")
            sys.exit(1)

    run(task, max_iterations=args.max_iter)


if __name__ == "__main__":
    main()