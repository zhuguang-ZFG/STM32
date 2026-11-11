#!/usr/bin/env python3
"""Record wall-clock time per production stage in JOB/work/timing.json and summarize it.

Agent stages are marked by hand: `python3 scripts/timing.py JOB mark script start|end`.
handdraw_video.py records doctor/build/render/verify/finalize automatically.
"""
import argparse
import json
from pathlib import Path
import time

AGENT_STAGES = ('options', 'script', 'voice', 'images', 'review')


def timing_path(job):
    return Path(job) / 'work' / 'timing.json'


def load(job):
    path = timing_path(job)
    return json.loads(path.read_text()) if path.is_file() else {'records': []}


def save(job, data):
    path = timing_path(job)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def mark(job, stage, event, now=None):
    now = time.time() if now is None else now
    data = load(job)
    if event == 'start':
        data['records'].append({'stage': stage, 'source': 'agent', 'start': now, 'end': None})
    else:
        pending = [record for record in data['records'] if record['stage'] == stage and record['end'] is None]
        if not pending:
            raise ValueError(f'No open "{stage}" stage; mark start first')
        pending[-1].update(end=now, seconds=round(now - pending[-1]['start'], 3))
    save(job, data)


def record(job, stage, start, end, status):
    """Automatic record for a tool command; never blocks the command itself."""
    if not (Path(job) / 'job.json').is_file():
        return
    data = load(job)
    data['records'].append({'stage': stage, 'source': 'tool', 'start': start, 'end': end, 'seconds': round(end - start, 3), 'status': status})
    save(job, data)


def clock(seconds):
    minutes, seconds = divmod(round(seconds), 60)
    return f'{minutes // 60:d}:{minutes % 60:02d}:{seconds:02d}'


def summary(job):
    records = load(job)['records']
    if not records:
        return 'Timing: no records yet (python3 scripts/timing.py JOB mark script start)'
    stages = {}
    for item in records:
        entry = stages.setdefault(item['stage'], {'runs': 0, 'seconds': 0., 'open': 0, 'source': item['source']})
        entry['runs'] += 1
        entry['seconds'] += item.get('seconds') or 0
        entry['open'] += item['end'] is None
    lines = [f'Timing ({timing_path(job)})', f'{"stage":<16}{"runs":>5}{"time":>10}  source']
    for stage, entry in stages.items():
        lines.append(f'{stage:<16}{entry["runs"]:>5}{clock(entry["seconds"]):>10}  {entry["source"]}' + ('  (still open)' if entry['open'] else ''))
    ends = [item['end'] for item in records if item['end']]
    measured = sum(entry['seconds'] for entry in stages.values())
    lines.append(f'{"measured total":<21}{clock(measured):>10}')
    if ends:
        lines.append(f'{"wall clock":<21}{clock(max(ends) - min(item["start"] for item in records)):>10}  first start to last end')
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('job', type=Path)
    commands = parser.add_subparsers(dest='command', required=True)
    marker = commands.add_parser('mark')
    marker.add_argument('stage', choices=AGENT_STAGES)
    marker.add_argument('event', choices=('start', 'end'))
    commands.add_parser('summary')
    arguments = parser.parse_args()
    if arguments.command == 'mark':
        try:
            mark(arguments.job, arguments.stage, arguments.event)
        except ValueError as error:
            parser.error(str(error))
    print(summary(arguments.job))
