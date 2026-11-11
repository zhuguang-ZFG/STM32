#!/usr/bin/env python3
"""Entry point for a job-specific narrated hand-drawn video."""
import argparse
import json
import sys
import time
from pathlib import Path
import timing


def run(arguments):
    if arguments.command == 'doctor':
        from video_job import inspect_environment
        report = inspect_environment(arguments.job)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report['ready'] else 1
    if arguments.command == 'build':
        from video_job import FilmBuilder
        FilmBuilder(arguments.job).build()
    elif arguments.command == 'render':
        from video_renderer import render_job
        render_job(arguments.job, arguments.start, arguments.duration, arguments.preview)
    elif arguments.command == 'verify':
        from video_verifier import verify_job
        verify_job(arguments.job, arguments.assets_only)
    elif arguments.command == 'finalize':
        from video_verifier import finalize_job
        finalize_job(arguments.job)
    elif arguments.command == 'reject':
        from video_verifier import reject_job
        reject_job(arguments.job, arguments.reason or '')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['doctor', 'build', 'render', 'verify', 'finalize', 'reject'])
    parser.add_argument('job', type=Path, help='Directory containing job.json')
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--start', type=float, default=0.)
    parser.add_argument('--duration', type=float)
    parser.add_argument('--assets-only', action='store_true')
    parser.add_argument('--reason', help='reject: what the user rejected, in their words')
    arguments = parser.parse_args()
    stage = arguments.command
    if stage == 'render' and (arguments.preview or arguments.duration):
        stage = 'render:preview'
    started, status = time.time(), 'failed'
    try:
        code = run(arguments)
        status = 'ok' if code == 0 else 'not_ready'
        return code
    finally:
        try:
            timing.record(arguments.job, stage, started, time.time(), status)
            if arguments.command in ('doctor', 'verify'):
                print(timing.summary(arguments.job), file=sys.stderr)
        except (OSError, ValueError) as error:
            print(f'timing not recorded: {error}', file=sys.stderr)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except ImportError as error:
        print(f'ERROR: {error}\nInstall render dependencies: python3 -m pip install -r scripts/requirements.txt (or bash scripts/setup.sh)', file=sys.stderr)
        sys.exit(1)
    except (ValueError, FileNotFoundError, KeyError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
