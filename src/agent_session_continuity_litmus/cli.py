from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .adapters import run_codex, run_opencode
from .core import PROFILE_NAMES, compare_paths, make_fixture


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-session-continuity-litmus")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fixture = subparsers.add_parser("fixture", help="print one deterministic fixture contract")
    fixture.add_argument("--repetition", type=int, default=1)
    fixture.add_argument("--profile", choices=PROFILE_NAMES, default=PROFILE_NAMES[0])

    run = subparsers.add_parser("run", help="run baseline and native-compaction paths")
    run.add_argument("--adapter", choices=("codex-cli", "opencode-cli"), required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--repetitions", type=int, default=1)
    run.add_argument("--profile", choices=PROFILE_NAMES, action="append", dest="profiles")
    run.add_argument("--allow-live", action="store_true")
    run.add_argument("--timeout-seconds", type=int, default=300)
    run.add_argument("--codex-bin", default="codex")
    run.add_argument("--opencode-bin", default="opencode")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "fixture":
        fixture = make_fixture(args.repetition, args.profile)
        print(fixture.phase_one)
        return 0
    if args.command == "run":
        executable = args.codex_bin if args.adapter == "codex-cli" else args.opencode_bin
        if not args.allow_live:
            print(f"adapter executable: {shutil.which(executable) or 'not found'}")
            print("Live execution may consume model quota. Re-run with --allow-live to opt in.")
            return 2
        if not 1 <= args.repetitions <= 10:
            raise ValueError("repetitions must be between 1 and 10")
        if args.output.exists():
            raise FileExistsError(f"output already exists: {args.output}")
        args.output.mkdir(parents=True)
        profiles = args.profiles or [PROFILE_NAMES[0]]
        comparisons = []
        results = []
        for profile in profiles:
            for repetition in range(1, args.repetitions + 1):
                fixture = make_fixture(repetition, profile)
                run = run_codex if args.adapter == "codex-cli" else run_opencode
                kwargs = {"timeout_seconds": args.timeout_seconds}
                kwargs["codex_bin" if args.adapter == "codex-cli" else "opencode_bin"] = executable
                run_output = args.output / profile / f"run-{repetition:02d}"
                baseline = run(fixture, "baseline", run_output / "baseline", **kwargs)
                compact = run(fixture, "compact", run_output / "compact", **kwargs)
                comparison = compare_paths(baseline, compact)
                comparisons.append(comparison)
                results.extend([baseline, compact])
                print(
                    f"{profile}/run-{repetition:02d}: baseline {baseline.passed_fields}/6 {baseline.status}; "
                    f"compact {compact.passed_fields}/6 {compact.status}; "
                    f"boundary drift {comparison['boundary_attributable_exact_drift']}"
                )
        summary = {
            "adapter": args.adapter,
            "profiles": profiles,
            "repetitions": args.repetitions,
            "complete_runs": sum(result.status != "INCONCLUSIVE" for result in results),
            "total_runs": len(results),
            "comparisons": comparisons,
        }
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        return 1 if any(result.status != "PASS" for result in results) else 0
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileExistsError, FileNotFoundError, RuntimeError, TimeoutError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        raise SystemExit(2)
